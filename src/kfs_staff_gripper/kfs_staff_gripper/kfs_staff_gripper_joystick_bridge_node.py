#!/usr/bin/env python3
"""KFS-mode joystick bridge for the KFS gripper relay."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32, Int32MultiArray

from my_joystick_msgs.msg import Joystick


MODE_KFS = 2


class KfsStaffGripperJoystickBridgeNode(Node):
    """Convert one KFS-mode joystick button into the KFS gripper relay command.

    Default mapping:
      Y: toggle KFS gripper OPEN/CLOSE on each press, only in KFS mode.

    SELECT/START are owned by operation_mode_selector_node. In STAFF mode the Y
    button is used by the staff pneumatic bridge for Motor 8 height, so this node
    ignores Y unless `/operation_mode` is KFS and fresh.
    """

    def __init__(self):
        super().__init__("kfs_staff_gripper_joystick_bridge_node")

        self.declare_parameter("staff_button", "y")
        self.declare_parameter("publish_hz", 20.0)
        self.declare_parameter("input_timeout_sec", 0.3)
        self.declare_parameter("mode_timeout_sec", 0.5)
        self.declare_parameter("safe_state", [0])

        self.last_joystick_time = None
        self.last_mode_time = None
        self.operation_mode = 0
        self.current_state = self.get_safe_state()
        self.staff_toggle_pressed = True

        self.joy_sub = self.create_subscription(
            Joystick,
            "/joystick_data",
            self.joystick_callback,
            10,
        )
        self.mode_sub = self.create_subscription(
            Int32, "/operation_mode", self.operation_mode_callback, 10
        )
        self.cmd_pub = self.create_publisher(Int32MultiArray, "/kfs_staff_gripper_cmd", 10)

        publish_hz = max(float(self.get_parameter("publish_hz").value), 1.0)
        self.publish_timer = self.create_timer(1.0 / publish_hz, self.publish_timer_callback)

        self.get_logger().info("KFS gripper joystick bridge initialized")
        self.get_logger().info(
            "Mapping: KFS mode only, "
            f"{self.get_parameter('staff_button').value} -> toggle KFS gripper open/close"
        )

    def get_safe_state(self):
        """Return the one-channel KFS gripper safe state."""
        raw = list(self.get_parameter("safe_state").value)
        safe = [0]
        for index, value in enumerate(raw[:1]):
            safe[index] = 1 if int(value) else 0
        return safe

    def operation_mode_callback(self, msg):
        """Track `/operation_mode`; only KFS mode enables this bridge."""
        self.operation_mode = int(msg.data)
        self.last_mode_time = self.get_clock().now()

    def kfs_mode_active(self):
        """Return true only while a fresh KFS mode message is present."""
        if self.last_mode_time is None:
            return False
        elapsed = (self.get_clock().now() - self.last_mode_time).nanoseconds / 1e9
        return (
            self.operation_mode == MODE_KFS
            and elapsed <= float(self.get_parameter("mode_timeout_sec").value)
        )

    def joystick_callback(self, msg):
        """Toggle the KFS gripper once on each configured button press in KFS mode."""
        self.last_joystick_time = self.get_clock().now()
        staff_button = str(self.get_parameter("staff_button").value)
        pressed = self.get_button(msg, staff_button) if self.kfs_mode_active() else False
        state, self.staff_toggle_pressed = self.apply_staff_toggle(
            self.current_state[0],
            pressed,
            self.staff_toggle_pressed,
        )
        self.current_state = [state]
        if not self.kfs_mode_active():
            self.staff_toggle_pressed = True

    @staticmethod
    def apply_staff_toggle(state, pressed, was_pressed):
        """Toggle CLOSE/OPEN once on a button rising edge."""
        if pressed and not was_pressed:
            state = 1 - state
        return state, pressed

    def get_button(self, msg, button_name):
        """Read a boolean button from Joystick by name, returning False if invalid."""
        if not hasattr(msg, button_name):
            self.get_logger().warn(f"Unknown joystick button: {button_name}")
            return False
        return bool(getattr(msg, button_name))

    def publish_timer_callback(self):
        """Refresh command output and fail safe if joystick input times out."""
        if self.is_joystick_timed_out():
            self.current_state = self.get_safe_state()
            self.staff_toggle_pressed = True
        self.publish_state(self.current_state)

    def is_joystick_timed_out(self):
        """Return true when /joystick_data has stopped for input_timeout_sec."""
        if self.last_joystick_time is None:
            return True
        elapsed = (self.get_clock().now() - self.last_joystick_time).nanoseconds / 1e9
        return elapsed > float(self.get_parameter("input_timeout_sec").value)

    def publish_state(self, state):
        """Publish [kfs_gripper_state]."""
        cmd = Int32MultiArray()
        cmd.data = [int(state[0])]
        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = KfsStaffGripperJoystickBridgeNode()
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
