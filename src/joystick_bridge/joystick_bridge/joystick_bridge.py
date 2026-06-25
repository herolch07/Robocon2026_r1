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
from std_msgs.msg import Float32MultiArray, Int32
import math
import time

AXIS_MAX = 512.0
VIEW_FRONT = 0
VIEW_RIGHT = 1
VIEW_BACK = 2
VIEW_LEFT = 3
VIEW_NAMES = {
    VIEW_FRONT: "FRONT",
    VIEW_RIGHT: "RIGHT",
    VIEW_BACK: "BACK",
    VIEW_LEFT: "LEFT",
}

class JoystickBridge(Node):
    """
    手柄到底盘控制的桥接节点
    
    订阅: /joystick_data (my_joystick_msgs/Joystick)
        - lx, ly: 左摇杆坐标 (-512 到 512)
        - rx: 右摇杆 X 坐标 (-512 到 512)
    
    发布: /local_driving (std_msgs/Float32MultiArray)
        - [direction_rad, plane_speed_cm/s, rotation_rad/s]
    """
    
    def __init__(self):
        super().__init__('joystick_bridge')
        
        # 声明参数（符合 AGENTS.md 2.2.4 规范）
        self.declare_parameter('max_speed_cm', 150.0)
        self.declare_parameter('max_rotation', 3.0)
        self.declare_parameter('deadzone', 15)
        self.declare_parameter('input_timeout_sec', 0.3)
        self.declare_parameter('watchdog_hz', 20.0)
        self.declare_parameter('translation_linear_weight', 0.1)
        self.declare_parameter('rotation_linear_weight', 0.1)
        self.declare_parameter('default_view_orientation', VIEW_FRONT)
        self.declare_parameter('view_change_requires_neutral', True)

        self.last_joystick_time = 0.0
        self.joystick_seen = False
        self.timeout_stop_sent = False
        configured_view = int(self.get_parameter('default_view_orientation').value)
        self.view_orientation = (
            configured_view if configured_view in VIEW_NAMES else VIEW_FRONT
        )
        self.last_dpad_direction = None
        
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
        self.view_pub = self.create_publisher(Int32, '/view_orientation', 10)

        watchdog_hz = max(float(self.get_parameter('watchdog_hz').value), 1.0)
        self.watchdog_timer = self.create_timer(1.0 / watchdog_hz, self.watchdog_callback)
        
        self.get_logger().info("Joystick bridge node initialized")
        self.get_logger().info(f"Max speed: {self.get_parameter('max_speed_cm').value} cm/s")
        self.get_logger().info(
            "Translation curve: y = a*x + (1-a)*x^3, "
            f"a={self.get_parameter('translation_linear_weight').value}"
        )
        self.get_logger().info(
            "Rotation curve: y = a*x + (1-a)*x^3, "
            f"a={self.get_parameter('rotation_linear_weight').value}"
        )
        self.get_logger().info("START/SELECT chassis speed switching disabled")
        self.get_logger().info(
            "D-pad selects KFS gripper view: up/front, right/right, "
            "down/back, left/left"
        )
        self.publish_view_orientation()
        self.get_logger().info(f"Max rotation: {self.get_parameter('max_rotation').value} rad/s")
        self.get_logger().info(f"Deadzone: {self.get_parameter('deadzone').value}")
        self.get_logger().info(f"Input timeout: {self.get_parameter('input_timeout_sec').value}s")
        self.get_logger().info("✓ Dynamic parameter updates enabled")

    def parameter_callback(self, params):
        """Validate runtime tuning parameters before accepting an update."""
        from rcl_interfaces.msg import SetParametersResult

        for param in params:
            if param.name in ['max_speed_cm', 'max_rotation'] and float(param.value) <= 0.0:
                return SetParametersResult(
                    successful=False,
                    reason=f'{param.name} must be greater than 0',
                )
            if param.name in ['translation_linear_weight', 'rotation_linear_weight']:
                weight = float(param.value)
                if not 0.0 <= weight <= 1.0:
                    return SetParametersResult(
                        successful=False,
                        reason=f'{param.name} must be in [0.0, 1.0]',
                    )
            if param.name in [
                'max_speed_cm',
                'max_rotation',
                'deadzone',
                'input_timeout_sec',
                'translation_linear_weight',
                'rotation_linear_weight',
                'default_view_orientation',
                'view_change_requires_neutral',
            ]:
                self.get_logger().info(f"Parameter updated: {param.name} = {param.value}")

        return SetParametersResult(successful=True)
    
    def joystick_callback(self, msg):
        """
        处理手柄输入并转换为底盘指令
        
        输入: Joystick 消息 (lx, ly, rx ∈ [-512, 512])
        输出: Float32MultiArray [direction_rad, speed_cm/s, rotation_rad/s]
        """
        self.last_joystick_time = time.monotonic()
        self.joystick_seen = True
        self.timeout_stop_sent = False

        # 左搖桿先按人的視角解讀；十字鍵記錄 KFS gripper 在人視角中的方向。
        lx = msg.lx
        ly = msg.ly
        rx = msg.rx
        
        # 实时获取参数（支持运行时修改）
        max_speed_cm = self.get_parameter('max_speed_cm').value
        max_rotation = self.get_parameter('max_rotation').value
        deadzone = self.get_parameter('deadzone').value
        linear_weight = float(self.get_parameter('translation_linear_weight').value)
        rotation_linear_weight = float(
            self.get_parameter('rotation_linear_weight').value
        )
        
        # 应用死区过滤
        if abs(lx) < deadzone:
            lx = 0
        if abs(ly) < deadzone:
            ly = 0
        if abs(rx) < deadzone:
            rx = 0

        requested_view = self.orientation_from_dpad(
            msg.dx, msg.dy, self.view_orientation, deadzone
        )
        dpad_direction = self.active_dpad_direction(msg.dx, msg.dy, deadzone)
        dpad_edge = dpad_direction is not None and dpad_direction != self.last_dpad_direction
        requires_neutral = bool(
            self.get_parameter('view_change_requires_neutral').value
        )
        if dpad_edge and requested_view != self.view_orientation:
            if not requires_neutral or (lx == 0 and ly == 0):
                self.view_orientation = requested_view
                self.publish_view_orientation()
                self.get_logger().info(
                    f"Operator view set: KFS gripper is {VIEW_NAMES[self.view_orientation]}"
                )
            else:
                self.get_logger().warn(
                    "View change ignored: release the left stick first",
                    throttle_duration_sec=1.0,
                )
        self.last_dpad_direction = dpad_direction
        
        # 轉換為底盤指令
        if lx == 0 and ly == 0:
            # 摇杆回中：只考虑旋转
            direction = 0.0
            speed_cm = 0.0
        else:
            # 计算方向角 (弧度)
            # 注意：Y轴取反是因为手柄坐标系与机器人坐标系可能不同
            operator_direction = math.atan2(float(lx), -float(ly))
            direction = self.operator_to_body_direction(
                operator_direction, self.view_orientation
            )
            
            # 计算速度大小并限幅到 0-100%。斜向推杆时 lx/ly 同时接近满量程，
            # 如果不限幅，sqrt(lx^2 + ly^2) 会超过 AXIS_MAX。
            magnitude = min(math.sqrt(lx*lx + ly*ly) / AXIS_MAX, 1.0)

            # 混合三次曲线在中心区域提供低速精细控制，同时保留满杆最高速度。
            # linear_weight=1.0 为线性；0.0 为纯三次；默认 0.1。
            curved_magnitude = (
                linear_weight * magnitude
                + (1.0 - linear_weight) * magnitude ** 3
            )
            speed_cm = curved_magnitude * max_speed_cm
        
        # 右摇杆旋转使用独立混合三次曲线，保留方向和满杆最大速度。
        normalized_rotation = max(-1.0, min(float(rx) / AXIS_MAX, 1.0))
        rotation = (
            rotation_linear_weight * normalized_rotation
            + (1.0 - rotation_linear_weight) * normalized_rotation ** 3
        ) * max_rotation
        
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

    @staticmethod
    def active_dpad_direction(dx, dy, deadzone):
        """Return one exclusive D-pad direction, ignoring diagonal input."""
        horizontal = 0 if abs(int(dx)) < deadzone else (1 if dx > 0 else -1)
        vertical = 0 if abs(int(dy)) < deadzone else (1 if dy > 0 else -1)
        if bool(horizontal) == bool(vertical):
            return None
        if vertical < 0:
            return VIEW_FRONT
        if horizontal > 0:
            return VIEW_RIGHT
        if vertical > 0:
            return VIEW_BACK
        return VIEW_LEFT

    @classmethod
    def orientation_from_dpad(cls, dx, dy, current, deadzone):
        """Map D-pad position to the absolute KFS gripper orientation."""
        requested = cls.active_dpad_direction(dx, dy, deadzone)
        return int(current) if requested is None else requested

    @staticmethod
    def operator_to_body_direction(operator_direction, view_orientation):
        """Convert an operator-frame direction into the robot body frame.

        view_orientation describes where the KFS gripper is in the operator
        frame. Real-machine testing shows the chassis body-frame forward axis is
        90 degrees counter-clockwise from the visible KFS front marker, so the
        KFS view is shifted by one step before converting operator-frame motion.
        """
        body_front_view = (int(view_orientation) - 1) % 4
        body_direction = float(operator_direction) - body_front_view * math.pi / 2.0
        return math.atan2(math.sin(body_direction), math.cos(body_direction))

    def publish_view_orientation(self):
        """Publish KFS view: 0=front, 1=right, 2=back, 3=left."""
        msg = Int32()
        msg.data = int(self.view_orientation)
        self.view_pub.publish(msg)

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
