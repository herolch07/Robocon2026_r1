import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import Float32MultiArray
from base_omniwheel_r2_700.DM_CAN import *
import serial
import os
import time
import threading

# 配置参数
DEVICE_ID = "usb-HDSC_CDC_Device_00000000050C-if00"
DEFAULT_MOTOR_IDS = [1, 2, 3, 4, 5, 6, 7]
DEFAULT_CONTROL_MODE = Control_Type.VEL  # 默认使用速度模式
RECONNECT_INTERVAL = 2.0  # 重连尝试间隔（秒）
RECONNECT_MAX_ATTEMPTS = 5  # 最大重连尝试次数，0 表示无限重试
REENABLE_MIN_INTERVAL = 1.0  # 不在每条速度命令里反复阻塞使能

def find_device_port(device_id):
    by_id_dir = "/dev/serial/by-id/"
    try:
        for entry in os.listdir(by_id_dir):
            if device_id in entry:
                return os.path.realpath(os.path.join(by_id_dir, entry))
    except FileNotFoundError:
        pass
    return None

class MotorControllerNode(Node):
    def __init__(self):
        super().__init__("motor_controller_node")
        self.declare_parameter("motor_ids", DEFAULT_MOTOR_IDS)
        self.declare_parameter("command_timeout_sec", 0.5)
        self.declare_parameter("watchdog_hz", 20.0)
        
        # 连接状态标志
        self.is_connected = False
        self.reconnect_attempts = 0
        
        # 电机计时器字典 {motor_id: timer}
        self.motor_timers = {}
        self.last_reenable_time = {}
        self.last_velocity_command_time = {}
        self.watchdog_stopped = {}
        
        # 初始化硬件连接
        if not self._init_hardware():
            self.get_logger().error("Failed to initialize hardware. Will retry in background.")
        
        # 创建定时器用于检测和重连
        self.reconnect_timer = self.create_timer(RECONNECT_INTERVAL, self._check_connection)
        
        # 创建定时器用于周期性读取电机反馈（关键！）
        self.recv_timer = self.create_timer(0.01, self._recv_feedback)  # 100Hz 读取反馈

        watchdog_hz = max(float(self.get_parameter("watchdog_hz").value), 1.0)
        self.command_watchdog_timer = self.create_timer(1.0 / watchdog_hz, self._command_watchdog)
        
        # 订阅控制话题
        self.subscription = self.create_subscription(
            Float32MultiArray, "damiao_control", self.control_callback, 10
        )

    def _init_hardware(self):
        """初始化硬件连接和电机"""
        try:
            # 1. 串口自动发现
            port = find_device_port(DEVICE_ID)
            if not port:
                self.get_logger().warn(f"Device {DEVICE_ID} not found in /dev/serial/by-id/!")
                return False
                
            self.get_logger().info(f"Found device at {port}")
            
            # 2. 打开串口
            try:
                if hasattr(self, 'ser') and self.ser.is_open:
                    self.ser.close()
                self.ser = serial.Serial(port, 921600, timeout=0.01)
            except serial.SerialException as e:
                self.get_logger().error(f"Failed to open serial port: {e}")
                return False
            
            # 3. 创建电机控制器
            self.motor_control = MotorControl(self.ser)

            # 4. 初始化电机 (支持多个电机 ID)
            self.motors = {}
            motor_ids = [
                int(motor_id)
                for motor_id in self.get_parameter("motor_ids").get_parameter_value().integer_array_value
            ]
            self.get_logger().info(f"Configured motor IDs: {motor_ids}")
            for motor_id in motor_ids:
                motor = Motor(DM_Motor_Type.DMH3510, motor_id, 0x00)
                self.motors[motor_id] = motor
                self.motor_control.addMotor(motor)

            # 5. 显式初始化序列 (为所有电机执行)
            self.get_logger().info(f"Executing hardware initialization for all motors in {DEFAULT_CONTROL_MODE.name} mode...")
            for motor_id, motor in self.motors.items():
                try:
                    # A. 切换到指定模式
                    self.motor_control.switchControlMode(motor, DEFAULT_CONTROL_MODE)
                    # B. 设置当前位置为零位
                    self.motor_control.set_zero_position(motor)
                    # C. 显式使能
                    self.motor_control.enable(motor)
                    self.get_logger().info(f"Motor {motor_id} INITIALIZED and ENABLED in {DEFAULT_CONTROL_MODE.name} mode.")
                except Exception as e:
                    self.get_logger().error(f"Failed to initialize motor {motor_id}: {e}")
                    return False
            
            self.is_connected = True
            self.reconnect_attempts = 0
            self.get_logger().info("Hardware initialization completed successfully.")
            return True
            
        except Exception as e:
            self.get_logger().error(f"Hardware initialization failed: {e}")
            return False

    def _recv_feedback(self):
        """周期性读取电机反馈数据并更新状态"""
        if self.is_connected and hasattr(self, 'motor_control'):
            try:
                self.motor_control.recv()
            except Exception as e:
                self.get_logger().debug(f"Recv feedback error: {e}")
    
    def _check_connection(self):
        """定时检查连接状态，断线时尝试重连"""
        if self.is_connected:
            # 检查串口是否仍然可用
            try:
                if not hasattr(self, 'ser') or not self.ser.is_open:
                    self.get_logger().warn("Serial port is closed. Attempting reconnection...")
                    self.is_connected = False
            except Exception as e:
                self.get_logger().warn(f"Connection check failed: {e}. Attempting reconnection...")
                self.is_connected = False
        
        # 如果未连接，尝试重连
        if not self.is_connected:
            if RECONNECT_MAX_ATTEMPTS > 0 and self.reconnect_attempts >= RECONNECT_MAX_ATTEMPTS:
                self.get_logger().error(f"Max reconnection attempts ({RECONNECT_MAX_ATTEMPTS}) reached. Giving up.")
                self.reconnect_timer.cancel()
                return
            
            self.reconnect_attempts += 1
            self.get_logger().info(f"Reconnection attempt {self.reconnect_attempts}...")
            
            if self._init_hardware():
                self.get_logger().info("Reconnection successful!")
            else:
                self.get_logger().warn(f"Reconnection failed. Will retry in {RECONNECT_INTERVAL}s...")

    def control_callback(self, msg):
        """
        消息协议: [motor_id, mode, speed, param4]
        - motor_id: 电机 ID
        - mode: 控制模式
          - 0: 失能
          - 2: POS_VEL 模式，param4 = position (位置，弧度)
          - 3: VEL 模式，param4 = time (持续时间，秒)
        - speed: 速度 (rad/s)
        - param4: 根据模式不同含义不同
        """
        if len(msg.data) < 4:
            self.get_logger().warn(f"Invalid damiao_control command: expected 4 values, got {len(msg.data)}")
            return

        if not self.is_connected:
            self.get_logger().warn("Not connected to hardware. Ignoring command.")
            return
        
        motor_id = int(msg.data[0])
        mode = int(msg.data[1])
        speed = float(msg.data[2])
        param4 = float(msg.data[3])
        
        if motor_id == 4:
            self.get_logger().debug(f"M4 received: mode={mode}, speed={speed}, param4={param4}")

        if motor_id in self.motors:
            motor = self.motors[motor_id]
            try:
                if mode == 0:
                    self.motor_control.disable(motor)
                    self.last_velocity_command_time.pop(motor_id, None)
                    self.watchdog_stopped[motor_id] = True
                    self.get_logger().info(f"Motor {motor_id} disabled")
                elif mode == 2:
                    # POS_VEL 模式: param4 = position
                    position = param4
                    self.ensure_motor_enabled(motor, motor_id)
                    self.motor_control.control_Pos_Vel(motor, position, speed)
                    self.get_logger().debug(f"Motor {motor_id}: pos={position}, vel={speed}")
                elif mode == 3:
                    # VEL 模式: param4 = time (持续时间)
                    duration = param4
                    self.ensure_motor_enabled(motor, motor_id)
                    self.motor_control.control_Vel(motor, speed)
                    self.get_logger().debug(f"Motor {motor_id}: vel={speed}, duration={duration}s")

                    # duration=0 表示连续速度命令，必须由 watchdog 兜底。
                    # 上游如果停止刷新该电机命令，本节点会在 command_timeout_sec 后归零。
                    if duration <= 0:
                        self.last_velocity_command_time[motor_id] = time.monotonic()
                        self.watchdog_stopped[motor_id] = abs(speed) < 1e-6
                    
                    # 如果 duration > 0，使用 threading.Timer 实现一次性停止
                    if duration > 0:
                        # 取消该电机之前的计时器（如果存在）
                        if motor_id in self.motor_timers:
                            self.motor_timers[motor_id].cancel()
                        
                        # 创建一次性计时器
                        timer = threading.Timer(duration, self._auto_stop_motor, args=[motor, motor_id])
                        timer.start()
                        self.motor_timers[motor_id] = timer
                        self.get_logger().info(f"Motor {motor_id} will auto-stop after {duration}s")
            except serial.SerialException as e:
                self.get_logger().error(f"Serial communication error: {e}")
                self.is_connected = False
            except Exception as e:
                self.get_logger().error(f"Motor control error: {e}")
        else:
            self.get_logger().warn(f"Motor {motor_id} not initialized")

    def ensure_motor_enabled(self, motor, motor_id):
        """Re-enable at a throttled rate so feedback glitches do not stall control."""
        if motor.isEnable:
            return

        now = time.monotonic()
        last_time = self.last_reenable_time.get(motor_id, 0.0)
        if now - last_time < REENABLE_MIN_INTERVAL:
            self.get_logger().debug(
                f"Motor {motor_id} feedback reports disabled; skipping repeated enable"
            )
            return

        self.last_reenable_time[motor_id] = now
        self.motor_control.enable(motor)
        self.get_logger().warn(f"Motor {motor_id} re-enabled (feedback isEnable={motor.isEnable})")
    
    def _auto_stop_motor(self, motor, motor_id):
        """自动停止电机（duration 结束后调用）- 由 threading.Timer 触发"""
        try:
            # 发送停止命令
            self.motor_control.control_Vel(motor, 0.0)
            self.last_velocity_command_time.pop(motor_id, None)
            self.watchdog_stopped[motor_id] = True
            self.get_logger().info(f"Motor {motor_id} auto-stopped (duration elapsed)")
            
            # 清除计时器引用
            if motor_id in self.motor_timers:
                del self.motor_timers[motor_id]
        except Exception as e:
            self.get_logger().error(f"Failed to auto-stop motor {motor_id}: {e}")

    def _command_watchdog(self):
        """
        电机级连续速度命令看门狗。

        对 duration=0 的 VEL 命令，如果超过 command_timeout_sec 没有收到新的刷新，
        立即向对应电机发送 0 rad/s。这个逻辑是最后一道安全防线，覆盖上游 node 崩溃、
        topic 中断或手动发布一次连续速度后忘记停止的情况。
        """
        if not self.is_connected or not hasattr(self, "motor_control"):
            return

        timeout_sec = float(self.get_parameter("command_timeout_sec").value)
        now = time.monotonic()

        for motor_id, last_time in list(self.last_velocity_command_time.items()):
            if now - last_time <= timeout_sec:
                continue
            if self.watchdog_stopped.get(motor_id, False):
                continue
            motor = self.motors.get(motor_id)
            if motor is None:
                continue
            try:
                self.motor_control.control_Vel(motor, 0.0)
                self.watchdog_stopped[motor_id] = True
                self.get_logger().warn(
                    f"Motor {motor_id} command timeout after {timeout_sec:.2f}s; sent 0 rad/s"
                )
            except serial.SerialException as e:
                self.get_logger().error(f"Serial communication error in command watchdog: {e}")
                self.is_connected = False
            except Exception as e:
                self.get_logger().error(f"Command watchdog failed for motor {motor_id}: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = MotorControllerNode()
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
