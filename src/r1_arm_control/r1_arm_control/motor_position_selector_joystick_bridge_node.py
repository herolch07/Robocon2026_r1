#!/usr/bin/env python3
"""Shared joystick selector for Motor 7 and Motor 8 position controllers."""

import time

import rclpy
from my_joystick_msgs.msg import Joystick
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


TRIGGER_MAX = 512.0


class MotorPositionSelectorJoystickBridgeNode(Node):
    """Route X and L2/R2 to one selected position-controlled motor.

    Motor 7 is selected at startup. START switches between Motor 7 and Motor 8
    only while X and both triggers are released. The unselected motor receives
    a valid neutral input so it keeps its own target without accepting trim.
    """

    def __init__(self):
        super().__init__("motor_position_selector_joystick_bridge_node")

        self.declare_parameter("default_motor_id", 7)
        self.declare_parameter("switch_button", "start")
        self.declare_parameter("toggle_button", "x")
        self.declare_parameter("trigger_deadzone", 24)
        self.declare_parameter("publish_hz", 20.0)
        self.declare_parameter("input_timeout_sec", 0.3)

        default_motor = int(self.get_parameter("default_motor_id").value)
        self.selected_motor_id = default_motor if default_motor in (7, 8) else 7
        self.last_joystick_time = 0.0
        self.switch_was_pressed = True
        self.toggle_was_pressed = True
        self.pending_toggle = False
        self.trim_input = 0.0
        self.switch_blocked = False

        self.joy_sub = self.create_subscription(
            Joystick, "/joystick_data", self.joystick_callback, 10
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
            f"Position selector initialized; default Motor {self.selected_motor_id}. "
            "START selects 7/8, X cycles 0/+35/-35, L2/R2 trim"
        )

    @staticmethod
    def rising_edge(pressed, was_pressed):
        """Return whether a rising edge occurred and the new edge state."""
        return bool(pressed and not was_pressed), bool(pressed)

    @staticmethod
    def trigger_trim(l2, r2, deadzone):
        """Convert trigger depth difference to signed -1..1 trim input."""
        left = 0 if int(l2) < deadzone else min(int(l2), int(TRIGGER_MAX))
        right = 0 if int(r2) < deadzone else min(int(r2), int(TRIGGER_MAX))
        return max(-1.0, min((float(right) - float(left)) / TRIGGER_MAX, 1.0))

    @staticmethod
    def controls_are_neutral(toggle_pressed, l2, r2, deadzone):
        """Allow motor selection only after all shared controls are released."""
        return (
            not bool(toggle_pressed)
            and int(l2) < deadzone
            and int(r2) < deadzone
        )

    @staticmethod
    def next_motor_id(current):
        """Toggle the selected motor between 7 and 8."""
        return 8 if int(current) == 7 else 7

    def get_button(self, msg, parameter_name):
        """Read one parameter-selected button from the joystick message."""
        name = str(self.get_parameter(parameter_name).value)
        if not hasattr(msg, name):
            self.get_logger().warn(
                f"Unknown joystick button: {name}",
                throttle_duration_sec=2.0,
            )
            return False
        return bool(getattr(msg, name))

    def joystick_callback(self, msg):
        """Update selection, X edge, and trigger trim from one joystick sample."""
        self.last_joystick_time = time.monotonic()
        deadzone = max(0, int(self.get_parameter("trigger_deadzone").value))
        toggle_pressed = self.get_button(msg, "toggle_button")
        switch_pressed = self.get_button(msg, "switch_button")
        neutral = self.controls_are_neutral(
            toggle_pressed, msg.l2, msg.r2, deadzone
        )

        switch_edge, self.switch_was_pressed = self.rising_edge(
            switch_pressed, self.switch_was_pressed
        )
        self.switch_blocked = bool(switch_edge and not neutral)
        if switch_edge and neutral:
            self.selected_motor_id = self.next_motor_id(self.selected_motor_id)
            self.pending_toggle = False
            self.toggle_was_pressed = True
            self.get_logger().info(
                f"Position controls selected Motor {self.selected_motor_id}"
            )

        toggle_edge, self.toggle_was_pressed = self.rising_edge(
            toggle_pressed, self.toggle_was_pressed
        )
        self.pending_toggle = self.pending_toggle or toggle_edge
        self.trim_input = self.trigger_trim(msg.l2, msg.r2, deadzone)

    def timer_callback(self):
        """Publish selected input and neutral hold input for the other motor."""
        timeout = max(float(self.get_parameter("input_timeout_sec").value), 0.0)
        timed_out = time.monotonic() - self.last_joystick_time > timeout
        valid = not timed_out
        if timed_out:
            self.trim_input = 0.0
            self.pending_toggle = False
            self.switch_was_pressed = True
            self.toggle_was_pressed = True

        selected_data = [
            1.0 if self.pending_toggle else 0.0,
            self.trim_input,
            1.0 if valid else 0.0,
        ]
        neutral_data = [0.0, 0.0, 1.0 if valid else 0.0]

        motor7_msg = Float32MultiArray()
        motor8_msg = Float32MultiArray()
        if self.selected_motor_id == 7:
            motor7_msg.data = selected_data
            motor8_msg.data = neutral_data
        else:
            motor7_msg.data = neutral_data
            motor8_msg.data = selected_data
        self.motor7_pub.publish(motor7_msg)
        self.motor8_pub.publish(motor8_msg)

        status = Float32MultiArray()
        status.data = [
            float(self.selected_motor_id),
            1.0 if valid else 0.0,
            1.0 if self.switch_blocked else 0.0,
        ]
        self.status_pub.publish(status)
        self.pending_toggle = False
        self.switch_blocked = False


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
