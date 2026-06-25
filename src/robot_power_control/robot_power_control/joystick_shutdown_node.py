#!/usr/bin/env python3
"""Joystick long-press shutdown node for robot power management.

The node is intentionally separate from arm, chassis, and joystick driver
packages. It watches a configurable button combination on ``/joystick_data`` and
triggers a configurable shutdown command after a sustained hold. Dry-run mode is
enabled by default so the first real-machine test cannot power off the Pi.
"""

import shlex
import subprocess
import time

import rclpy
from my_joystick_msgs.msg import Joystick
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String


class LongPressShutdownDetector:
    """Track a button combination and report when it has been held long enough."""

    def __init__(self, required_buttons, hold_sec):
        """Store the required button names and hold duration in seconds."""
        self.required_buttons = [str(button) for button in required_buttons]
        self.hold_sec = max(float(hold_sec), 0.0)
        self.hold_start = None
        self.triggered = False

    def update(self, pressed, now):
        """Return true once when all buttons stay pressed for ``hold_sec``."""
        if not pressed:
            self.reset()
            return False

        if self.hold_start is None:
            self.hold_start = float(now)
            self.triggered = False
            return False

        if self.triggered:
            return False

        if float(now) - self.hold_start >= self.hold_sec:
            self.triggered = True
            return True
        return False

    def reset(self):
        """Clear the current hold state after release or input timeout."""
        self.hold_start = None
        self.triggered = False

    def held_duration(self, now):
        """Return the current hold duration for status reporting."""
        if self.hold_start is None:
            return 0.0
        return max(0.0, float(now) - self.hold_start)


class JoystickShutdownNode(Node):
    """Convert a sustained joystick button combination into a shutdown action."""

    def __init__(self):
        super().__init__("joystick_shutdown_node")

        self.declare_parameter("joystick_topic", "/joystick_data")
        self.declare_parameter("status_topic", "/robot_power_status")
        self.declare_parameter("required_buttons", ["x", "y", "b", "a"])
        self.declare_parameter("hold_sec", 5.0)
        self.declare_parameter("input_timeout_sec", 0.5)
        self.declare_parameter("watchdog_hz", 10.0)
        self.declare_parameter("dry_run", True)
        self.declare_parameter("stop_tmux_before_shutdown", False)
        self.declare_parameter("stop_tmux_session", "r1_control")
        self.declare_parameter("shutdown_command", "sudo -n /usr/bin/systemctl poweroff")

        self.required_buttons = self.get_required_buttons()
        self.detector = LongPressShutdownDetector(
            self.required_buttons,
            self.get_parameter("hold_sec").value,
        )
        self.last_input_time = None
        self.last_status = None
        self.shutdown_started = False

        joystick_topic = str(self.get_parameter("joystick_topic").value)
        status_topic = str(self.get_parameter("status_topic").value)
        self.joy_sub = self.create_subscription(
            Joystick,
            joystick_topic,
            self.joystick_callback,
            10,
        )
        self.status_pub = self.create_publisher(String, status_topic, 10)

        watchdog_hz = max(float(self.get_parameter("watchdog_hz").value), 1.0)
        self.watchdog_timer = self.create_timer(1.0 / watchdog_hz, self.watchdog)

        self.publish_status(
            "READY dry_run={} buttons={} hold_sec={:.1f}".format(
                bool(self.get_parameter("dry_run").value),
                "+".join(self.required_buttons),
                float(self.get_parameter("hold_sec").value),
            )
        )

    def get_required_buttons(self):
        """Return a non-empty list of valid Joystick button field names."""
        raw_buttons = list(self.get_parameter("required_buttons").value)
        valid_buttons = []
        invalid_buttons = []
        for button in raw_buttons:
            name = str(button)
            if hasattr(Joystick(), name):
                valid_buttons.append(name)
            else:
                invalid_buttons.append(name)
        if invalid_buttons:
            self.get_logger().warn(f"Ignoring invalid shutdown buttons: {invalid_buttons}")
        if not valid_buttons:
            valid_buttons = ["x", "y", "b", "a"]
            self.get_logger().warn("No valid required_buttons; falling back to X+Y+B+A")
        return valid_buttons

    def joystick_callback(self, msg):
        """Update the long-press detector from one joystick sample."""
        now = time.monotonic()
        self.last_input_time = now
        all_pressed = all(bool(getattr(msg, button)) for button in self.required_buttons)
        if self.detector.update(all_pressed, now):
            self.handle_shutdown_trigger()

    def watchdog(self):
        """Reset long-press state when joystick input stops arriving."""
        if self.last_input_time is None:
            return
        timeout = max(float(self.get_parameter("input_timeout_sec").value), 0.0)
        if time.monotonic() - self.last_input_time > timeout:
            if self.detector.hold_start is not None:
                self.publish_status("RESET input_timeout")
            self.detector.reset()

    def handle_shutdown_trigger(self):
        """Publish status and either dry-run or execute the shutdown sequence."""
        if self.shutdown_started:
            return
        self.shutdown_started = True
        dry_run = bool(self.get_parameter("dry_run").value)
        if dry_run:
            self.publish_status("DRY_RUN shutdown_combo_held")
            self.get_logger().warn("Dry-run shutdown trigger: no poweroff command executed")
            return

        self.publish_status("SHUTDOWN combo_held")
        self.get_logger().warn("Shutdown combo held; executing robot shutdown")
        self.execute_shutdown_sequence()

    def execute_shutdown_sequence(self):
        """Run the shutdown command before any optional tmux cleanup."""
        command = str(self.get_parameter("shutdown_command").value)
        try:
            subprocess.Popen(shlex.split(command))
            self.publish_status(f"SHUTDOWN_COMMAND_STARTED {command}")
        except Exception as exc:
            self.publish_status(f"SHUTDOWN_COMMAND_FAILED {exc}")
            self.get_logger().error(f"Failed to start shutdown command: {exc}")
            return

        if bool(self.get_parameter("stop_tmux_before_shutdown").value):
            session = str(self.get_parameter("stop_tmux_session").value)
            subprocess.run(["tmux", "kill-session", "-t", session], check=False)

    def publish_status(self, text):
        """Publish a human-readable power-control status string."""
        if text == self.last_status:
            return
        self.last_status = text
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)
        self.get_logger().info(text)


def main(args=None):
    """Run the joystick shutdown node."""
    rclpy.init(args=args)
    node = JoystickShutdownNode()
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
