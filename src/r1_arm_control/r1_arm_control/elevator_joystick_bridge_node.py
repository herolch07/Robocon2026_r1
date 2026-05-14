#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from my_joystick_msgs.msg import Joystick


AXIS_MAX = 128.0


class ElevatorJoystickBridgeNode(Node):
    """
    Converts joystick trigger input to elevator speed command.

    Default mapping:
      R2 trigger: elevator positive speed
      L2 trigger: elevator negative speed
      speed = (r2 - l2) / 128 * max_speed_rad_s
    """

    def __init__(self):
        super().__init__("elevator_joystick_bridge_node")

        self.declare_parameter("max_speed_rad_s", 3.0)
        self.declare_parameter("deadzone", 6)

        self.joy_sub = self.create_subscription(
            Joystick,
            "/joystick_data",
            self.joystick_callback,
            10,
        )
        self.elevator_pub = self.create_publisher(Float32MultiArray, "/elevator_speed_cmd", 10)

        self.get_logger().info("Elevator joystick bridge initialized")
        self.get_logger().info("Mapping: R2 positive, L2 negative")

    def joystick_callback(self, msg):
        max_speed = float(self.get_parameter("max_speed_rad_s").value)
        deadzone = int(self.get_parameter("deadzone").value)

        l2 = 0 if msg.l2 < deadzone else msg.l2
        r2 = 0 if msg.r2 < deadzone else msg.r2
        speed = ((float(r2) - float(l2)) / AXIS_MAX) * max_speed

        cmd = Float32MultiArray()
        cmd.data = [speed]
        self.elevator_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ElevatorJoystickBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
