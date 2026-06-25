#!/usr/bin/env python3
"""
Simple Motor Controller Script

This script acts as an intermediate between the joystick bridge and the motor controller,
converting the local_driving commands to damiao_control commands to bypass the crashing
navigation node.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import math


class SimpleMotorController(Node):
    def __init__(self):
        super().__init__('simple_motor_controller')
        
        # Subscribe to local_driving (output from joystick bridge)
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/local_driving',
            self.local_driving_callback,
            10
        )
        
        # Publish to damiao_control (input to motor controller)
        self.publisher = self.create_publisher(
            Float32MultiArray,
            '/damiao_control',
            10
        )
        
        # Throttle control to prevent overwhelming the motor controller
        self.last_cmd_time = 0
        self.cmd_interval = 0.05  # 20Hz (reduce frequency to prevent overload)
        
        self.get_logger().info("Simple motor controller initialized")
    
    def local_driving_callback(self, msg):
        """
        Convert local_driving commands to damiao_control commands
        local_driving: [direction_rad, speed_cm/s, rotation_rad/s]
        damiao_control expects: [motor_id, mode, speed, param4]
        """
        # Throttle the command rate to prevent overwhelming the motor controller
        current_time = self.get_clock().now().nanoseconds / 1e9
        if current_time - self.last_cmd_time < self.cmd_interval:
            return
        self.last_cmd_time = current_time
        
        direction = msg.data[0]  # radians
        speed = msg.data[1]      # cm/s
        rotation = msg.data[2]   # rad/s
        
        # Convert to individual wheel speeds (mecanum drive)
        # Using the kinematic model for mecanum wheels
        vx = speed * math.cos(direction) / 100.0  # Convert cm/s to m/s
        vy = speed * math.sin(direction) / 100.0  # Convert cm/s to m/s
        
        # Wheel configuration constants
        L = 0.23  # half wheel base (meters) - adjusted for your robot
        W = 0.17  # half track width (meters) - adjusted for your robot
        R = 0.05  # wheel radius (meters)
        
        # Calculate wheel velocities in m/s
        v1 = (vx - vy - (L + W) * rotation) / R  # Front-left
        v2 = (vx + vy + (L + W) * rotation) / R  # Front-right
        v3 = (vx + vy - (L + W) * rotation) / R  # Rear-right
        v4 = (vx - vy + (L + W) * rotation) / R  # Rear-left
        
        # Limit maximum speeds to prevent motor damage and reduce load
        max_speed = 40.0  # Limit to 40 rad/s
        v1 = max(min(v1, max_speed), -max_speed)
        v2 = max(min(v2, max_speed), -max_speed)
        v3 = max(min(v3, max_speed), -max_speed)
        v4 = max(min(v4, max_speed), -max_speed)
        
        # Send commands to each motor individually but in a coordinated manner
        # Format: [motor_id, mode, speed, param4]
        # Mode 3 = VEL mode, param4 = duration (0 = continuous)
        
        # Create all commands first, then publish them quickly to minimize timing differences
        commands = [
            [1, 3, float(v1), 0.0],  # Motor 1 (Front-left)
            [2, 3, float(v2), 0.0],  # Motor 2 (Front-right) 
            [3, 3, float(v3), 0.0],  # Motor 3 (Rear-right)
            [4, 3, float(v4), 0.0],  # Motor 4 (Rear-left)
        ]
        
        # Publish all commands in quick succession to synchronize them
        for cmd in commands:
            cmd_msg = Float32MultiArray()
            cmd_msg.data = cmd
            self.publisher.publish(cmd_msg)
        
        self.get_logger().debug(f"All motors: vel=({v1:.2f}, {v2:.2f}, {v3:.2f}, {v4:.2f}) rad/s")


def main(args=None):
    rclpy.init(args=args)
    node = SimpleMotorController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Send stop commands to all motors
        node.get_logger().info("Shutting down - sending stop commands to all motors")
        for motor_id in [1, 2, 3, 4]:
            cmd_msg = Float32MultiArray()
            cmd_msg.data = [motor_id, 3, 0.0, 0.0]  # Stop command
            node.publisher.publish(cmd_msg)
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()