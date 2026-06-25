#!/usr/bin/env python3
"""KFS-mode joystick bridge for the R1 elevator actuator on Motor 5."""

import rclpy
from my_joystick_msgs.msg import Joystick
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Int32


MODE_KFS = 2


class ElevatorJoystickBridgeNode(Node):
    """Convert L1/R1 digital shoulder buttons to elevator speed in KFS mode.

    STAFF mode uses L1/R1 for Motor8/Motor7 pneumatic head toggles, so this node
    ignores them unless `/operation_mode` is KFS and fresh.
    """

    def __init__(self):
        super().__init__("elevator_joystick_bridge_node")

        self.declare_parameter("command_speed_rad_s", 28.0)
        self.declare_parameter("mode_timeout_sec", 0.5)

        self.operation_mode = 0
        self.last_mode_time = None

        self.joy_sub = self.create_subscription(
            Joystick,
            "/joystick_data",
            self.joystick_callback,
            10,
        )
        self.mode_sub = self.create_subscription(
            Int32, "/operation_mode", self.operation_mode_callback, 10
        )
        self.elevator_pub = self.create_publisher(
            Float32MultiArray, "/elevator_speed_cmd", 10
        )

        self.get_logger().info("Elevator joystick bridge initialized")
        self.get_logger().info("Mapping: KFS mode R1 positive, L1 negative, both stop")

    def operation_mode_callback(self, msg):
        """Track `/operation_mode`; only KFS mode enables elevator buttons."""
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

    @staticmethod
    def speed_from_buttons(l1_pressed, r1_pressed, command_speed):
        """Return signed elevator speed; conflicting or released buttons stop."""
        speed = abs(float(command_speed))
        if r1_pressed and not l1_pressed:
            return speed
        if l1_pressed and not r1_pressed:
            return -speed
        return 0.0

    def joystick_callback(self, msg):
        """Publish KFS-mode elevator speed from the shoulder buttons."""
        if self.kfs_mode_active():
            speed = self.speed_from_buttons(
                bool(msg.l1),
                bool(msg.r1),
                self.get_parameter("command_speed_rad_s").value,
            )
        else:
            speed = 0.0

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
