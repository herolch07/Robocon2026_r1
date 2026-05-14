#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from my_joystick_msgs.msg import Joystick


class ArmGripperJoystickBridgeNode(Node):
    """
    Converts L1/R1 button input to arm gripper speed command.

    Default mapping:
      R1: positive gripper speed
      L1: negative gripper speed
      speed = direction * max_speed_rad_s
    """

    def __init__(self):
        super().__init__("arm_gripper_joystick_bridge_node")

        self.declare_parameter("max_speed_rad_s", 1.0)

        self.joy_sub = self.create_subscription(
            Joystick,
            "/joystick_data",
            self.joystick_callback,
            10,
        )
        self.gripper_pub = self.create_publisher(Float32MultiArray, "/arm_gripper_speed_cmd", 10)

        self.get_logger().info("Arm gripper joystick bridge initialized")
        self.get_logger().info("Mapping: R1 positive, L1 negative")

    def joystick_callback(self, msg):
        max_speed = float(self.get_parameter("max_speed_rad_s").value)

        direction = 0.0
        if msg.r1 and not msg.l1:
            direction = 1.0
        elif msg.l1 and not msg.r1:
            direction = -1.0

        cmd = Float32MultiArray()
        cmd.data = [direction * max_speed]
        self.gripper_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ArmGripperJoystickBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
