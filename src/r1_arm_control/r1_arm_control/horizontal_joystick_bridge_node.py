#!/usr/bin/env python3
"""KFS-mode joystick bridge for Motor 6 horizontal motion using L2/R2."""

import rclpy
from my_joystick_msgs.msg import Joystick
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Int32


TRIGGER_MAX = 512.0
MODE_KFS = 2


class HorizontalJoystickBridgeNode(Node):
    """Convert L2/R2 trigger depth to a fixed signed Motor 6 speed in KFS mode.

    STAFF mode uses L2/R2 for Motor8/Motor7 position trim, so this node ignores
    triggers unless `/operation_mode` is KFS and fresh.
    """

    def __init__(self):
        super().__init__("horizontal_joystick_bridge_node")

        self.declare_parameter("command_speed_rad_s", 30.0)
        self.declare_parameter("trigger_deadzone", 24)
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
        self.horizontal_pub = self.create_publisher(
            Float32MultiArray, "/horizontal_speed_cmd", 10
        )

        self.get_logger().info("Horizontal joystick bridge initialized")
        self.get_logger().info("Mapping: KFS mode L2 positive/out, R2 negative/in")

    def operation_mode_callback(self, msg):
        """Track `/operation_mode`; only KFS mode enables horizontal triggers."""
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
    def trigger_axis(value, deadzone):
        """Convert one trigger depth to normalized 0..1 after deadzone."""
        depth = 0 if int(value) < int(deadzone) else min(int(value), int(TRIGGER_MAX))
        return max(0.0, min(float(depth) / TRIGGER_MAX, 1.0))

    @classmethod
    def speed_from_triggers(cls, l2, r2, command_speed, deadzone=24):
        """Return signed speed from analog triggers; L2 positive, R2 negative."""
        speed = abs(float(command_speed))
        left = cls.trigger_axis(l2, deadzone)
        right = cls.trigger_axis(r2, deadzone)
        return max(-speed, min((left - right) * speed, speed))

    @staticmethod
    def speed_from_buttons(l3_pressed, r3_pressed, command_speed):
        """Legacy helper retained for old tests; L3 positive and R3 negative."""
        speed = abs(float(command_speed))
        if l3_pressed and not r3_pressed:
            return speed
        if r3_pressed and not l3_pressed:
            return -speed
        return 0.0

    def joystick_callback(self, msg):
        """Publish Motor 6 speed from L2/R2 only in KFS mode."""
        if self.kfs_mode_active():
            speed = self.speed_from_triggers(
                msg.l2,
                msg.r2,
                self.get_parameter("command_speed_rad_s").value,
                self.get_parameter("trigger_deadzone").value,
            )
        else:
            speed = 0.0
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
