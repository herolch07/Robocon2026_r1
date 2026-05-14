#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from my_joystick_msgs.msg import Joystick


AXIS_MAX = 128.0


class HorizontalJoystickBridgeNode(Node):
    """
    Converts D-pad left/right input to horizontal arm speed command.

    Default mapping:
      D-pad right: positive horizontal speed
      D-pad left: negative horizontal speed
      D-pad up: increase power level
      D-pad down: decrease power level
      speed = dx / 128 * max_speed_rad_s * power_level
    """

    def __init__(self):
        super().__init__("horizontal_joystick_bridge_node")

        self.declare_parameter("max_speed_rad_s", 20.0)
        self.declare_parameter("deadzone", 6)
        self.declare_parameter("power_levels", [0.2, 0.5, 1.0])
        self.declare_parameter("default_power_index", 0)

        self.power_levels = list(self.get_parameter("power_levels").value)
        if not self.power_levels:
            self.power_levels = [1.0]
        default_index = int(self.get_parameter("default_power_index").value)
        self.power_index = max(0, min(default_index, len(self.power_levels) - 1))
        self.last_dy = 0

        self.joy_sub = self.create_subscription(
            Joystick,
            "/joystick_data",
            self.joystick_callback,
            10,
        )
        self.horizontal_pub = self.create_publisher(Float32MultiArray, "/horizontal_speed_cmd", 10)

        self.get_logger().info("Horizontal joystick bridge initialized")
        self.get_logger().info("Mapping: D-pad left/right moves, up/down changes power")
        self.get_logger().info(
            f"Power levels: {self.power_levels}, current={self.current_power():.2f}"
        )

    def joystick_callback(self, msg):
        max_speed = float(self.get_parameter("max_speed_rad_s").value)
        deadzone = int(self.get_parameter("deadzone").value)

        dx = 0 if abs(msg.dx) < deadzone else msg.dx
        dy = 0 if abs(msg.dy) < deadzone else msg.dy
        self.update_power_level(dy)

        speed = (float(dx) / AXIS_MAX) * max_speed * self.current_power()

        cmd = Float32MultiArray()
        cmd.data = [speed]
        self.horizontal_pub.publish(cmd)

    def update_power_level(self, dy):
        # D-pad Y may be positive or negative depending on controller mode.
        # Here negative means up/increase, positive means down/decrease.
        if dy != 0 and self.last_dy == 0:
            if dy < 0:
                self.power_index = min(self.power_index + 1, len(self.power_levels) - 1)
            else:
                self.power_index = max(self.power_index - 1, 0)
            self.get_logger().info(f"Horizontal power level: {self.current_power():.2f}")
        self.last_dy = dy

    def current_power(self):
        return float(self.power_levels[self.power_index])


def main(args=None):
    rclpy.init(args=args)
    node = HorizontalJoystickBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
