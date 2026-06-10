#!/usr/bin/env python3
"""
ROS2 three-relay Arduino Mega driver for the KFS staff gripper panel.

This node is designed for the Arduino sketch that accepts serial commands in the
exact format "[1,0,1]". Because the staff gripper shares the same Arduino Mega
panel as the existing pneumatic arm system, this node aggregates both command
sources and opens the serial port only once.
"""

import os
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, String

try:
    import serial
except ImportError:  # pragma: no cover - reported clearly at runtime on robot
    serial = None


DEFAULT_SAFE_STATE = [0, 0, 0]  # arm LOW + arm OPEN + KFS CLOSE


class KfsStaffGripperArduinoNode(Node):
    """
    Aggregate arm pneumatic and KFS staff gripper relay commands.

    Subscribes:
      /pneumatic_gripper_cmd: Int32MultiArray, default mapped to relay 1-2
      /kfs_staff_gripper_cmd: Int32MultiArray, default mapped to relay 3

    Publishes:
      /kfs_staff_gripper_status: String status and Arduino serial feedback

    Output to Arduino:
      [relay1,relay2,relay3]\n, where each value is 0 or 1.
    """

    def __init__(self):
        super().__init__("kfs_staff_gripper_arduino_node")

        self.declare_parameter(
            "serial_port",
            "/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0",
        )
        self.declare_parameter("baud_rate", 9600)
        self.declare_parameter("serial_timeout_sec", 0.1)
        self.declare_parameter("command_timeout_sec", 0.5)
        self.declare_parameter("watchdog_hz", 20.0)
        self.declare_parameter("reconnect_sec", 1.0)
        self.declare_parameter("safe_state", DEFAULT_SAFE_STATE)
        self.declare_parameter("arm_relay_indices", [0, 1])
        self.declare_parameter("staff_relay_indices", [2])
        self.declare_parameter("arm_cmd_topic", "/pneumatic_gripper_cmd")
        self.declare_parameter("staff_cmd_topic", "/kfs_staff_gripper_cmd")

        self.serial_handle = None
        self.connected = False
        self.last_reconnect_attempt = 0.0
        self.last_serial_state = None
        self.current_state = self.get_safe_state()

        self.last_arm_command_time = None
        self.last_staff_command_time = None
        self.arm_timeout_safe_sent = False
        self.staff_timeout_safe_sent = False

        arm_topic = str(self.get_parameter("arm_cmd_topic").value)
        staff_topic = str(self.get_parameter("staff_cmd_topic").value)
        self.arm_cmd_sub = self.create_subscription(
            Int32MultiArray, arm_topic, self.arm_command_callback, 10
        )
        self.staff_cmd_sub = self.create_subscription(
            Int32MultiArray, staff_topic, self.staff_command_callback, 10
        )
        self.status_pub = self.create_publisher(String, "/kfs_staff_gripper_status", 10)

        watchdog_hz = max(float(self.get_parameter("watchdog_hz").value), 1.0)
        self.watchdog_timer = self.create_timer(1.0 / watchdog_hz, self.watchdog_callback)
        self.reader_timer = self.create_timer(0.05, self.read_serial_lines)

        self.connect_serial()
        self.send_state(self.current_state, reason="startup_safe_state", force=True)
        self.get_logger().info("KFS staff gripper Arduino node initialized")
        self.get_logger().info(f"Arm pneumatic topic: {arm_topic}")
        self.get_logger().info(f"KFS staff topic: {staff_topic}")

    def get_safe_state(self):
        """Return a three-relay safe state, clamped to 0/1 values."""
        raw = list(self.get_parameter("safe_state").value)
        safe = [0, 0, 0]
        for index, value in enumerate(raw[:3]):
            safe[index] = 1 if int(value) else 0
        return safe

    def get_indices(self, parameter_name):
        """Load relay indices and keep only valid Arduino relay positions."""
        return [
            int(index)
            for index in list(self.get_parameter(parameter_name).value)
            if 0 <= int(index) < 3
        ]

    def connect_serial(self):
        """Open the Arduino serial port and publish connection status."""
        if serial is None:
            self.publish_status("ERROR pyserial_not_available")
            self.get_logger().error("pyserial is not available")
            return

        configured_port = str(self.get_parameter("serial_port").value)
        port = self.resolve_serial_port(configured_port)
        baud_rate = int(self.get_parameter("baud_rate").value)
        timeout = float(self.get_parameter("serial_timeout_sec").value)

        if port is None:
            self.connected = False
            self.serial_handle = None
            self.publish_status(f"DISCONNECTED no_arduino_serial_port configured={configured_port}")
            self.get_logger().warn(
                "No Arduino serial port found. Close Arduino IDE Serial Monitor "
                "and check /dev/serial/by-id/."
            )
            return

        try:
            self.serial_handle = serial.Serial(port, baud_rate, timeout=timeout)
            # Arduino Mega resets when USB serial opens, so wait before sending.
            time.sleep(2.0)
            self.connected = True
            self.publish_status(f"CONNECTED {port}")
            self.get_logger().info(f"Connected KFS staff gripper Arduino at {port}")
        except Exception as exc:
            self.connected = False
            self.serial_handle = None
            self.publish_status(f"DISCONNECTED {port} {exc}")
            self.get_logger().warn(f"Failed to open Arduino serial port {port}: {exc}")

    def resolve_serial_port(self, configured_port):
        """Return configured port if valid, otherwise auto-detect Arduino by-id."""
        if configured_port and os.path.exists(configured_port):
            return configured_port

        by_id_dir = "/dev/serial/by-id"
        try:
            entries = sorted(os.listdir(by_id_dir))
        except FileNotFoundError:
            return None

        # Prefer Arduino/CH340 USB serial adapters and avoid the Damiao USB-CAN.
        preferred_keywords = ("Arduino", "arduino", "1a86", "CH340", "ch340")
        excluded_keywords = ("HDSC", "CDC_Device_00000000050C")
        for entry in entries:
            if any(keyword in entry for keyword in excluded_keywords):
                continue
            if any(keyword in entry for keyword in preferred_keywords):
                return os.path.realpath(os.path.join(by_id_dir, entry))
        return None

    def arm_command_callback(self, msg):
        """Update relay 1-2 from the existing arm pneumatic command topic."""
        self.apply_partial_command(
            msg.data,
            self.get_indices("arm_relay_indices"),
            source="arm_pneumatic",
        )
        self.last_arm_command_time = time.monotonic()
        self.arm_timeout_safe_sent = False

    def staff_command_callback(self, msg):
        """Update relay 3 from the KFS staff gripper command topic."""
        self.apply_partial_command(
            msg.data,
            self.get_indices("staff_relay_indices"),
            source="kfs_staff",
        )
        self.last_staff_command_time = time.monotonic()
        self.staff_timeout_safe_sent = False

    def apply_partial_command(self, data, indices, source):
        """Merge a shorter command into the three-relay Arduino state."""
        if len(data) < len(indices):
            self.get_logger().warn(
                f"Invalid {source} command: expected {len(indices)} values, got {len(data)}"
            )
            return

        state = list(self.current_state)
        for src_index, relay_index in enumerate(indices):
            state[relay_index] = 1 if int(data[src_index]) else 0
        self.send_state(state, reason=source)

    def send_state(self, state, reason, force=False):
        """Send the three-relay state using the Arduino sketch list protocol."""
        self.current_state = [1 if int(value) else 0 for value in state[:3]]
        if not force and self.last_serial_state == self.current_state:
            return

        if not self.connected or self.serial_handle is None:
            self.publish_status(f"NOT_CONNECTED {reason} state={self.current_state}")
            return

        line = "[" + ",".join(str(value) for value in self.current_state) + "]\n"
        try:
            self.serial_handle.write(line.encode("ascii"))
            self.serial_handle.flush()
            self.last_serial_state = list(self.current_state)
            self.publish_status(f"SENT {reason} {line.strip()}")
        except Exception as exc:
            self.connected = False
            self.publish_status(f"WRITE_ERROR {exc}")
            self.get_logger().error(f"Failed to write KFS staff gripper command: {exc}")

    def read_serial_lines(self):
        """Read Arduino feedback lines without blocking the ROS executor."""
        if not self.connected or self.serial_handle is None:
            return
        try:
            while self.serial_handle.in_waiting > 0:
                line = self.serial_handle.readline().decode("utf-8", errors="replace").strip()
                if line:
                    self.publish_status(f"ARDUINO {line}")
        except Exception as exc:
            self.connected = False
            self.publish_status(f"READ_ERROR {exc}")
            self.get_logger().error(f"Failed to read Arduino serial feedback: {exc}")

    def watchdog_callback(self):
        """Reconnect serial and fail safe each command source independently."""
        now = time.monotonic()
        if not self.connected and now - self.last_reconnect_attempt > float(
            self.get_parameter("reconnect_sec").value
        ):
            self.last_reconnect_attempt = now
            self.connect_serial()
            if self.connected:
                self.send_state(self.get_safe_state(), reason="reconnect_safe_state", force=True)

        self.check_source_timeout(
            source="arm_pneumatic",
            last_time=self.last_arm_command_time,
            indices=self.get_indices("arm_relay_indices"),
            timeout_flag="arm_timeout_safe_sent",
        )
        self.check_source_timeout(
            source="kfs_staff",
            last_time=self.last_staff_command_time,
            indices=self.get_indices("staff_relay_indices"),
            timeout_flag="staff_timeout_safe_sent",
        )

    def check_source_timeout(self, source, last_time, indices, timeout_flag):
        """Apply safe values only to the relay group owned by one topic."""
        if last_time is None or getattr(self, timeout_flag):
            return

        timeout_sec = float(self.get_parameter("command_timeout_sec").value)
        if time.monotonic() - last_time <= timeout_sec:
            return

        safe_state = self.get_safe_state()
        state = list(self.current_state)
        for relay_index in indices:
            state[relay_index] = safe_state[relay_index]
        self.send_state(state, reason=f"{source}_timeout_safe_state", force=True)
        setattr(self, timeout_flag, True)
        self.get_logger().warn(
            f"No {source} command for {timeout_sec:.2f}s; "
            f"sent safe values for relay indices {indices}"
        )

    def publish_status(self, text):
        """Publish a human-readable status string for monitoring."""
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)

    def destroy_node(self):
        """Send safe state and close serial during shutdown."""
        try:
            if rclpy.ok():
                self.send_state(self.get_safe_state(), reason="shutdown_safe_state", force=True)
        except Exception:
            pass
        try:
            if self.serial_handle is not None:
                self.serial_handle.close()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = KfsStaffGripperArduinoNode()
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
