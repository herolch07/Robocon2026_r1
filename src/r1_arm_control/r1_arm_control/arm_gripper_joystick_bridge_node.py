#!/usr/bin/env python3
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from my_joystick_msgs.msg import Joystick


class ArmGripperJoystickBridgeNode(Node):
    """Convert L1/R1 hold duration to arm gripper speed commands."""

    def __init__(self):
        super().__init__("arm_gripper_joystick_bridge_node")

        self.declare_parameter("slow_speed_rad_s", 0.3)
        self.declare_parameter("fast_speed_rad_s", 1.3)
        self.declare_parameter("hold_threshold_sec", 0.5)
        self.declare_parameter("speed_adjust_step_rad_s", 0.1)
        self.declare_parameter("min_fast_speed_rad_s", 0.3)
        self.declare_parameter("max_fast_speed_rad_s", 1.3)

        self.fast_speed = self.clamp_fast_speed(
            float(self.get_parameter("fast_speed_rad_s").value)
        )
        self.active_direction = 0.0
        self.hold_started_at = None
        self.last_start = False
        self.last_select = False

        self.joy_sub = self.create_subscription(
            Joystick,
            "/joystick_data",
            self.joystick_callback,
            10,
        )
        self.gripper_pub = self.create_publisher(
            Float32MultiArray, "/arm_gripper_speed_cmd", 10
        )

        self.get_logger().info("Arm gripper joystick bridge initialized")
        self.get_logger().info(
            "Mapping: R1 positive, L1 negative; "
            "0.3 rad/s for first 0.5s, then adjustable fast speed"
        )
        self.get_logger().info(
            f"START (+) increases and SELECT (-) decreases fast speed; "
            f"current={self.fast_speed:.2f} rad/s"
        )

    def joystick_callback(self, msg):
        self.update_fast_speed(bool(msg.start), bool(msg.select))

        direction = 0.0
        if msg.r1 and not msg.l1:
            direction = 1.0
        elif msg.l1 and not msg.r1:
            direction = -1.0

        now = time.monotonic()
        if direction == 0.0:
            self.active_direction = 0.0
            self.hold_started_at = None
            speed = 0.0
        else:
            if direction != self.active_direction or self.hold_started_at is None:
                self.active_direction = direction
                self.hold_started_at = now

            held_sec = now - self.hold_started_at
            threshold = max(
                0.0, float(self.get_parameter("hold_threshold_sec").value)
            )
            slow_speed = abs(float(self.get_parameter("slow_speed_rad_s").value))
            speed_magnitude = slow_speed if held_sec <= threshold else self.fast_speed
            speed = direction * speed_magnitude

        cmd = Float32MultiArray()
        cmd.data = [speed]
        self.gripper_pub.publish(cmd)

    def update_fast_speed(self, start_pressed, select_pressed):
        """Adjust fast speed once per START/SELECT press."""
        step = abs(float(self.get_parameter("speed_adjust_step_rad_s").value))
        changed = False

        if start_pressed and not self.last_start and not select_pressed:
            new_speed = self.clamp_fast_speed(self.fast_speed + step)
            changed = new_speed != self.fast_speed
            self.fast_speed = new_speed
        elif select_pressed and not self.last_select and not start_pressed:
            new_speed = self.clamp_fast_speed(self.fast_speed - step)
            changed = new_speed != self.fast_speed
            self.fast_speed = new_speed

        self.last_start = start_pressed
        self.last_select = select_pressed

        if changed:
            self.get_logger().info(
                f"Arm gripper fast speed: {self.fast_speed:.2f} rad/s"
            )

    def clamp_fast_speed(self, speed):
        """Clamp the adjustable long-hold speed to the configured safe range."""
        minimum = abs(float(self.get_parameter("min_fast_speed_rad_s").value))
        maximum = abs(float(self.get_parameter("max_fast_speed_rad_s").value))
        if minimum > maximum:
            minimum, maximum = maximum, minimum
        return max(minimum, min(maximum, abs(float(speed))))


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
