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
    Convert joystick buttons into gripper open and height latch commands.

    Default mapping:
      B: gripper open, D9 = 0, keep current height
      A: latch height high, D8 = 1
      X: latch height low, D8 = 0

    Initial state is [1, 0]: gripper close, height low. After A is pressed,
    height stays high until X is pressed. After X is pressed, height stays low
    until A is pressed again.
    """

    def __init__(self):
        super().__init__("pneumatic_gripper_joystick_bridge_node")

        self.declare_parameter("initial_height_state", 0)
        self.declare_parameter("publish_hz", 20.0)

        self.height_state = self.normalize_state(
            self.get_parameter("initial_height_state").value
        )
        self.gripper_state = 1
        self.height_latched = False

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
        self.get_logger().info("Mapping: B open gripper, A height high, X height low")

    def joystick_callback(self, msg):
        """
        Update pneumatic state from joystick buttons.

        A latches height high. X latches height low. B opens the gripper while
        it is held; releasing B closes the gripper while preserving height.
        """
        if msg.a:
            self.height_state = 1
            self.height_latched = True
        if msg.x:
            self.height_state = 0
            self.height_latched = True

        self.gripper_state = 0 if msg.b else 1

        if msg.b or msg.a or msg.x or self.height_latched:
            self.publish_state([self.gripper_state, self.height_state])

    def normalize_state(self, value):
        """Convert any numeric state parameter to the relay protocol value 0 or 1."""
        return 1 if int(value) else 0

    def publish_timer_callback(self):
        """
        Keep refreshing the latched height state after A or X is pressed.

        This prevents the lower-level driver timeout from returning D8 to the
        startup safe state once the match flow has selected a height state.
        """
        if self.height_latched:
            self.publish_state([self.gripper_state, self.height_state])

    def publish_state(self, state):
        """Publish [D9_gripper_state, D8_height_state] to the serial driver node."""
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
