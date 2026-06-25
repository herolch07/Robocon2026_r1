"""
Local Navigation Node for R2 Omniwheel Base

功能:
- 订阅高层运动指令 (local_driving: [direction_rad, plane_speed_cm/s, rotation_rad/s])
- 计算 4 轮全向底盘的逆运动学
- 发布各电机速度控制指令到 damiao_control

机械参数:
- 4 轮 X 型布局 (45°, 135°, 225°, 315°)
- 轮心距中心距离: 327.038 mm = 0.327038 m
- 全向轮半径: 63.5 mm = 0.0635 m
- 轮子编号: 1(左前), 2(右前), 3(右后), 4(左后)
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import Float32MultiArray
import numpy as np
import time

# 默认机械参数。运行时会复制到 ROS 参数，方便不同底盘小改动时不改源码。
WHEEL_BASE_RADIUS = 0.327038  # 轮心到底盘中心距离 (m)
OMNIWHEEL_RADIUS_M = 0.0635  # 全向轮半径 (m)

# 轮子角度 (X 型布局，单位：弧度)
# 实际布局（从上方看机器人）：
#        前方 (Front)
#           ↑
#     M1         M2
#      \         /
#       \       /
#        \     /
#         机器人
#        /     \
#       /       \
#      /         \
#     M4         M3
#
# 电机位置与安装角度（X型全向轮标准配置）：
# - Motor 1: 左前 (Left Front)  - 45°  角度
# - Motor 2: 右前 (Right Front) - 135° 角度  
# - Motor 3: 右后 (Right Back)  - 225° 角度
# - Motor 4: 左后 (Left Back)   - 315° 角度
#
# 注意：这里的角度是相对于机器人坐标系的安装角度

WHEEL_ANGLES = {
    1: np.deg2rad(45),    # 左前
    2: np.deg2rad(135),   # 右前
    3: np.deg2rad(225),   # 右后
    4: np.deg2rad(315),   # 左后
}

# 电机方向标志 (1=正常, -1=反转)。
# 这里仅描述电机接线/安装方向，不描述底盘运动基底。
MOTOR_DIRECTION = {
    1: -1,  # 左前 - 反转（直接测试确认需要反转）
    2: 1,   # 右前 - 正常
    3: -1,  # 右后 - 反转
    4: 1,   # 左后 - 正常（手动测试确认：逆运动学输出已经是反向，不需要再反转）
}

# 实机校准后的 3 个运动基底。
#
# 当前底盘轮位:
#   1 = 左前, 2 = 右前, 3 = 右后, 4 = 左后
#
# 这里把底盘运动拆成 forward / lateral / rotation 三组独立系数。
# 每组系数仍然通过 ROS 参数暴露，后续如果换轮组安装或电机编号，只需调参数。
# 这些系数会再叠加 motor_direction_*, 所以不要把电机反转重复写进这里。
FORWARD_COEFF = {
    1: 1.0,
    2: 1.0,
    3: -1.0,
    4: -1.0,
}

# X 型四轮全向底盘的横移基底必须使用前左/后左与前右/后右的交叉组合。
# 旧版全 -1 会让左右摇杆时四个轮子都转，但底盘受力互相抵消，无法横移。
LATERAL_COEFF = {
    1: 1.0,
    2: -1.0,
    3: -1.0,
    4: 1.0,
}

# 原地旋转基底使用实机确认的对角组合。
# [1, 1, 1, 1] 会四轮转但车体不转，[-1, 1, 1, -1] 会变成横移。
# 如果实机旋转方向相反，只需要调整 rotation_axis_sign。
ROTATION_COEFF = {
    1: 1.0,
    2: -1.0,
    3: 1.0,
    4: -1.0,
}

# ROS2 控制参数
DEFAULT_MOTOR_MODE = 3  # VEL 模式
DEFAULT_DURATION = 0.0  # 0 = 持续运行，由下一条指令更新


class LocalNavigationNode(Node):
    """
    本地导航节点
    
    订阅: local_driving (Float32MultiArray)
        格式: [direction_rad, plane_speed_cm/s, rotation_rad/s]
        - direction_rad: 运动方向（弧度，0=正前方，逆时针为正）
        - plane_speed_cm/s: 平移速度（cm/s）
        - rotation_rad/s: 旋转速度（rad/s，逆时针为正）
    
    发布: damiao_control (Float32MultiArray)
        格式: [motor_id, mode, speed_rad/s, duration]
        - 为 4 个电机独立发布速度指令
    
    运动学模型: 4 轮全向 X 型布局
    """
    
    def __init__(self):
        super().__init__("local_navigation_node")

        self.declare_parameter("command_timeout_sec", 0.3)
        self.declare_parameter("watchdog_hz", 20.0)
        self.declare_parameter("wheel_base_radius_m", WHEEL_BASE_RADIUS)
        self.declare_parameter("omniwheel_radius_m", OMNIWHEEL_RADIUS_M)
        self.declare_parameter("lateral_axis_sign", 1.0)
        self.declare_parameter("rotation_axis_sign", 1.0)
        # DM-S3519 geared-output rated speed is 395 rpm (41.36 rad/s).
        # Keep the software hard limit slightly below that rated point.
        self.declare_parameter("max_wheel_speed_rad_s", 40.0)
        self.declare_parameter("max_wheel_accel_rad_s2", 25.0)
        self.declare_parameter("accel_limit_mode", "per_wheel")
        self.declare_parameter("motor_direction_1", float(MOTOR_DIRECTION[1]))
        self.declare_parameter("motor_direction_2", float(MOTOR_DIRECTION[2]))
        self.declare_parameter("motor_direction_3", float(MOTOR_DIRECTION[3]))
        self.declare_parameter("motor_direction_4", float(MOTOR_DIRECTION[4]))
        self.declare_motion_coeff_parameters()

        self.last_wheel_speeds = {motor_id: 0.0 for motor_id in WHEEL_ANGLES}
        self.last_speed_time = time.monotonic()
        self.last_command_time = 0.0
        self.command_seen = False
        self.timeout_stop_sent = False
        
        # 订阅高层指令
        self.subscription = self.create_subscription(
            Float32MultiArray,
            "local_driving",
            self.driving_callback,
            10
        )
        
        # 发布电机控制指令
        self.motor_publisher = self.create_publisher(
            Float32MultiArray,
            "damiao_control",
            10
        )

        watchdog_hz = max(float(self.get_parameter("watchdog_hz").value), 1.0)
        self.watchdog_timer = self.create_timer(1.0 / watchdog_hz, self.watchdog_callback)
        
        self.get_logger().info("Local Navigation Node initialized")
        self.get_logger().info(
            f"Wheel base radius: {self.get_parameter('wheel_base_radius_m').value * 1000:.2f} mm"
        )
        self.get_logger().info(
            f"Omniwheel radius: {self.get_parameter('omniwheel_radius_m').value * 1000:.2f} mm"
        )
        self.get_logger().info(
            f"Lateral axis sign: {self.get_parameter('lateral_axis_sign').value}"
        )
        self.get_logger().info(
            f"Rotation axis sign: {self.get_parameter('rotation_axis_sign').value}"
        )
        self.get_logger().info(
            f"Max wheel speed: {self.get_parameter('max_wheel_speed_rad_s').value} rad/s"
        )
        self.get_logger().info(
            f"Max wheel accel: {self.get_parameter('max_wheel_accel_rad_s2').value} rad/s^2"
        )
        self.get_logger().info(
            f"Accel limit mode: {self.get_parameter('accel_limit_mode').value}"
        )
        self.get_logger().info(f"Motor control mode: {DEFAULT_MOTOR_MODE} (VEL)")
        self.get_logger().info(f"Command timeout: {self.get_parameter('command_timeout_sec').value}s")

    def declare_motion_coeff_parameters(self):
        """Declare per-motor motion basis coefficients for hardware calibration."""
        for motor_id in WHEEL_ANGLES:
            self.declare_parameter(
                f"forward_coeff_{motor_id}", float(FORWARD_COEFF[motor_id])
            )
            self.declare_parameter(
                f"lateral_coeff_{motor_id}", float(LATERAL_COEFF[motor_id])
            )
            self.declare_parameter(
                f"rotation_coeff_{motor_id}", float(ROTATION_COEFF[motor_id])
            )
    
    def driving_callback(self, msg):
        """
        处理运动指令并转换为轮速
        
        输入: [direction_rad, plane_speed_cm/s, rotation_rad/s]
        输出: 4 个电机的速度指令
        """
        if len(msg.data) < 3:
            self.get_logger().warn(f"Invalid driving command: expected 3 values, got {len(msg.data)}")
            return

        self.last_command_time = time.monotonic()
        self.command_seen = True
        self.timeout_stop_sent = False
        
        direction_rad = msg.data[0]
        plane_speed_cm = msg.data[1]
        rotation_rad = msg.data[2]
        
        # 转换 cm/s → m/s
        plane_speed_m = plane_speed_cm / 100.0
        
        # 计算各轮速度
        wheel_speeds = self.inverse_kinematics(
            direction_rad,
            plane_speed_m,
            rotation_rad
        )
        wheel_speeds = self.apply_output_limits(wheel_speeds)
        
        # 发布电机指令
        for motor_id, speed in wheel_speeds.items():
            self.publish_motor_command(motor_id, speed)
        
        self.get_logger().debug(
            f"Driving cmd: dir={np.rad2deg(direction_rad):.1f}°, "
            f"v={plane_speed_cm:.1f}cm/s, ω={rotation_rad:.2f}rad/s"
        )

    def watchdog_callback(self):
        """
        /local_driving 输入看门狗。

        如果上游桥接节点停止发布，底盘不能继续保持上一条速度命令。
        超时后这里会给 1-4 号轮子各发布一次 0 rad/s，底层 damiao_node
        还有独立电机级 watchdog 作为最后防线。
        """
        if not self.command_seen:
            return

        timeout_sec = float(self.get_parameter("command_timeout_sec").value)
        if time.monotonic() - self.last_command_time <= timeout_sec:
            return

        if not self.timeout_stop_sent:
            self.publish_all_stop(use_accel_limit=False)
            self.timeout_stop_sent = True
            self.get_logger().warn(
                f"No /local_driving for {timeout_sec:.2f}s; sent zero speed to base motors"
            )
    
    def inverse_kinematics(self, direction_rad, plane_speed_m, rotation_rad):
        """
        4 轮全向底盘逆运动学
        
        参数:
            direction_rad: 运动方向（弧度）
            plane_speed_m: 平移速度（m/s）
            rotation_rad: 旋转角速度（rad/s）
        
        返回:
            dict: {motor_id: speed_rad/s}
        
        运动学公式 (X 型布局):
            v_wheel_i = v_x * sin(θ_i) + v_y * cos(θ_i) + ω * R
        
        其中:
            v_x = plane_speed * cos(direction)
            v_y = plane_speed * sin(direction)
            θ_i = 轮子 i 的安装角度
            R = 轮心到中心的距离
        """
        # 检查是否为停止指令
        # 不再发送 disable，而是继续计算零速度让电机保持使能状态
        # if plane_speed_m == 0.0 and rotation_rad == 0.0:
        #     self.get_logger().debug("Zero velocity command")
        #     # 不 return，继续计算（会得到全零速度）
        
        # 分解平移速度到机体坐标系
        # direction_rad: 0 = 前方, π/2 = 右方, π = 后方, -π/2 = 左方
        v_forward = plane_speed_m * np.cos(direction_rad)
        v_lateral = plane_speed_m * np.sin(direction_rad)
        lateral_axis_sign = float(self.get_parameter("lateral_axis_sign").value)
        rotation_axis_sign = float(self.get_parameter("rotation_axis_sign").value)
        wheel_base_radius = float(self.get_parameter("wheel_base_radius_m").value)
        omniwheel_radius = float(self.get_parameter("omniwheel_radius_m").value)
        
        wheel_speeds = {}
        
        for motor_id in WHEEL_ANGLES:
            # 当前底盘使用实机校准矩阵，而不是直接套 45° 理想公式。
            # 这样 forward / lateral / rotation 三个基底可以独立调试：
            # - forward 已由实机确认正常
            # - lateral 使用与旋转不同的对角轮组合，避免横推变成原地旋转
            # - rotation 使用实机观察到的同侧轮组合
            v_translation = (
                v_forward * self.motion_coeff("forward", motor_id)
                + lateral_axis_sign * v_lateral * self.motion_coeff("lateral", motor_id)
            )
            v_rotation = (
                rotation_axis_sign
                * rotation_rad
                * wheel_base_radius
                * self.motion_coeff("rotation", motor_id)
            )
            
            # 轮子线速度 (m/s)
            v_wheel = v_translation + v_rotation
            
            # 达妙 VEL 模式需要电机角速度。这里按轮子直驱换算:
            # rad/s = wheel linear speed (m/s) / wheel radius (m)
            wheel_speeds[motor_id] = v_wheel / omniwheel_radius
        
        return wheel_speeds

    def apply_output_limits(self, wheel_speeds):
        """
        Apply wheel-speed and acceleration limits before publishing motor commands.

        Diagonal and combined translate+rotate commands can produce a larger wheel
        command than pure forward/sideways motion. Speed limiting still scales all
        wheels together. Acceleration limiting is selectable: ``per_wheel`` keeps a
        speed ramp without the shared vector alpha, while ``vector`` preserves the
        complete four-wheel command ratio during the ramp.
        """
        max_speed = abs(float(self.get_parameter("max_wheel_speed_rad_s").value))
        if max_speed > 0.0:
            peak = max(abs(speed) for speed in wheel_speeds.values())
            if peak > max_speed:
                scale = max_speed / peak
                wheel_speeds = {
                    motor_id: speed * scale for motor_id, speed in wheel_speeds.items()
                }
                self.get_logger().debug(
                    f"Wheel speeds scaled by {scale:.2f} to max {max_speed:.2f} rad/s"
                )

        max_accel = abs(float(self.get_parameter("max_wheel_accel_rad_s2").value))
        if max_accel <= 0.0:
            self.last_wheel_speeds = dict(wheel_speeds)
            self.last_speed_time = time.monotonic()
            return wheel_speeds

        now = time.monotonic()
        dt = max(now - self.last_speed_time, 1e-3)
        max_delta = max_accel * dt
        accel_mode = str(self.get_parameter("accel_limit_mode").value).strip().lower()
        if accel_mode == "vector":
            limited, alpha = self.limit_wheel_vector_delta(
                self.last_wheel_speeds,
                wheel_speeds,
                max_delta,
            )
            if alpha < 1.0:
                self.get_logger().debug(
                    f"Wheel vector acceleration scaled by {alpha:.3f}; "
                    f"max delta {max_delta:.3f} rad/s"
                )
        elif accel_mode == "per_wheel":
            limited = self.limit_wheel_independent_delta(
                self.last_wheel_speeds,
                wheel_speeds,
                max_delta,
            )
        else:
            self.get_logger().warn(
                f"Unknown accel_limit_mode '{accel_mode}', using per_wheel",
                throttle_duration_sec=2.0,
            )
            limited = self.limit_wheel_independent_delta(
                self.last_wheel_speeds,
                wheel_speeds,
                max_delta,
            )

        self.last_wheel_speeds = dict(limited)
        self.last_speed_time = now
        return limited

    @staticmethod
    def limit_wheel_vector_delta(current_speeds, target_speeds, max_delta):
        """Move the complete wheel vector toward target with one shared scale.

        A shared alpha keeps the command inside the chassis kinematic subspace.
        Independent per-wheel clipping can alter the intended translation/rotation
        mix and create transient yaw during acceleration at arbitrary directions.
        """
        deltas = {
            motor_id: target - current_speeds.get(motor_id, 0.0)
            for motor_id, target in target_speeds.items()
        }
        peak_delta = max((abs(delta) for delta in deltas.values()), default=0.0)
        if max_delta <= 0.0 or peak_delta <= max_delta:
            alpha = 1.0
        else:
            alpha = max_delta / peak_delta

        limited = {
            motor_id: current_speeds.get(motor_id, 0.0) + alpha * delta
            for motor_id, delta in deltas.items()
        }
        return limited, alpha

    @staticmethod
    def limit_wheel_independent_delta(current_speeds, target_speeds, max_delta):
        """Clamp each wheel speed change independently by max_delta.

        This keeps the speed ramp active while disabling the shared vector alpha.
        It is useful for comparing real chassis behavior against the vector limiter
        without removing acceleration limiting entirely.
        """
        if max_delta <= 0.0:
            return {
                motor_id: current_speeds.get(motor_id, 0.0)
                for motor_id in target_speeds
            }

        limited = {}
        for motor_id, target in target_speeds.items():
            current = current_speeds.get(motor_id, 0.0)
            delta = target - current
            if delta > max_delta:
                delta = max_delta
            elif delta < -max_delta:
                delta = -max_delta
            limited[motor_id] = current + delta
        return limited

    def motor_direction(self, motor_id):
        """
        读取单个电机方向参数。

        返回值只允许 1 或 -1。这样实机发现某个电机方向相反时，可以通过
        ROS 参数临时修正，而不需要复制一份新的底盘控制代码。
        """
        value = float(self.get_parameter(f"motor_direction_{motor_id}").value)
        return 1.0 if value >= 0.0 else -1.0

    def motion_coeff(self, axis, motor_id):
        """
        读取某个运动基底在单个电机上的系数，并叠加电机方向参数。

        axis 只能是 forward / lateral / rotation。系数本身描述底盘运动
        基底，motor_direction_* 负责处理电机接线或安装方向差异。
        """
        coeff = float(self.get_parameter(f"{axis}_coeff_{motor_id}").value)
        return coeff * self.motor_direction(motor_id)
    
    def publish_motor_command(self, motor_id, speed_rad):
        """
        发布单个电机的控制指令
        
        参数:
            motor_id: 电机编号 (1-4)
            speed_rad: 速度 (rad/s)
        """
        msg = Float32MultiArray()
        msg.data = [
            float(motor_id),
            float(DEFAULT_MOTOR_MODE),
            float(speed_rad),
            float(DEFAULT_DURATION)
        ]
        
        if motor_id == 4:
            self.get_logger().debug(f"Publishing M4: {msg.data}")
        
        self.motor_publisher.publish(msg)

    def publish_all_stop(self, use_accel_limit=True):
        """向底盘 4 个轮子发布零速度命令。"""
        speeds = {motor_id: 0.0 for motor_id in WHEEL_ANGLES}
        if use_accel_limit:
            speeds = self.apply_output_limits(speeds)
        else:
            self.last_wheel_speeds = dict(speeds)
            self.last_speed_time = time.monotonic()
        for motor_id in WHEEL_ANGLES:
            self.publish_motor_command(motor_id, speeds[motor_id])


def main(args=None):
    rclpy.init(args=args)
    node = LocalNavigationNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            try:
                node.publish_all_stop()
            except Exception:
                pass
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
