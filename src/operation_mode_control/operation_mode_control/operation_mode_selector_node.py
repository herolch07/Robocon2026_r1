#!/usr/bin/env python3
"""Select the active robot mechanism operation mode from joystick buttons.

This node intentionally owns only the operator mode state. It does not command
any actuator directly. Mechanism bridge nodes subscribe to ``/operation_mode``
and decide whether their local button mapping should be active.
"""

import time

import rclpy
from my_joystick_msgs.msg import Joystick
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32

MODE_INVALID = 0
MODE_STAFF = 1
MODE_KFS = 2
MODE_NAMES = {
    MODE_INVALID: "INVALID",
    MODE_STAFF: "STAFF",
    MODE_KFS: "KFS",
}


class OperationModeSelectorNode(Node):
    """Publish STAFF/KFS mode selected by two joystick buttons.

    Default mapping:
      SELECT: STAFF mode
      START: KFS mode

    The node publishes ``MODE_INVALID`` when joystick input is stale. This makes
    downstream bridges ignore mechanism buttons instead of continuing with an
    old mode if the controller data path fails.
    """

    def __init__(self):
        super().__init__("operation_mode_selector_node")

        self.declare_parameter("staff_button", "select")
        self.declare_parameter("kfs_button", "start")
        self.declare_parameter("default_mode", MODE_STAFF)
        self.declare_parameter("publish_hz", 10.0)
        self.declare_parameter("input_timeout_sec", 0.5)

        configured_default = int(self.get_parameter("default_mode").value)
        self.current_mode = self.normalize_mode(configured_default)
        if self.current_mode == MODE_INVALID:
            self.current_mode = MODE_STAFF

        self.last_joystick_time = 0.0
        self.joystick_seen = False
        self.staff_was_pressed = True
        self.kfs_was_pressed = True

        self.joy_sub = self.create_subscription(
            Joystick, "/joystick_data", self.joystick_callback, 10
        )
        self.mode_pub = self.create_publisher(Int32, "/operation_mode", 10)

        publish_hz = max(float(self.get_parameter("publish_hz").value), 1.0)
        self.publish_timer = self.create_timer(1.0 / publish_hz, self.publish_mode)

        self.get_logger().info(
            "Operation mode selector initialized: SELECT=STAFF, START=KFS"
        )

    @staticmethod
    def normalize_mode(value):
        """Clamp an arbitrary numeric mode to one of the supported constants."""
        mode = int(value)
        return mode if mode in (MODE_INVALID, MODE_STAFF, MODE_KFS) else MODE_INVALID

    @staticmethod
    def rising_edge(pressed, was_pressed):
        """Return true once when a button transitions from released to pressed."""
        pressed = bool(pressed)
        return bool(pressed and not was_pressed), pressed

    @classmethod
    def resolve_mode(cls, current_mode, staff_edge, kfs_edge):
        """Resolve simultaneous selector input without creating ambiguous mode jumps."""
        if staff_edge and not kfs_edge:
            return MODE_STAFF
        if kfs_edge and not staff_edge:
            return MODE_KFS
        return cls.normalize_mode(current_mode) or MODE_STAFF

    def joystick_callback(self, msg):
        """Update the selected mode from SELECT/START rising edges."""
        self.last_joystick_time = time.monotonic()
        self.joystick_seen = True

        staff_pressed = self.get_button(msg, str(self.get_parameter("staff_button").value))
        kfs_pressed = self.get_button(msg, str(self.get_parameter("kfs_button").value))

        staff_edge, self.staff_was_pressed = self.rising_edge(
            staff_pressed, self.staff_was_pressed
        )
        kfs_edge, self.kfs_was_pressed = self.rising_edge(
            kfs_pressed, self.kfs_was_pressed
        )

        next_mode = self.resolve_mode(self.current_mode, staff_edge, kfs_edge)
        if next_mode != self.current_mode:
            self.current_mode = next_mode
            self.get_logger().info(f"Operation mode set to {MODE_NAMES[self.current_mode]}")

    def get_button(self, msg, button_name):
        """Read one Joystick button by field name, returning False if invalid."""
        if not hasattr(msg, button_name):
            self.get_logger().warn(
                f"Unknown operation mode button: {button_name}",
                throttle_duration_sec=2.0,
            )
            return False
        return bool(getattr(msg, button_name))

    def publish_mode(self):
        """Publish current mode, or INVALID if joystick data is stale."""
        mode = self.current_mode
        timeout = max(float(self.get_parameter("input_timeout_sec").value), 0.0)
        if not self.joystick_seen or time.monotonic() - self.last_joystick_time > timeout:
            mode = MODE_INVALID

        msg = Int32()
        msg.data = int(mode)
        self.mode_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = OperationModeSelectorNode()
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
