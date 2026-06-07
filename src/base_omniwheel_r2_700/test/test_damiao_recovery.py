"""No-hardware tests for damiao_node E-stop recovery gating."""

import time
from types import SimpleNamespace

from base_omniwheel_r2_700.damiao_node import (
    MotorControllerNode,
    STATE_READY,
    STATE_RECOVERING,
    STATE_WAIT_NEUTRAL,
)


class FakeMotorControl:
    def __init__(self):
        self.calls = []

    def switchControlMode(self, motor, mode):
        self.calls.append(("mode", int(mode)))

    def enable(self, motor):
        self.calls.append(("enable", motor.SlaveID))

    def control_Vel(self, motor, speed):
        self.calls.append(("vel", float(speed)))


def make_node(state, enabled=True, age=0.0):
    node = object.__new__(MotorControllerNode)
    motor = SimpleNamespace(
        SlaveID=1,
        isEnable=enabled,
        last_feedback_time=time.monotonic() - age,
    )
    node.is_connected = True
    node.motor_control = FakeMotorControl()
    node.motors = {1: motor}
    node.motor_states = {1: state}
    node.recovery_attempts = {1: 0}
    node.last_recovery_time = {1: 0.0}
    node.neutral_received = {1: False}
    node.watchdog_stopped = {1: True}
    node.motor_timers = {}
    node.last_velocity_command_time = {}
    node.latest_commands = {}
    node.get_parameter = lambda name: SimpleNamespace(
        value={
            "feedback_timeout_sec": 0.5,
            "recovery_retry_sec": 2.0,
            "neutral_speed_threshold_rad_s": 0.02,
        }[name]
    )
    node.get_logger = lambda: SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warn=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        debug=lambda *args, **kwargs: None,
    )
    return node, motor


def command(speed):
    return SimpleNamespace(data=[1.0, 3.0, float(speed), 0.0])


def test_nonzero_is_blocked_until_neutral_after_recovery():
    node, _ = make_node(STATE_WAIT_NEUTRAL)

    node.control_callback(command(1.0))
    assert node.motor_states[1] == STATE_WAIT_NEUTRAL
    assert node.motor_control.calls[-1] == ("vel", 0.0)

    node.control_callback(command(0.0))
    assert node.motor_states[1] == STATE_READY

    node.control_callback(command(1.0))
    assert node.motor_control.calls[-1] == ("vel", 1.0)


def test_feedback_timeout_sends_mode_enable_zero_recovery_sequence():
    node, _ = make_node(STATE_READY, enabled=False, age=1.0)

    node._recovery_watchdog()

    assert node.motor_states[1] == STATE_RECOVERING
    assert node.motor_control.calls == [
        ("mode", 3),
        ("enable", 1),
        ("vel", 0.0),
    ]
