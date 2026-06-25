#!/usr/bin/env python3
"""
简单的电机控制测试脚本
直接发布电机指令，绕过逆运动学，测试每个电机
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import time

class DirectMotorTest(Node):
    def __init__(self):
        super().__init__('direct_motor_test')
        self.publisher = self.create_publisher(Float32MultiArray, '/damiao_control', 10)
        time.sleep(1)  # 等待发布器准备好
        
    def test_motor(self, motor_id, speed, duration):
        """测试单个电机"""
        print(f"\n测试 Motor {motor_id}，速度 {speed} rad/s，持续 {duration} 秒")
        
        # 发送运动指令
        msg = Float32MultiArray()
        msg.data = [float(motor_id), 3.0, float(speed), 0.0]  # mode 3 = VEL
        self.publisher.publish(msg)
        print(f"  已发送指令: {msg.data}")
        
        time.sleep(duration)
        
        # 发送停止指令
        stop_msg = Float32MultiArray()
        stop_msg.data = [float(motor_id), 0.0, 0.0, 0.0]  # mode 0 = disable
        self.publisher.publish(stop_msg)
        print(f"  Motor {motor_id} 已停止")
        
        time.sleep(1)

def main():
    rclpy.init()
    node = DirectMotorTest()
    
    print("=" * 50)
    print("直接电机测试 - 绕过逆运动学")
    print("=" * 50)
    print("测试速度: 5.0 rad/s")
    print("每个电机运行 3 秒")
    print("")
    
    test_speed = 5.0
    test_duration = 3.0
    
    # 测试每个电机
    for motor_id in [1, 2, 3, 4]:
        node.test_motor(motor_id, test_speed, test_duration)
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)
    print("\n请告诉我：")
    print("- Motor 1 (左前): 转了吗？方向对吗？")
    print("- Motor 2 (右前): 转了吗？方向对吗？")
    print("- Motor 3 (右后): 转了吗？方向对吗？")
    print("- Motor 4 (左后): 转了吗？方向对吗？")
    print("")
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
