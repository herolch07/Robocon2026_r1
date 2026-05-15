#!/usr/bin/env python3
"""
ROS2 USB-serial driver for an Arduino Mega pneumatic relay controller.

This node keeps Arduino-specific serial parsing out of higher-level robot logic.
It accepts a two-channel relay state command and sends the exact list format used
by the tested Arduino sketch, for example "[1,1]\\n" or "[0,0]\\n".
"""

import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray, String

try:
    import serial
except ImportError:  # pragma: no cover - reported at runtime on the robot
    serial = None


class PneumaticRelayDriverNode(Node):
    """
    Bridge ROS2 gripper commands to Arduino Mega relay commands.

    Subscribes:
      /pneumatic_gripper_cmd: Int32MultiArray [relay1_state, relay2_state]
        0 = OPEN, 1 = CLOSE, matching the Arduino sketch.

    Publishes:
      /pneumatic_gripper_status: String with connection and command status.
    """

    def __init__(self):
        super().__init__("pneumatic_relay_driver_node")

        self.declare_parameter(
            "serial_port",
            "/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0",
        )
        self.declare_parameter("baud_rate", 9600)
        self.declare_parameter("serial_timeout_sec", 0.1)
        self.declare_parameter("command_timeout_sec", 0.5)
        self.declare_parameter("watchdog_hz", 20.0)
        self.declare_parameter("reconnect_sec", 1.0)
        self.declare_parameter("safe_state", [1, 0])

        self.serial_handle = None
        self.connected = False
        self.last_command_time = 0.0
        self.command_seen = False
        self.timeout_safe_sent = False
        self.current_state = self.get_safe_state()
        self.last_reconnect_attempt = 0.0

        self.cmd_sub = self.create_subscription(
            Int32MultiArray,
            "/pneumatic_gripper_cmd",
            self.command_callback,
            10,
        )
        self.status_pub = self.create_publisher(String, "/pneumatic_gripper_status", 10)

        watchdog_hz = max(float(self.get_parameter("watchdog_hz").value), 1.0)
        self.watchdog_timer = self.create_timer(1.0 / watchdog_hz, self.watchdog_callback)
        self.reader_timer = self.create_timer(0.05, self.read_serial_lines)

        self.connect_serial()
        self.send_state(self.current_state, reason="startup_safe_state")

    def get_safe_state(self):
        """Return the configured two-relay safe state, clamped to 0/1 values."""
        raw = list(self.get_parameter("safe_state").value)
        if len(raw) < 2:
            return [1, 1]
        return [1 if int(raw[0]) else 0, 1 if int(raw[1]) else 0]

    def connect_serial(self):
        """Open the Arduino serial port if possible, with status logging."""
        if serial is None:
            self.publish_status("ERROR pyserial_not_available")
            self.get_logger().error("pyserial is not available")
            return

        port = str(self.get_parameter("serial_port").value)
        baud_rate = int(self.get_parameter("baud_rate").value)
        timeout = float(self.get_parameter("serial_timeout_sec").value)

        try:
            self.serial_handle = serial.Serial(port, baud_rate, timeout=timeout)
            # Arduino Mega resets after USB serial open. Give it a short boot window.
            time.sleep(2.0)
            self.connected = True
            self.publish_status(f"CONNECTED {port}")
            self.get_logger().info(f"Connected Arduino pneumatic controller at {port}")
        except Exception as exc:
            self.connected = False
            self.serial_handle = None
            self.publish_status(f"DISCONNECTED {port} {exc}")
            self.get_logger().warn(f"Failed to open Arduino serial port {port}: {exc}")

    def command_callback(self, msg):
        """
        Validate and send a two-relay command to Arduino.

        The Arduino sketch accepts any string containing two 0/1 digits, but this
        node sends a strict list string so logs and tests remain predictable.
        """
        if len(msg.data) < 2:
            self.get_logger().warn("Invalid /pneumatic_gripper_cmd: expected [state1, state2]")
            return

        state = [1 if int(msg.data[0]) else 0, 1 if int(msg.data[1]) else 0]
        self.last_command_time = time.monotonic()
        self.command_seen = True
        self.timeout_safe_sent = False
        self.send_state(state, reason="command")

    def send_state(self, state, reason):
        """Send one relay state command to Arduino using the tested list format."""
        self.current_state = state
        if not self.connected or self.serial_handle is None:
            self.publish_status(f"NOT_CONNECTED {reason} state={state}")
            return

        line = f"[{state[0]},{state[1]}]\n"
        try:
            self.serial_handle.write(line.encode("ascii"))
            self.serial_handle.flush()
            self.publish_status(f"SENT {reason} {line.strip()}")
        except Exception as exc:
            self.connected = False
            self.publish_status(f"WRITE_ERROR {exc}")
            self.get_logger().error(f"Failed to write Arduino pneumatic command: {exc}")

    def read_serial_lines(self):
        """Read Arduino status lines without blocking the ROS executor."""
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
            self.get_logger().error(f"Failed to read Arduino pneumatic status: {exc}")

    def watchdog_callback(self):
        """
        Safety watchdog for command loss and serial reconnect.

        If no fresh command arrives within command_timeout_sec, send safe_state.
        The default startup safe state is [1, 0]: gripper closed, height low.
        Higher-level nodes may keep refreshing [1, 1] after the height is raised.
        """
        now = time.monotonic()
        if not self.connected and now - self.last_reconnect_attempt > float(
            self.get_parameter("reconnect_sec").value
        ):
            self.last_reconnect_attempt = now
            self.connect_serial()
            if self.connected:
                self.send_state(self.get_safe_state(), reason="reconnect_safe_state")

        if not self.command_seen:
            return

        timeout_sec = float(self.get_parameter("command_timeout_sec").value)
        if now - self.last_command_time <= timeout_sec:
            return

        if not self.timeout_safe_sent:
            safe_state = self.get_safe_state()
            self.send_state(safe_state, reason="timeout_safe_state")
            self.timeout_safe_sent = True
            self.get_logger().warn(
                f"No pneumatic command for {timeout_sec:.2f}s; sent safe state {safe_state}"
            )

    def publish_status(self, text):
        """Publish a human-readable status string for debugging."""
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)

    def destroy_node(self):
        """Close serial after sending safe state when ROS context is still valid."""
        try:
            if rclpy.ok():
                self.send_state(self.get_safe_state(), reason="shutdown_safe_state")
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
    node = PneumaticRelayDriverNode()
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
