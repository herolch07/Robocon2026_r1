#!/usr/bin/env python3
"""Safe two-position and manual-trim controller for Damiao Motor 8."""

import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class Motor8PositionControllerNode(Node):
    """Convert discrete/trim input into bounded POS_VEL commands.

    The node waits for fresh Motor 8 feedback before publishing. On startup and
    after feedback recovery it first targets the measured position, preventing
    an old preset from being replayed after an E-stop or driver restart.
    """

    STATUS_POSITION_INDEX = 10
    STATUS_VELOCITY_INDEX = 11
    STATUS_MODE_INDEX = 13

    def __init__(self):
        super().__init__("motor8_position_controller_node")

        self.declare_parameter("motor_id", 8)
        self.declare_parameter("position_a_rad", 0.0)
        self.declare_parameter("position_b_rad", 33.0)
        self.declare_parameter("min_position_rad", -35.0)
        self.declare_parameter("max_position_rad", 35.0)
        self.declare_parameter("preset_speed_rad_s", 3.0)
        self.declare_parameter("trim_speed_rad_s", 2.0)
        self.declare_parameter("hold_speed_rad_s", 0.1)
        self.declare_parameter("position_tolerance_rad", 0.03)
        self.declare_parameter("input_timeout_sec", 0.3)
        self.declare_parameter("feedback_timeout_sec", 0.5)
        self.declare_parameter("publish_hz", 20.0)

        self.motor_id = int(self.get_parameter("motor_id").value)
        self.actual_position = 0.0
        self.actual_velocity = 0.0
        self.target_position = 0.0
        self.trim_input = 0.0
        self.selected_position = 0
        self.last_input_time = 0.0
        self.last_feedback_time = 0.0
        self.driver_feedback_fresh = False
        self.feedback_initialized = False
        self.recovery_hold_required = True
        self.input_source_valid = False

        self.input_sub = self.create_subscription(
            Float32MultiArray,
            "/motor8_position_input",
            self.input_callback,
            10,
        )
        self.feedback_sub = self.create_subscription(
            Float32MultiArray,
            "/damiao_motor_status",
            self.feedback_callback,
            10,
        )
        self.motor_pub = self.create_publisher(
            Float32MultiArray, "/damiao_control", 10
        )
        self.status_pub = self.create_publisher(
            Float32MultiArray, "/motor8_position_status", 10
        )

        publish_hz = max(float(self.get_parameter("publish_hz").value), 1.0)
        self.period = 1.0 / publish_hz
        self.timer = self.create_timer(self.period, self.timer_callback)
        self.get_logger().info(
            "Motor 8 POS_VEL experiment initialized; waiting for feedback"
        )

    @staticmethod
    def clamp_position(value, minimum, maximum):
        """Clamp one target to ordered software limits."""
        low, high = sorted((float(minimum), float(maximum)))
        return max(low, min(high, float(value)))

    @staticmethod
    def next_position_index(current):
        """Toggle between position A (0) and position B (1)."""
        return 1 if int(current) == 0 else 0

    @classmethod
    def integrate_trim(cls, target, trim_input, trim_speed, dt, minimum, maximum):
        """Integrate signed joystick input into a bounded position target."""
        updated = float(target) + float(trim_input) * abs(float(trim_speed)) * float(dt)
        return cls.clamp_position(updated, minimum, maximum)

    def input_callback(self, msg):
        """Accept [toggle_event, trim_input, input_valid] from the bridge."""
        if len(msg.data) < 3:
            self.get_logger().warn(
                "Invalid /motor8_position_input: expected [toggle, trim, valid]"
            )
            return
        self.last_input_time = time.monotonic()
        self.input_source_valid = bool(msg.data[2] > 0.5)
        self.trim_input = (
            max(-1.0, min(1.0, float(msg.data[1])))
            if self.input_source_valid
            else 0.0
        )
        if float(msg.data[0]) > 0.5 and self.feedback_initialized:
            self.selected_position = self.next_position_index(
                self.selected_position
            )
            parameter = (
                "position_b_rad"
                if self.selected_position == 1
                else "position_a_rad"
            )
            self.target_position = self.limit_position(
                float(self.get_parameter(parameter).value)
            )

    def feedback_callback(self, msg):
        """Read Motor 8 feedback appended by damiao_node."""
        if len(msg.data) <= self.STATUS_MODE_INDEX:
            return
        if int(msg.data[0]) != self.motor_id:
            return

        feedback_fresh = bool(msg.data[2] > 0.5)
        enabled = bool(msg.data[3] > 0.5)
        ready = int(msg.data[1]) == 2
        position_mode = int(msg.data[self.STATUS_MODE_INDEX]) == 2
        self.driver_feedback_fresh = feedback_fresh and enabled and position_mode
        if not self.driver_feedback_fresh:
            self.recovery_hold_required = True
            return

        self.actual_position = float(msg.data[self.STATUS_POSITION_INDEX])
        self.actual_velocity = float(msg.data[self.STATUS_VELOCITY_INDEX])
        self.last_feedback_time = time.monotonic()

        if not self.feedback_initialized or self.recovery_hold_required or not ready:
            self.target_position = self.limit_position(self.actual_position)
            self.selected_position = 0
            self.trim_input = 0.0
            self.feedback_initialized = True
            self.recovery_hold_required = not ready

    def limit_position(self, value):
        """Apply configured Motor 8 software limits."""
        return self.clamp_position(
            value,
            self.get_parameter("min_position_rad").value,
            self.get_parameter("max_position_rad").value,
        )

    def feedback_valid(self):
        """Return true only while enabled feedback is recent."""
        timeout = max(float(self.get_parameter("feedback_timeout_sec").value), 0.05)
        return (
            self.feedback_initialized
            and self.driver_feedback_fresh
            and time.monotonic() - self.last_feedback_time <= timeout
        )

    def timer_callback(self):
        """Update trim, publish POS_VEL command, and publish diagnostic status."""
        input_timeout = max(float(self.get_parameter("input_timeout_sec").value), 0.0)
        input_timed_out = (
            time.monotonic() - self.last_input_time > input_timeout
            or not self.input_source_valid
        )
        valid = self.feedback_valid()
        if input_timed_out:
            self.trim_input = 0.0
            if valid:
                self.target_position = self.limit_position(self.actual_position)

        if valid:
            if abs(self.trim_input) > 1e-6:
                self.target_position = self.integrate_trim(
                    self.target_position,
                    self.trim_input,
                    self.get_parameter("trim_speed_rad_s").value,
                    self.period,
                    self.get_parameter("min_position_rad").value,
                    self.get_parameter("max_position_rad").value,
                )
                command_speed = abs(
                    float(self.get_parameter("trim_speed_rad_s").value)
                )
            elif self.recovery_hold_required:
                command_speed = abs(
                    float(self.get_parameter("hold_speed_rad_s").value)
                )
            else:
                command_speed = abs(
                    float(self.get_parameter("preset_speed_rad_s").value)
                )

            self.publish_motor_command(command_speed)

        self.publish_status(valid, input_timed_out)

    def publish_motor_command(self, speed):
        """Publish [motor_id, POS_VEL, max_speed, target_position]."""
        msg = Float32MultiArray()
        msg.data = [
            float(self.motor_id),
            2.0,
            max(float(speed), 0.01),
            float(self.target_position),
        ]
        self.motor_pub.publish(msg)

    def publish_status(self, feedback_valid, input_timed_out):
        """Publish target, feedback, state, timeout, and at-target flag."""
        tolerance = max(
            float(self.get_parameter("position_tolerance_rad").value), 0.0
        )
        at_target = feedback_valid and abs(
            self.target_position - self.actual_position
        ) <= tolerance
        msg = Float32MultiArray()
        msg.data = [
            float(self.target_position),
            float(self.actual_position),
            float(self.actual_velocity),
            float(self.selected_position),
            float(self.trim_input),
            1.0 if feedback_valid else 0.0,
            1.0 if input_timed_out else 0.0,
            float(self.motor_id),
            1.0 if at_target else 0.0,
        ]
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = Motor8PositionControllerNode()
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
