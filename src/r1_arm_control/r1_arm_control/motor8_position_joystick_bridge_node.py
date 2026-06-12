#!/usr/bin/env python3
"""Joystick mapping for the experimental Motor 8 position controller."""

import time

import rclpy
from my_joystick_msgs.msg import Joystick
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class Motor8PositionJoystickBridgeNode(Node):
    """Publish X toggle events and L3/R3 position trim input.

    The bridge contains no motor or CAN logic. X emits one event on its rising
    edge. L3 and R3 form a signed trim input so Motor 7 can keep using L2/R2.
    """

    def __init__(self):
        super().__init__("motor8_position_joystick_bridge_node")

        self.declare_parameter("toggle_button", "x")
        self.declare_parameter("negative_trim_button", "l3")
        self.declare_parameter("positive_trim_button", "r3")
        self.declare_parameter("publish_hz", 20.0)
        self.declare_parameter("input_timeout_sec", 0.3)

        self.last_joystick_time = 0.0
        self.toggle_was_pressed = True
        self.pending_toggle = False
        self.trim_input = 0.0

        self.joy_sub = self.create_subscription(
            Joystick, "/joystick_data", self.joystick_callback, 10
        )
        self.command_pub = self.create_publisher(
            Float32MultiArray, "/motor8_position_input", 10
        )

        publish_hz = max(float(self.get_parameter("publish_hz").value), 1.0)
        self.timer = self.create_timer(1.0 / publish_hz, self.timer_callback)
        self.get_logger().info(
            "Motor 8 position bridge: X toggles A/B, L3/R3 trim position"
        )

    @staticmethod
    def signed_button_input(negative_pressed, positive_pressed):
        """Return -1, 0, or 1; opposite buttons cancel each other."""
        return float(bool(positive_pressed)) - float(bool(negative_pressed))

    @staticmethod
    def rising_edge(pressed, was_pressed):
        """Return whether a rising edge occurred and the new edge state."""
        return bool(pressed and not was_pressed), bool(pressed)

    def get_button(self, msg, parameter_name):
        """Read a parameter-selected button, returning false for bad names."""
        button_name = str(self.get_parameter(parameter_name).value)
        if not hasattr(msg, button_name):
            self.get_logger().warn(
                f"Unknown joystick button: {button_name}",
                throttle_duration_sec=2.0,
            )
            return False
        return bool(getattr(msg, button_name))

    def joystick_callback(self, msg):
        """Update edge memory and signed trim input from one joystick sample."""
        self.last_joystick_time = time.monotonic()
        toggle_pressed = self.get_button(msg, "toggle_button")
        edge, self.toggle_was_pressed = self.rising_edge(
            toggle_pressed, self.toggle_was_pressed
        )
        self.pending_toggle = self.pending_toggle or edge

        negative = self.get_button(msg, "negative_trim_button")
        positive = self.get_button(msg, "positive_trim_button")
        self.trim_input = self.signed_button_input(negative, positive)

    def timer_callback(self):
        """Publish continuously and fail neutral when joystick input times out."""
        timeout = max(float(self.get_parameter("input_timeout_sec").value), 0.0)
        timed_out = time.monotonic() - self.last_joystick_time > timeout
        if timed_out:
            self.trim_input = 0.0
            self.pending_toggle = False
            self.toggle_was_pressed = True

        msg = Float32MultiArray()
        msg.data = [
            1.0 if self.pending_toggle else 0.0,
            self.trim_input,
            0.0 if timed_out else 1.0,
        ]
        self.command_pub.publish(msg)
        self.pending_toggle = False


def main(args=None):
    rclpy.init(args=args)
    node = Motor8PositionJoystickBridgeNode()
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
