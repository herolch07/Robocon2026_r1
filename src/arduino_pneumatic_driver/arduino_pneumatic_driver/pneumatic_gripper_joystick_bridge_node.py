#!/usr/bin/env python3
"""Route STAFF-mode joystick buttons to the five-relay staff pneumatic panel."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32, Int32MultiArray

from my_joystick_msgs.msg import Joystick


# /pneumatic_gripper_cmd order for Arduino relays 2-5:
# [M7 gripper, M8 inclination, M8 gripper, M7 inclination]
DEFAULT_ARM_SAFE_STATE = [1, 0, 1, 0]
MODE_STAFF = 1


class PneumaticGripperJoystickBridgeNode(Node):
    """Control staff gripper relays only while STAFF mode is active.

    Current STAFF mapping:
      B  -> Motor 7 staff gripper relay toggle
      Y  -> Motor 8 staff gripper relay toggle
      R3 -> Motor 7 inclination/head relay toggle
      L3 -> Motor 8 inclination/head relay toggle

    If `/view_orientation` is D-pad down (`2`), Motor 7 and Motor 8 relay
    controls are swapped to match operator-facing STAFF gripper control.

    The former Motor7/Motor8 height relays were removed from the Arduino panel.
    L1/R1/L2/R2 are reserved for Motor7/8 manual trim.
    """

    def __init__(self):
        super().__init__("pneumatic_gripper_joystick_bridge_node")

        self.declare_parameter("motor7_gripper_button", "b")
        self.declare_parameter("motor8_gripper_button", "y")
        self.declare_parameter("motor7_inclination_button", "r3")
        self.declare_parameter("motor8_inclination_button", "l3")
        self.declare_parameter("safe_state", DEFAULT_ARM_SAFE_STATE)
        self.declare_parameter("publish_hz", 20.0)
        self.declare_parameter("input_timeout_sec", 0.3)
        self.declare_parameter("mode_timeout_sec", 0.5)
        self.declare_parameter("swap_staff_grippers_on_view_down", True)

        self.states = self.get_safe_state()
        self.last_joystick_time = None
        self.last_mode_time = None
        self.operation_mode = 0
        self.view_orientation = 0
        self.motor7_gripper_pressed = True
        self.motor8_gripper_pressed = True
        self.motor7_inclination_pressed = True
        self.motor8_inclination_pressed = True

        self.joy_sub = self.create_subscription(
            Joystick, "/joystick_data", self.joystick_callback, 10
        )
        self.mode_sub = self.create_subscription(
            Int32, "/operation_mode", self.operation_mode_callback, 10
        )
        self.view_sub = self.create_subscription(
            Int32, "/view_orientation", self.view_orientation_callback, 10
        )
        self.cmd_pub = self.create_publisher(
            Int32MultiArray, "/pneumatic_gripper_cmd", 10
        )

        publish_hz = max(float(self.get_parameter("publish_hz").value), 1.0)
        self.publish_timer = self.create_timer(
            1.0 / publish_hz, self.publish_timer_callback
        )

        self.get_logger().info(
            "Pneumatic bridge initialized: STAFF mode B=M7 gripper, Y=M8 gripper, "
            "R3=M7 head, L3=M8 head; D-pad down swaps M7/M8"
        )

    def get_safe_state(self):
        """Return four staff relay values in the confirmed wiring order."""
        raw = list(self.get_parameter("safe_state").value)
        safe = list(DEFAULT_ARM_SAFE_STATE)
        for index, value in enumerate(raw[:4]):
            safe[index] = self.normalize_state(value)
        return safe

    def operation_mode_callback(self, msg):
        """Track `/operation_mode`; only STAFF mode enables button toggles."""
        self.operation_mode = int(msg.data)
        self.last_mode_time = self.get_clock().now()

    def view_orientation_callback(self, msg):
        """Track operator view; D-pad down optionally swaps Motor7/Motor8."""
        self.view_orientation = int(msg.data)

    def staff_mode_active(self):
        """Return true only while a fresh STAFF mode message is present."""
        if self.last_mode_time is None:
            return False
        elapsed = (self.get_clock().now() - self.last_mode_time).nanoseconds / 1e9
        return (
            self.operation_mode == MODE_STAFF
            and elapsed <= float(self.get_parameter("mode_timeout_sec").value)
        )

    def joystick_callback(self, msg):
        """Apply STAFF-mode rising-edge toggles to fixed staff relay channels."""
        self.last_joystick_time = self.get_clock().now()

        if not self.staff_mode_active():
            self.reset_edge_memory()
            return

        buttons = self.maybe_swap_button_pairs(
            self.get_configured_button(msg, "motor7_gripper_button"),
            self.get_configured_button(msg, "motor8_gripper_button"),
            self.get_configured_button(msg, "motor7_inclination_button"),
            self.get_configured_button(msg, "motor8_inclination_button"),
            self.get_parameter("swap_staff_grippers_on_view_down").value,
            self.view_orientation,
        )

        self.states[0], self.motor7_gripper_pressed = self.apply_toggle(
            self.states[0], buttons["motor7_gripper"], self.motor7_gripper_pressed
        )
        self.states[2], self.motor8_gripper_pressed = self.apply_toggle(
            self.states[2], buttons["motor8_gripper"], self.motor8_gripper_pressed
        )
        self.states[3], self.motor7_inclination_pressed = self.apply_toggle(
            self.states[3], buttons["motor7_inclination"], self.motor7_inclination_pressed
        )
        self.states[1], self.motor8_inclination_pressed = self.apply_toggle(
            self.states[1], buttons["motor8_inclination"], self.motor8_inclination_pressed
        )

    def reset_edge_memory(self):
        """Require release before accepting a toggle after timeout or mode change."""
        self.motor7_gripper_pressed = True
        self.motor8_gripper_pressed = True
        self.motor7_inclination_pressed = True
        self.motor8_inclination_pressed = True

    @staticmethod
    def maybe_swap_button_pairs(
        motor7_gripper,
        motor8_gripper,
        motor7_inclination,
        motor8_inclination,
        swap_enabled,
        view_orientation,
    ):
        """Return button states after optional D-pad-down Motor7/Motor8 swap."""
        if bool(swap_enabled) and int(view_orientation) == 2:
            motor7_gripper, motor8_gripper = motor8_gripper, motor7_gripper
            motor7_inclination, motor8_inclination = (
                motor8_inclination,
                motor7_inclination,
            )
        return {
            "motor7_gripper": bool(motor7_gripper),
            "motor8_gripper": bool(motor8_gripper),
            "motor7_inclination": bool(motor7_inclination),
            "motor8_inclination": bool(motor8_inclination),
        }

    @staticmethod
    def normalize_state(value):
        """Clamp a numeric relay value to zero or one."""
        return 1 if int(value) else 0

    @staticmethod
    def selected_arm_indices(motor_id):
        """Return legacy gripper-only indices for Motor 7 or Motor 8."""
        return (0, 0) if int(motor_id) == 7 else (2, 2)

    @staticmethod
    def selected_inclination_index(motor_id):
        """Return inclination command index for Motor 7 or Motor 8."""
        return 3 if int(motor_id) == 7 else 1

    @staticmethod
    def selected_gripper_index(motor_id):
        """Return gripper command index for Motor 7 or Motor 8."""
        return 0 if int(motor_id) == 7 else 2

    @staticmethod
    def apply_toggle(state, pressed, was_pressed):
        """Toggle once on a button rising edge and update edge memory."""
        if pressed and not was_pressed:
            state = 1 - int(state)
        return int(state), bool(pressed)

    @staticmethod
    def apply_height_toggle(height_state, pressed, was_pressed):
        """Backward-compatible alias for old tests; no height relay remains."""
        return PneumaticGripperJoystickBridgeNode.apply_toggle(
            height_state, pressed, was_pressed
        )

    @staticmethod
    def apply_gripper_toggle(gripper_state, pressed, was_pressed):
        """Backward-compatible alias used by existing unit tests."""
        return PneumaticGripperJoystickBridgeNode.apply_toggle(
            gripper_state, pressed, was_pressed
        )

    def get_configured_button(self, msg, parameter_name):
        """Read a parameter-selected Joystick button safely."""
        button_name = str(self.get_parameter(parameter_name).value)
        if not hasattr(msg, button_name):
            self.get_logger().warn(
                f"Unknown pneumatic button: {button_name}",
                throttle_duration_sec=2.0,
            )
            return False
        return bool(getattr(msg, button_name))

    def publish_timer_callback(self):
        """Publish continuously and restore all staff relays after joystick timeout."""
        if self.is_joystick_timed_out():
            self.states = self.get_safe_state()
            self.reset_edge_memory()

        msg = Int32MultiArray()
        msg.data = [int(value) for value in self.states]
        self.cmd_pub.publish(msg)

    def is_joystick_timed_out(self):
        """Return true after input_timeout_sec without joystick updates."""
        if self.last_joystick_time is None:
            return True
        elapsed = (self.get_clock().now() - self.last_joystick_time).nanoseconds / 1e9
        return elapsed > float(self.get_parameter("input_timeout_sec").value)


def main(args=None):
    rclpy.init(args=args)
    node = PneumaticGripperJoystickBridgeNode()
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
