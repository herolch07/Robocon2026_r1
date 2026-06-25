#!/usr/bin/env python3
"""Direct STAFF-mode joystick bridge for Motor 7 and Motor 8 position controllers."""

import time

import rclpy
from my_joystick_msgs.msg import Joystick
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Int32


TRIGGER_MAX = 512.0
MODE_STAFF = 1


class MotorPositionSelectorJoystickBridgeNode(Node):
    """Route STAFF-mode buttons directly to Motor 7/8 position inputs.

    Current STAFF mapping:
      A     -> Motor 7 preset / left-right 90-degree cycle
      X     -> Motor 8 preset / left-right 90-degree cycle
      R1/R2 -> Motor 7 trim, negative/positive
      L1/L2 -> Motor 8 trim, negative/positive

    If `/view_orientation` is D-pad down (`2`), Motor 7 and Motor 8 controls
    are swapped so STAFF operation follows the operator-facing robot direction.

    SELECT/START are intentionally not used here; they are owned by
    operation_mode_selector_node. When operation mode is not STAFF, this bridge
    publishes invalid neutral input so the position controllers stop accepting
    toggle/trim commands and hold safely.
    """

    def __init__(self):
        super().__init__("motor_position_selector_joystick_bridge_node")

        self.declare_parameter("motor7_toggle_button", "a")
        self.declare_parameter("motor8_toggle_button", "x")
        self.declare_parameter("trigger_deadzone", 24)
        self.declare_parameter("publish_hz", 20.0)
        self.declare_parameter("input_timeout_sec", 0.3)
        self.declare_parameter("mode_timeout_sec", 0.5)
        self.declare_parameter("swap_staff_grippers_on_view_down", True)

        self.last_joystick_time = 0.0
        self.last_mode_time = 0.0
        self.operation_mode = 0
        self.view_orientation = 0
        self.motor7_toggle_was_pressed = True
        self.motor8_toggle_was_pressed = True
        self.pending_motor7_toggle = False
        self.pending_motor8_toggle = False
        self.motor7_trim_input = 0.0
        self.motor8_trim_input = 0.0

        self.joy_sub = self.create_subscription(
            Joystick, "/joystick_data", self.joystick_callback, 10
        )
        self.mode_sub = self.create_subscription(
            Int32, "/operation_mode", self.operation_mode_callback, 10
        )
        self.view_sub = self.create_subscription(
            Int32, "/view_orientation", self.view_orientation_callback, 10
        )
        self.motor7_pub = self.create_publisher(
            Float32MultiArray, "/motor7_position_input", 10
        )
        self.motor8_pub = self.create_publisher(
            Float32MultiArray, "/motor8_position_input", 10
        )
        self.status_pub = self.create_publisher(
            Float32MultiArray, "/motor_position_selector_status", 10
        )

        publish_hz = max(float(self.get_parameter("publish_hz").value), 1.0)
        self.timer = self.create_timer(1.0 / publish_hz, self.timer_callback)
        self.get_logger().info(
            "Position bridge initialized: STAFF mode A->M7 preset, X->M8 preset, "
            "R1/R2->M7 trim, L1/L2->M8 trim; D-pad down swaps M7/M8"
        )

    @staticmethod
    def rising_edge(pressed, was_pressed):
        """Return whether a rising edge occurred and the new edge state."""
        return bool(pressed and not was_pressed), bool(pressed)

    @staticmethod
    def trigger_axis(value, deadzone):
        """Convert one trigger depth to normalized 0..1 after deadzone."""
        depth = 0 if int(value) < deadzone else min(int(value), int(TRIGGER_MAX))
        return max(0.0, min(float(depth) / TRIGGER_MAX, 1.0))

    @staticmethod
    def trigger_trim(l2, r2, deadzone):
        """Backward-compatible combined trim helper used by older tests."""
        left = MotorPositionSelectorJoystickBridgeNode.trigger_axis(l2, deadzone)
        right = MotorPositionSelectorJoystickBridgeNode.trigger_axis(r2, deadzone)
        return max(-1.0, min(right - left, 1.0))

    @staticmethod
    def direct_motor_trims(l1, l2, r1, r2, deadzone):
        """Return independent trims for the STAFF-mode paired controls.

        Motor 7 uses R1/R2 and Motor 8 uses L1/L2. The shoulder button is the
        negative direction, and the analog trigger is the positive direction.
        """
        motor7_trim = (
            MotorPositionSelectorJoystickBridgeNode.trigger_axis(r2, deadzone)
            - (1.0 if bool(r1) else 0.0)
        )
        motor8_trim = (
            MotorPositionSelectorJoystickBridgeNode.trigger_axis(l2, deadzone)
            - (1.0 if bool(l1) else 0.0)
        )
        return (
            max(-1.0, min(motor7_trim, 1.0)),
            max(-1.0, min(motor8_trim, 1.0)),
        )

    @staticmethod
    def maybe_swap_motor_values(motor7_value, motor8_value, swap_enabled, view_orientation):
        """Swap Motor7/Motor8 values only when D-pad down view is active."""
        if bool(swap_enabled) and int(view_orientation) == 2:
            return motor8_value, motor7_value
        return motor7_value, motor8_value

    @staticmethod
    def maybe_swap_trim_values(motor7_trim, motor8_trim, swap_enabled, view_orientation):
        """Swap Motor7/Motor8 trims and reverse each pair direction on D-pad down.

        D-pad down means the operator is facing the STAFF side from the opposite
        direction. Besides swapping Motor7 and Motor8, each local trim pair also
        needs its positive/negative buttons reversed: R1<->R2 and L1<->L2.
        """
        if bool(swap_enabled) and int(view_orientation) == 2:
            return -motor8_trim, -motor7_trim
        return motor7_trim, motor8_trim

    @staticmethod
    def controls_are_neutral(toggle_pressed, l2, r2, deadzone):
        """Legacy helper retained for tests and documentation history."""
        return (
            not bool(toggle_pressed)
            and int(l2) < deadzone
            and int(r2) < deadzone
        )

    @staticmethod
    def next_motor_id(current):
        """Legacy helper from the former START selector behavior."""
        return 8 if int(current) == 7 else 7

    def operation_mode_callback(self, msg):
        """Track `/operation_mode`; only STAFF mode enables this bridge."""
        self.operation_mode = int(msg.data)
        self.last_mode_time = time.monotonic()

    def view_orientation_callback(self, msg):
        """Track operator view; D-pad down optionally swaps Motor7/Motor8."""
        self.view_orientation = int(msg.data)

    def staff_mode_active(self):
        """Return true only while a fresh STAFF mode message is present."""
        timeout = max(float(self.get_parameter("mode_timeout_sec").value), 0.0)
        return (
            self.operation_mode == MODE_STAFF
            and time.monotonic() - self.last_mode_time <= timeout
        )

    def get_button(self, msg, parameter_name):
        """Read one parameter-selected button from the joystick message."""
        name = str(self.get_parameter(parameter_name).value)
        if not hasattr(msg, name):
            self.get_logger().warn(
                f"Unknown position button: {name}",
                throttle_duration_sec=2.0,
            )
            return False
        return bool(getattr(msg, name))

    def joystick_callback(self, msg):
        """Update direct Motor7/8 toggle and trim inputs from one joystick sample."""
        self.last_joystick_time = time.monotonic()
        deadzone = max(0, int(self.get_parameter("trigger_deadzone").value))

        if not self.staff_mode_active():
            self.pending_motor7_toggle = False
            self.pending_motor8_toggle = False
            self.motor7_trim_input = 0.0
            self.motor8_trim_input = 0.0
            self.motor7_toggle_was_pressed = True
            self.motor8_toggle_was_pressed = True
            return

        motor7_toggle_pressed = self.get_button(msg, "motor7_toggle_button")
        motor8_toggle_pressed = self.get_button(msg, "motor8_toggle_button")
        motor7_toggle_pressed, motor8_toggle_pressed = self.maybe_swap_motor_values(
            motor7_toggle_pressed,
            motor8_toggle_pressed,
            self.get_parameter("swap_staff_grippers_on_view_down").value,
            self.view_orientation,
        )

        motor7_edge, self.motor7_toggle_was_pressed = self.rising_edge(
            motor7_toggle_pressed, self.motor7_toggle_was_pressed
        )
        motor8_edge, self.motor8_toggle_was_pressed = self.rising_edge(
            motor8_toggle_pressed, self.motor8_toggle_was_pressed
        )
        self.pending_motor7_toggle = self.pending_motor7_toggle or motor7_edge
        self.pending_motor8_toggle = self.pending_motor8_toggle or motor8_edge
        self.motor7_trim_input, self.motor8_trim_input = self.direct_motor_trims(
            msg.l1, msg.l2, msg.r1, msg.r2, deadzone
        )
        self.motor7_trim_input, self.motor8_trim_input = self.maybe_swap_trim_values(
            self.motor7_trim_input,
            self.motor8_trim_input,
            self.get_parameter("swap_staff_grippers_on_view_down").value,
            self.view_orientation,
        )

    def timer_callback(self):
        """Publish direct Motor7 and Motor8 position inputs."""
        timeout = max(float(self.get_parameter("input_timeout_sec").value), 0.0)
        joystick_valid = time.monotonic() - self.last_joystick_time <= timeout
        valid = joystick_valid and self.staff_mode_active()
        if not valid:
            self.motor7_trim_input = 0.0
            self.motor8_trim_input = 0.0
            self.pending_motor7_toggle = False
            self.pending_motor8_toggle = False
            self.motor7_toggle_was_pressed = True
            self.motor8_toggle_was_pressed = True

        motor7_msg = Float32MultiArray()
        motor7_msg.data = [
            1.0 if self.pending_motor7_toggle and valid else 0.0,
            self.motor7_trim_input if valid else 0.0,
            1.0 if valid else 0.0,
        ]
        motor8_msg = Float32MultiArray()
        motor8_msg.data = [
            1.0 if self.pending_motor8_toggle and valid else 0.0,
            self.motor8_trim_input if valid else 0.0,
            1.0 if valid else 0.0,
        ]
        self.motor7_pub.publish(motor7_msg)
        self.motor8_pub.publish(motor8_msg)

        status = Float32MultiArray()
        status.data = [
            float(self.operation_mode),
            1.0 if valid else 0.0,
            0.0,
        ]
        self.status_pub.publish(status)
        self.pending_motor7_toggle = False
        self.pending_motor8_toggle = False


def main(args=None):
    rclpy.init(args=args)
    node = MotorPositionSelectorJoystickBridgeNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
