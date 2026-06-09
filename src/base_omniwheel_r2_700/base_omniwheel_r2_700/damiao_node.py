"""ROS 2 Damiao motor driver with watchdog and E-stop power recovery.

The node serves Motor 1-7 through one USB-CAN adapter. It blocks non-zero
commands while feedback is missing or a motor is disabled, retries VEL-mode
initialization at a low rate, and requires a neutral command before motion is
unlocked after recovery.
"""

import os
import threading
import time

import rclpy
import serial
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

from base_omniwheel_r2_700.DM_CAN import (
    Control_Type,
    DM_Motor_Type,
    Motor,
    MotorControl,
)


DEVICE_ID = "usb-HDSC_CDC_Device_00000000050C-if00"
DEFAULT_MOTOR_IDS = [1, 2, 3, 4, 5, 6, 7]
DEFAULT_CONTROL_MODE = Control_Type.VEL
RECONNECT_INTERVAL = 2.0
RECONNECT_MAX_ATTEMPTS = 0  # 0 means retry forever at a low rate.

STATE_RECOVERING = 0
STATE_WAIT_NEUTRAL = 1
STATE_READY = 2
STATE_DISABLED = 3
STATE_NAMES = {
    STATE_RECOVERING: "RECOVERING",
    STATE_WAIT_NEUTRAL: "WAIT_NEUTRAL",
    STATE_READY: "READY",
    STATE_DISABLED: "DISABLED",
}


def find_device_port(device_id):
    """Return the stable serial path for the configured USB-CAN adapter."""
    by_id_dir = "/dev/serial/by-id/"
    try:
        for entry in os.listdir(by_id_dir):
            if device_id in entry:
                return os.path.realpath(os.path.join(by_id_dir, entry))
    except FileNotFoundError:
        pass
    return None


