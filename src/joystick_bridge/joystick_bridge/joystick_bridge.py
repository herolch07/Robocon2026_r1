#!/usr/bin/env python3
"""
Joystick to Navigation Bridge Node

功能:
- 订阅手柄数据 (/joystick_data)
- 将摇杆映射到底盘运动指令
- 发布到 local_driving 话题

控制映射:
- 左摇杆 X (lx): 控制运动方向
- 左摇杆 Y (ly): 控制平移速度
- 右摇杆 X (rx): 控制旋转速度

符合 AGENTS.md 规范:
- 使用 Python 实现（规范 9.3）
- 包含完整注释和文档
- 参数化配置
- 明确的接口定义
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from my_joystick_msgs.msg import Joystick
from std_msgs.msg import Float32MultiArray
import math
import time

AXIS_MAX = 128.0

class JoystickBridge(Node):
    """
    手柄到底盘控制的桥接节点
    
    订阅: /joystick_data (my_joystick_msgs/Joystick)
        - lx, ly: 左摇杆坐标 (-128 到 128)
        - rx: 右摇杆 X 坐标 (-128 到 128)
    
    发布: /local_driving (std_msgs/Float32MultiArray)
        - [direction_rad, plane_speed_cm/s, rotation_rad/s]
    """
    
    def __init__(self):
        super().__init__('joystick_bridge')
        
        # 声明参数（符合 AGENTS.md 2.2.4 规范）
        self.declare_parameter('max_speed_cm', 40.0)
        self.declare_parameter('max_rotation', 1.0)
        self.declare_parameter('deadzone', 6)
        self.declare_parameter('input_timeout_sec', 0.3)
        self.declare_parameter('watchdog_hz', 20.0)

        self.last_joystick_time = 0.0
        self.joystick_seen = False
        self.timeout_stop_sent = False
        
        # 添加参数回调以支持运行时动态调整
        self.add_on_set_parameters_callback(self.parameter_callback)
        
        # 订阅手柄数据
        self.joy_sub = self.create_subscription(
            Joystick,
            '/joystick_data',
            self.joystick_callback,
            10
        )
        
        # 发布底盘控制指令
        self.nav_pub = self.create_publisher(
            Float32MultiArray,
            '/local_driving',
            10
        )

        watchdog_hz = max(float(self.get_parameter('watchdog_hz').value), 1.0)
        self.watchdog_timer = self.create_timer(1.0 / watchdog_hz, self.watchdog_callback)
        
        self.get_logger().info("Joystick bridge node initialized")
        self.get_logger().info(f"Max speed: {self.get_parameter('max_speed_cm').value} cm/s")
        self.get_logger().info(f"Max rotation: {self.get_parameter('max_rotation').value} rad/s")
        self.get_logger().info(f"Deadzone: {self.get_parameter('deadzone').value}")
        self.get_logger().info(f"Input timeout: {self.get_parameter('input_timeout_sec').value}s")
        self.get_logger().info("✓ Dynamic parameter updates enabled")
    
    def parameter_callback(self, params):
        """
        运行时参数更新回调
        允许在节点运行时动态调整速度参数
        """
        from rcl_interfaces.msg import SetParametersResult
        
        for param in params:
            if param.name in ['max_speed_cm', 'max_rotation', 'deadzone', 'input_timeout_sec']:
                self.get_logger().info(f"Parameter updated: {param.name} = {param.value}")
        
        return SetParametersResult(successful=True)
    
    def joystick_callback(self, msg):
        """
        处理手柄输入并转换为底盘指令
        
        输入: Joystick 消息 (lx, ly, rx ∈ [-128, 128])
        输出: Float32MultiArray [direction_rad, speed_cm/s, rotation_rad/s]
        """
        self.last_joystick_time = time.monotonic()
        self.joystick_seen = True
        self.timeout_stop_sent = False

        # 从手柄读取数据
        lx = msg.lx  # 左摇杆 X
        ly = msg.ly  # 左摇杆 Y
        rx = msg.rx  # 右摇杆 X
        
        # 实时获取参数（支持运行时修改）
        max_speed_cm = self.get_parameter('max_speed_cm').value
        max_rotation = self.get_parameter('max_rotation').value
        deadzone = self.get_parameter('deadzone').value
        
        # 应用死区过滤
        if abs(lx) < deadzone:
            lx = 0
        if abs(ly) < deadzone:
            ly = 0
        if abs(rx) < deadzone:
            rx = 0
        
        # 转换为底盘指令
        if lx == 0 and ly == 0:
            # 摇杆回中：只考虑旋转
            direction = 0.0
            speed_cm = 0.0
        else:
            # 计算方向角 (弧度)
            # 注意：Y轴取反是因为手柄坐标系与机器人坐标系可能不同
            direction = math.atan2(float(lx), -float(ly))
            
            # 计算速度大小并限幅到 0-100%。斜向推杆时 lx/ly 同时接近满量程，
            # 如果不限幅，sqrt(lx^2 + ly^2) 会超过 AXIS_MAX。
            magnitude = min(math.sqrt(lx*lx + ly*ly) / AXIS_MAX, 1.0)
            speed_cm = magnitude * max_speed_cm
        
        # 计算旋转速度
        rotation = (rx / AXIS_MAX) * max_rotation
        
        # 构造导航消息
        nav_msg = Float32MultiArray()
        nav_msg.data = [direction, speed_cm, rotation]
        
        # 发布指令
        self.nav_pub.publish(nav_msg)
        
        # 调试日志（只在有明显运动时输出）
        if speed_cm > 1.0 or abs(rotation) > 0.1:
            self.get_logger().debug(
                f"Joy: lx={lx}, ly={ly}, rx={rx} → "
                f"Nav: dir={math.degrees(direction):.1f}°, "
                f"speed={speed_cm:.1f}cm/s, rot={rotation:.2f}rad/s"
            )

    def watchdog_callback(self):
        """
        输入链路看门狗。

        如果一段时间没有收到 /joystick_data，主动向 /local_driving 发布零速度。
        这样即使 joystick_node 或手柄链路异常，底盘上层指令也会回到安全状态。
        """
        if not self.joystick_seen:
            return

        timeout_sec = float(self.get_parameter('input_timeout_sec').value)
        if time.monotonic() - self.last_joystick_time <= timeout_sec:
            return

        if not self.timeout_stop_sent:
            self.publish_stop_command()
            self.timeout_stop_sent = True
            self.get_logger().warn(
                f"No /joystick_data for {timeout_sec:.2f}s; published stop to /local_driving"
            )

    def publish_stop_command(self):
        """发布底盘停止指令，供 timeout 和节点关闭共用。"""
        stop_msg = Float32MultiArray()
        stop_msg.data = [0.0, 0.0, 0.0]
        self.nav_pub.publish(stop_msg)
    
    def destroy_node(self):
        """节点销毁时的安全处理"""
        try:
            self.publish_stop_command()
            self.get_logger().info("Joystick bridge stopped - sent stop command")
        except Exception:
            pass
        finally:
            super().destroy_node()


def main(args=None):
    """主函数"""
    rclpy.init(args=args)
    node = JoystickBridge()
    
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
