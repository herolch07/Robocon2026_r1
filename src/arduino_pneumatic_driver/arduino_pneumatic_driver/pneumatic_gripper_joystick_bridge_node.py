#!/usr/bin/env python3
"""
Joystick bridge for the Arduino pneumatic gripper.

This node maps controller buttons to the required pneumatic gripper sequence.
It contains no serial or hardware logic.
"""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray

from my_joystick_msgs.msg import Joystick


class PneumaticGripperJoystickBridgeNode(Node):
    """
    Convert joystick buttons into gripper hold and height toggle commands.

    Current real-machine mapping:
      B: toggle arm gripper OPEN/CLOSE on each press
      A: toggle arm height LOW/HIGH on each press

    Relay command order is [height_state, gripper_state] on the current wiring.
    Initial and timeout output is [0, 0]: height low, gripper open.
    """

    def __init__(self):
        super().__init__("pneumatic_gripper_joystick_bridge_node")

        self.declare_parameter("initial_height_state", 0)
        self.declare_parameter("height_toggle_button", "a")
        self.declare_parameter("publish_hz", 20.0)
        self.declare_parameter("input_timeout_sec", 0.3)

        self.height_state = self.normalize_state(
            self.get_parameter("initial_height_state").value
        )
        self.gripper_state = 0
        self.gripper_toggle_pressed = True
        self.height_toggle_pressed = True
        self.last_joystick_time = None

        self.joy_sub = self.create_subscription(
            Joystick,
            "/joystick_data",
            self.joystick_callback,
            10,
        )
        self.cmd_pub = self.create_publisher(Int32MultiArray, "/pneumatic_gripper_cmd", 10)

        publish_hz = max(float(self.get_parameter("publish_hz").value), 1.0)
        self.publish_timer = self.create_timer(1.0 / publish_hz, self.publish_timer_callback)

        self.get_logger().info("Pneumatic gripper joystick bridge initialized")
        self.get_logger().info(
            "Mapping: B toggles gripper open/close, "
            f"{self.get_parameter('height_toggle_button').value} toggles height; "
            "startup height low"
        )

    def joystick_callback(self, msg):
        """
        Update pneumatic state from joystick buttons.

        B toggles the arm gripper OPEN/CLOSE on its rising edge. The configured
        height button toggles LOW/HIGH the same way, so holding either button
        cannot repeatedly switch the pneumatic valves.
        """
        self.last_joystick_time = self.get_clock().now()

        toggle_button = str(self.get_parameter("height_toggle_button").value)
        toggle_pressed = self.get_button(msg, toggle_button)
        self.height_state, self.height_toggle_pressed = self.apply_height_toggle(
            self.height_state,
            toggle_pressed,
            self.height_toggle_pressed,
        )

        self.gripper_state, self.gripper_toggle_pressed = self.apply_gripper_toggle(
            self.gripper_state,
            bool(msg.b),
            self.gripper_toggle_pressed,
        )

        # The timer is the single publisher path. Keeping command output there
        # avoids duplicate serial traffic when joystick updates arrive at 20Hz.

    def normalize_state(self, value):
        """Convert any numeric state parameter to the relay protocol value 0 or 1."""
        return 1 if int(value) else 0

    @staticmethod
    def apply_height_toggle(height_state, pressed, was_pressed):
        """Toggle once on a button rising edge and return state plus edge memory."""
        if pressed and not was_pressed:
            height_state = 1 - height_state
        return height_state, pressed

    @staticmethod
    def apply_gripper_toggle(gripper_state, pressed, was_pressed):
        """Toggle OPEN/CLOSE once on a B-button rising edge."""
        if pressed and not was_pressed:
            gripper_state = 1 - gripper_state
        return gripper_state, pressed

    def get_button(self, msg, button_name):
        """Read one named joystick button, returning false for invalid names."""
        if not hasattr(msg, button_name):
            self.get_logger().warn(
                f"Unknown height_toggle_button: {button_name}",
                throttle_duration_sec=2.0,
            )
            return False
        return bool(getattr(msg, button_name))

    def publish_timer_callback(self):
        """
        Keep refreshing the current gripper latch and height hold state.

        If joystick input is lost, the bridge opens the gripper and returns
        height to the startup LOW state.
        """
        if self.is_joystick_timed_out():
            # Require both toggle buttons to be released after timeout.
            self.height_toggle_pressed = True
            self.gripper_toggle_pressed = True
            self.gripper_state = 0
            self.height_state = 0

        self.publish_state([self.height_state, self.gripper_state])

    def is_joystick_timed_out(self):
        """Return true when joystick updates stop, so the node can return to startup safe state."""
        if self.last_joystick_time is None:
            return True

        elapsed = (self.get_clock().now() - self.last_joystick_time).nanoseconds / 1e9
        return elapsed > float(self.get_parameter("input_timeout_sec").value)

    def publish_state(self, state):
        """Publish [height_state, gripper_state] for the current relay wiring."""
        cmd = Int32MultiArray()
        cmd.data = [int(state[0]), int(state[1])]
        self.cmd_pub.publish(cmd)


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
