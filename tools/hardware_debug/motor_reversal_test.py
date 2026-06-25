#!/usr/bin/env python3
import argparse
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class MotorReversalTest(Node):
    def __init__(self):
        super().__init__("motor_reversal_test")
        self.publisher = self.create_publisher(Float32MultiArray, "/damiao_control", 10)

    def publish_command(self, motor_id, speed):
        msg = Float32MultiArray()
        msg.data = [float(motor_id), 3.0, float(speed), 0.0]
        self.publisher.publish(msg)
        self.get_logger().info(f"motor={motor_id}, speed={speed}")

    def hold_speed(self, motor_id, speed, duration, rate_hz):
        if duration <= 0:
            return

        period = 1.0 / rate_hz
        deadline = time.time() + duration
        while time.time() < deadline:
            self.publish_command(motor_id, speed)
            rclpy.spin_once(self, timeout_sec=0.0)
            time.sleep(period)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--motor", type=int, required=True, choices=[1, 2, 3, 4])
    parser.add_argument("--speed", type=float, default=10.0)
    parser.add_argument("--hold", type=float, default=1.0)
    parser.add_argument("--stop-dwell", type=float, default=0.0)
    parser.add_argument("--rate", type=float, default=20.0)
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()

    rclpy.init()
    node = MotorReversalTest()

    try:
        deadline = time.time() + 2.0
        while time.time() < deadline and node.publisher.get_subscription_count() == 0:
            rclpy.spin_once(node, timeout_sec=0.05)

        if node.publisher.get_subscription_count() == 0:
            node.get_logger().error("No /damiao_control subscriber found.")
            return

        for _ in range(args.repeat):
            node.hold_speed(args.motor, args.speed, args.hold, args.rate)

            node.hold_speed(args.motor, 0.0, args.stop_dwell, args.rate)
            node.hold_speed(args.motor, -args.speed, args.hold, args.rate)
            node.hold_speed(args.motor, 0.0, args.stop_dwell, args.rate)

        node.hold_speed(args.motor, 0.0, 0.3, args.rate)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
