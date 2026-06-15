#!/usr/bin/env python3
"""Joystick bridge for Motor 6 horizontal motion using L3/R3."""

import rclpy
from my_joystick_msgs.msg import Joystick
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class HorizontalJoystickBridgeNode(Node):
    """Convert L3/R3 buttons to a fixed signed Motor 6 speed command.

    R3 commands positive motion, L3 commands negative motion, and pressing both
    or neither publishes zero. The downstream controller provides the 0.3 s
    command watchdog and motor speed clamp.
    """

    def __init__(self):
        super().__init__("horizontal_joystick_bridge_node")

        self.declare_parameter("command_speed_rad_s", 10.0)

        self.joy_sub = self.create_subscription(
            Joystick,
            "/joystick_data",
            self.joystick_callback,
            10,
        )
        self.horizontal_pub = self.create_publisher(
            Float32MultiArray, "/horizontal_speed_cmd", 10
        )

        self.get_logger().info("Horizontal joystick bridge initialized")
        self.get_logger().info("Mapping: R3 positive, L3 negative, both stop")

    @staticmethod
    def speed_from_buttons(l3_pressed, r3_pressed, command_speed):
        """Return fixed signed speed; conflicting or released buttons stop."""
        speed = abs(float(command_speed))
        if r3_pressed and not l3_pressed:
            return speed
        if l3_pressed and not r3_pressed:
            return -speed
        return 0.0

    def joystick_callback(self, msg):
        """Publish Motor 6 speed from the two stick-click buttons."""
        speed = self.speed_from_buttons(
            bool(msg.l3),
            bool(msg.r3),
            self.get_parameter("command_speed_rad_s").value,
        )
        cmd = Float32MultiArray()
        cmd.data = [speed]
        self.horizontal_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = HorizontalJoystickBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
