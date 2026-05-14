#!/usr/bin/env python3
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class ElevatorControllerNode(Node):
    """
    Elevator safety/control node.

    Subscribes:
      /elevator_speed_cmd: Float32MultiArray [speed_rad_s]

    Publishes:
      /damiao_control: Float32MultiArray [motor_id, mode, speed_rad_s, duration]
      /elevator_status: Float32MultiArray [target_speed, commanded_speed, timeout, motor_id]
    """

    def __init__(self):
        super().__init__("elevator_controller_node")

        self.declare_parameter("motor_id", 5)
        self.declare_parameter("max_speed_rad_s", 3.0)
        self.declare_parameter("timeout_sec", 0.3)
        self.declare_parameter("publish_hz", 20.0)
        self.declare_parameter("max_accel_rad_s2", 0.0)

        self.motor_id = int(self.get_parameter("motor_id").value)
        self.target_speed = 0.0
        self.commanded_speed = 0.0
        self.last_command_time = 0.0
        self.timeout_active = True

        self.command_sub = self.create_subscription(
            Float32MultiArray,
            "/elevator_speed_cmd",
            self.elevator_command_callback,
            10,
        )
        self.motor_pub = self.create_publisher(Float32MultiArray, "/damiao_control", 10)
        self.status_pub = self.create_publisher(Float32MultiArray, "/elevator_status", 10)

        publish_hz = max(float(self.get_parameter("publish_hz").value), 1.0)
        self.period = 1.0 / publish_hz
        self.timer = self.create_timer(self.period, self.timer_callback)

        self.get_logger().info("Elevator controller initialized")
        self.get_logger().info(f"Elevator motor ID: {self.motor_id}")
        self.get_logger().info(f"Max speed: {self.get_parameter('max_speed_rad_s').value} rad/s")
        self.get_logger().info(f"Timeout: {self.get_parameter('timeout_sec').value}s")

    def elevator_command_callback(self, msg):
        if not msg.data:
            self.get_logger().warn("Invalid /elevator_speed_cmd: expected [speed_rad_s]")
            return

        max_speed = float(self.get_parameter("max_speed_rad_s").value)
        self.target_speed = max(-max_speed, min(max_speed, float(msg.data[0])))
        self.last_command_time = time.monotonic()
        self.timeout_active = False

    def timer_callback(self):
        timeout_sec = float(self.get_parameter("timeout_sec").value)
        if time.monotonic() - self.last_command_time > timeout_sec:
            self.target_speed = 0.0
            self.timeout_active = True

        self.commanded_speed = self.limit_accel(self.commanded_speed, self.target_speed)
        self.publish_motor_command(self.commanded_speed)
        self.publish_status()

    def limit_accel(self, current, target):
        max_accel = float(self.get_parameter("max_accel_rad_s2").value)
        if max_accel <= 0.0:
            return target

        max_delta = max_accel * self.period
        delta = target - current
        if abs(delta) <= max_delta:
            return target
        return current + max_delta * (1.0 if delta > 0.0 else -1.0)

    def publish_motor_command(self, speed):
        msg = Float32MultiArray()
        msg.data = [float(self.motor_id), 3.0, float(speed), 0.0]
        self.motor_pub.publish(msg)

    def publish_status(self):
        msg = Float32MultiArray()
        msg.data = [
            float(self.target_speed),
            float(self.commanded_speed),
            1.0 if self.timeout_active else 0.0,
            float(self.motor_id),
        ]
        self.status_pub.publish(msg)

    def destroy_node(self):
        self.publish_motor_command(0.0)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ElevatorControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