class MotorControllerNode(Node):
    """Drive Damiao motors and recover safely after motor power interruption.

    A motor is allowed to receive a non-zero command only after fresh feedback
    confirms that it is enabled and a zero-speed command has been observed.
    This prevents an E-stop release from immediately replaying a held command.
    """

    def __init__(self):
        super().__init__("motor_controller_node")
        self.declare_parameter("motor_ids", DEFAULT_MOTOR_IDS)
        self.declare_parameter("command_timeout_sec", 0.5)
        self.declare_parameter("watchdog_hz", 20.0)
        self.declare_parameter("feedback_timeout_sec", 0.5)
        self.declare_parameter("recovery_retry_sec", 2.0)
        self.declare_parameter("neutral_speed_threshold_rad_s", 0.02)
        self.declare_parameter("status_hz", 5.0)

        self.is_connected = False
        self.reconnect_attempts = 0
        self.motor_timers = {}
        self.last_velocity_command_time = {}
        self.watchdog_stopped = {}
        self.latest_commands = {}
        self.motor_states = {}
        self.recovery_attempts = {}
        self.last_recovery_time = {}
        self.neutral_received = {}

        if not self._init_hardware():
            self.get_logger().error(
                "Failed to initialize hardware. Will retry in background."
            )

        self.reconnect_timer = self.create_timer(
            RECONNECT_INTERVAL, self._check_connection
        )
        self.recv_timer = self.create_timer(0.01, self._recv_feedback)
        self.recovery_timer = self.create_timer(0.05, self._recovery_watchdog)

        watchdog_hz = max(float(self.get_parameter("watchdog_hz").value), 1.0)
        self.command_watchdog_timer = self.create_timer(
            1.0 / watchdog_hz, self._command_watchdog
        )

        status_hz = max(float(self.get_parameter("status_hz").value), 1.0)
        self.status_timer = self.create_timer(1.0 / status_hz, self._publish_status)
        self.status_pub = self.create_publisher(
            Float32MultiArray, "/damiao_motor_status", 10
        )
        self.subscription = self.create_subscription(
            Float32MultiArray, "/damiao_control", self.control_callback, 10
        )

    def _configured_motor_ids(self):
        return [
            int(motor_id)
            for motor_id in self.get_parameter("motor_ids")
            .get_parameter_value()
            .integer_array_value
        ]

    def _reset_motor_runtime_state(self, motor_ids):
        """Reset recovery state while preserving the latest upstream commands."""
        now = time.monotonic()
        self.motor_states = {
            motor_id: STATE_RECOVERING for motor_id in motor_ids
        }
        self.recovery_attempts = {motor_id: 0 for motor_id in motor_ids}
        self.last_recovery_time = {motor_id: now for motor_id in motor_ids}
        self.neutral_received = {motor_id: False for motor_id in motor_ids}
        self.last_velocity_command_time.clear()
        self.watchdog_stopped = {motor_id: True for motor_id in motor_ids}

    def _init_hardware(self):
        """Open the serial adapter and send initial safe setup commands."""
        try:
            port = find_device_port(DEVICE_ID)
            if not port:
                self.get_logger().warn(
                    f"Device {DEVICE_ID} not found in /dev/serial/by-id/!"
                )
                return False

            self.get_logger().info(f"Found device at {port}")
            try:
                if hasattr(self, "ser") and self.ser.is_open:
                    self.ser.close()
                self.ser = serial.Serial(port, 921600, timeout=0.01)
            except serial.SerialException as exc:
                if getattr(exc, "errno", None) == 13 or "Permission denied" in str(exc):
                    self.get_logger().error(
                        f"Permission denied opening {port}. Add user "
                        f"{os.getenv('USER', '<user>')} to the dialout group, "
                        "then log out and back in: "
                        f"sudo usermod -aG dialout {os.getenv('USER', '<user>')}"
                    )
                else:
                    self.get_logger().error(f"Failed to open serial port: {exc}")
                return False

            self.motor_control = MotorControl(self.ser)
            self.motors = {}
            motor_ids = self._configured_motor_ids()
            self.get_logger().info(f"Configured motor IDs: {motor_ids}")
            self._reset_motor_runtime_state(motor_ids)

            for motor_id in motor_ids:
                motor = Motor(DM_Motor_Type.DMS3519, motor_id, 0x00)
                self.motors[motor_id] = motor
                self.motor_control.addMotor(motor)

            self.get_logger().info(
                "Sending initial VEL mode, zero-position, enable, and zero-speed "
                "commands; waiting for feedback confirmation."
            )
            for motor_id, motor in self.motors.items():
                try:
                    self.motor_control.switchControlMode(
                        motor, DEFAULT_CONTROL_MODE
                    )
                    self.motor_control.set_zero_position(motor)
                    self.motor_control.enable(motor)
                    self.motor_control.control_Vel(motor, 0.0)
                    self.recovery_attempts[motor_id] = 1
                    self.last_recovery_time[motor_id] = time.monotonic()
                    self.get_logger().info(
                        f"Motor {motor_id} initialization commands sent; "
                        "waiting for enabled feedback."
                    )
                except Exception as exc:
                    self.get_logger().error(
                        f"Failed to initialize motor {motor_id}: {exc}"
                    )
                    return False

            self.is_connected = True
            self.reconnect_attempts = 0
            self.get_logger().info(
                "Serial initialization completed; motor motion remains locked "
                "until feedback and neutral checks pass."
            )
            return True
        except Exception as exc:
            self.get_logger().error(f"Hardware initialization failed: {exc}")
            return False

    def _recv_feedback(self):
        """Read feedback and advance motors toward the neutral interlock."""
        if not self.is_connected or not hasattr(self, "motor_control"):
            return
        try:
            self.motor_control.recv()
            for motor_id, motor in self.motors.items():
                if (
                    self.motor_states.get(motor_id) == STATE_RECOVERING
                    and self._feedback_is_fresh(motor)
                    and motor.isEnable
                ):
                    self.motor_states[motor_id] = STATE_WAIT_NEUTRAL
                    self.neutral_received[motor_id] = False
                    self.get_logger().warn(
                        f"Motor {motor_id} enabled feedback confirmed; "
                        "waiting for a zero-speed command before motion is allowed."
                    )
        except serial.SerialException as exc:
            self.get_logger().error(f"Feedback serial error: {exc}")
            self.is_connected = False
        except Exception as exc:
            self.get_logger().debug(f"Recv feedback error: {exc}")

    def _feedback_age(self, motor):
        if motor.last_feedback_time is None:
            return float("inf")
        return max(0.0, time.monotonic() - motor.last_feedback_time)

    def _feedback_is_fresh(self, motor):
        timeout = max(
            float(self.get_parameter("feedback_timeout_sec").value), 0.05
        )
        return self._feedback_age(motor) <= timeout

    def _enter_recovery(self, motor_id, reason):
        if self.motor_states.get(motor_id) != STATE_RECOVERING:
            self.get_logger().error(
                f"Motor {motor_id} entered RECOVERING: {reason}; "
                "non-zero commands are blocked."
            )
        self.motor_states[motor_id] = STATE_RECOVERING
        self.neutral_received[motor_id] = False
        self.watchdog_stopped[motor_id] = True
        timer = self.motor_timers.pop(motor_id, None)
        if timer is not None:
            timer.cancel()

    def _recovery_watchdog(self):
        """Recover one motor per cycle so seven motors do not block together."""
        if not self.is_connected or not hasattr(self, "motor_control"):
            return

        now = time.monotonic()
        retry_sec = max(
            float(self.get_parameter("recovery_retry_sec").value), 0.5
        )

        for motor_id, motor in self.motors.items():
            state = self.motor_states.get(motor_id, STATE_RECOVERING)
            fresh = self._feedback_is_fresh(motor)

            if state in (STATE_READY, STATE_WAIT_NEUTRAL):
                if not fresh:
                    self._enter_recovery(motor_id, "motor feedback timed out")
                    state = STATE_RECOVERING
                elif not motor.isEnable:
                    self._enter_recovery(motor_id, "feedback reports disabled")
                    state = STATE_RECOVERING

            if state != STATE_RECOVERING:
                continue

            if fresh and motor.isEnable:
                self.motor_states[motor_id] = STATE_WAIT_NEUTRAL
                self.neutral_received[motor_id] = False
                self.get_logger().warn(
                    f"Motor {motor_id} enabled feedback confirmed; "
                    "waiting for neutral."
                )
                continue

            if now - self.last_recovery_time.get(motor_id, 0.0) < retry_sec:
                continue

            self.last_recovery_time[motor_id] = now
            self.recovery_attempts[motor_id] = (
                self.recovery_attempts.get(motor_id, 0) + 1
            )
            try:
                self.motor_control.switchControlMode(
                    motor, DEFAULT_CONTROL_MODE
                )
                self.motor_control.enable(motor)
                self.motor_control.control_Vel(motor, 0.0)
                self.get_logger().warn(
                    f"Motor {motor_id} recovery attempt "
                    f"{self.recovery_attempts[motor_id]} sent: VEL + enable + zero; "
                    "waiting for feedback."
                )
            except serial.SerialException as exc:
                self.get_logger().error(
                    f"Motor {motor_id} recovery serial error: {exc}"
                )
                self.is_connected = False
            except Exception as exc:
                self.get_logger().error(
                    f"Motor {motor_id} recovery attempt failed: {exc}"
                )
            return

    def _check_connection(self):
        """Reconnect the USB serial adapter indefinitely at a low rate."""
        if self.is_connected:
            try:
                if not hasattr(self, "ser") or not self.ser.is_open:
                    self.get_logger().warn(
                        "Serial port is closed. Attempting reconnection..."
                    )
                    self.is_connected = False
            except Exception as exc:
                self.get_logger().warn(
                    f"Connection check failed: {exc}. Attempting reconnection..."
                )
                self.is_connected = False

        if self.is_connected:
            return
        if (
            RECONNECT_MAX_ATTEMPTS > 0
            and self.reconnect_attempts >= RECONNECT_MAX_ATTEMPTS
        ):
            self.get_logger().error(
                f"Max reconnection attempts ({RECONNECT_MAX_ATTEMPTS}) reached."
            )
            return

        self.reconnect_attempts += 1
        self.get_logger().info(
            f"Reconnection attempt {self.reconnect_attempts}..."
        )
        if self._init_hardware():
            self.get_logger().info("Reconnection successful!")
        else:
            self.get_logger().warn(
                f"Reconnection failed. Will retry in {RECONNECT_INTERVAL}s..."
            )

    def control_callback(self, msg):
        """Handle [motor_id, mode, speed, position_or_duration]."""
        if len(msg.data) < 4:
            self.get_logger().warn(
                "Invalid /damiao_control command: expected 4 values, "
                f"got {len(msg.data)}"
            )
            return
        if not self.is_connected:
            self.get_logger().warn(
                "Not connected to hardware. Ignoring command.",
                throttle_duration_sec=2.0,
            )
            return

        motor_id = int(msg.data[0])
        mode = int(msg.data[1])
        speed = float(msg.data[2])
        param4 = float(msg.data[3])
        motor = self.motors.get(motor_id)
        if motor is None:
            self.get_logger().warn(f"Motor {motor_id} not initialized")
            return

        try:
            if mode == 0:
                self.motor_control.disable(motor)
                self.motor_states[motor_id] = STATE_DISABLED
                self.neutral_received[motor_id] = False
                self.last_velocity_command_time.pop(motor_id, None)
                self.watchdog_stopped[motor_id] = True
                self.get_logger().info(f"Motor {motor_id} disabled")
                return
            if mode not in (2, 3):
                self.get_logger().warn(
                    f"Unsupported motor mode {mode} for Motor {motor_id}"
                )
                return

            self.latest_commands[motor_id] = (mode, speed, param4, time.monotonic())
            state = self.motor_states.get(motor_id, STATE_RECOVERING)
            if state == STATE_DISABLED:
                self._enter_recovery(motor_id, "new control command after disable")
                state = STATE_RECOVERING

            if state == STATE_READY and (
                not self._feedback_is_fresh(motor) or not motor.isEnable
            ):
                self._enter_recovery(motor_id, "feedback lost before command")
                state = STATE_RECOVERING

            neutral_threshold = max(
                float(
                    self.get_parameter(
                        "neutral_speed_threshold_rad_s"
                    ).value
                ),
                0.0,
            )
            if (
                state == STATE_WAIT_NEUTRAL
                and self._feedback_is_fresh(motor)
                and motor.isEnable
                and abs(speed) <= neutral_threshold
            ):
                self.neutral_received[motor_id] = True
                self.motor_states[motor_id] = STATE_READY
                state = STATE_READY
                self.get_logger().info(
                    f"Motor {motor_id} neutral confirmed; motion unlocked."
                )

            if state != STATE_READY:
                self._send_safe_zero(motor, motor_id)
                return

            if mode == 2:
                self.motor_control.control_Pos_Vel(motor, param4, speed)
            else:
                self.motor_control.control_Vel(motor, speed)
                if param4 <= 0:
                    self.last_velocity_command_time[motor_id] = time.monotonic()
                    self.watchdog_stopped[motor_id] = abs(speed) < 1e-6
                else:
                    previous_timer = self.motor_timers.pop(motor_id, None)
                    if previous_timer is not None:
                        previous_timer.cancel()
                    timer = threading.Timer(
                        param4,
                        self._auto_stop_motor,
                        args=[motor, motor_id],
                    )
                    timer.start()
                    self.motor_timers[motor_id] = timer
        except serial.SerialException as exc:
            self.get_logger().error(f"Serial communication error: {exc}")
            self.is_connected = False
        except Exception as exc:
            self.get_logger().error(f"Motor control error: {exc}")

    def _send_safe_zero(self, motor, motor_id):
        """Send zero only; never replay a blocked non-zero command."""
        self.motor_control.control_Vel(motor, 0.0)
        self.watchdog_stopped[motor_id] = True

    def _auto_stop_motor(self, motor, motor_id):
        try:
            self.motor_control.control_Vel(motor, 0.0)
            self.last_velocity_command_time.pop(motor_id, None)
            self.watchdog_stopped[motor_id] = True
            self.get_logger().info(
                f"Motor {motor_id} auto-stopped (duration elapsed)"
            )
            self.motor_timers.pop(motor_id, None)
        except Exception as exc:
            self.get_logger().error(
                f"Failed to auto-stop motor {motor_id}: {exc}"
            )

    def _command_watchdog(self):
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
                    f"Motor {motor_id} command timeout after "
                    f"{timeout_sec:.2f}s; sent 0 rad/s"
                )
            except serial.SerialException as exc:
                self.get_logger().error(
                    f"Serial communication error in command watchdog: {exc}"
                )
                self.is_connected = False
            except Exception as exc:
                self.get_logger().error(
                    f"Command watchdog failed for motor {motor_id}: {exc}"
                )

    def _publish_status(self):
        """Publish one status message per motor for simple ros2 topic echo."""
        if not hasattr(self, "motors"):
            return
        for motor_id, motor in self.motors.items():
            age = self._feedback_age(motor)
            msg = Float32MultiArray()
            msg.data = [
                float(motor_id),
                float(self.motor_states.get(motor_id, STATE_RECOVERING)),
                1.0 if self._feedback_is_fresh(motor) else 0.0,
                1.0 if motor.isEnable else 0.0,
                -1.0 if age == float("inf") else float(age),
                float(self.recovery_attempts.get(motor_id, 0)),
                1.0 if self.neutral_received.get(motor_id, False) else 0.0,
                float(motor.error_code),
                (
                    -1.0
                    if motor.mos_temperature_c is None
                    else float(motor.mos_temperature_c)
                ),
                (
                    -1.0
                    if motor.rotor_temperature_c is None
                    else float(motor.rotor_temperature_c)
                ),
            ]
            self.status_pub.publish(msg)

    def destroy_node(self):
        for timer in self.motor_timers.values():
            timer.cancel()
        if self.is_connected and hasattr(self, "motor_control"):
            for motor in getattr(self, "motors", {}).values():
                try:
                    self.motor_control.control_Vel(motor, 0.0)
                except Exception:
                    pass
        super().destroy_node()


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


if __name__ == "__main__":
    main()
