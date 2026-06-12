"""No-hardware tests for damiao_node E-stop recovery gating."""

import time
from types import SimpleNamespace

from base_omniwheel_r2_700.DM_CAN import Control_Type
from base_omniwheel_r2_700.damiao_node import (
    MotorControllerNode,
    STATE_READY,
    STATE_RECOVERING,
    STATE_WAIT_NEUTRAL,
)


class FakeParameter:
    def __init__(self, value):
        self.value = value

    def get_parameter_value(self):
        return SimpleNamespace(integer_array_value=list(self.value))


class FakeMotorControl:
    def __init__(self):
        self.calls = []

    def switchControlMode(self, motor, mode):
        self.calls.append(("mode", int(mode)))
        motor.NowControlMode = mode

    def enable(self, motor):
        self.calls.append(("enable", motor.SlaveID))

    def control_Vel(self, motor, speed):
        self.calls.append(("vel", float(speed)))

    def control_Pos_Vel(self, motor, position, speed):
        self.calls.append(("pos_vel", float(position), float(speed)))


def make_node(state, motor_id=1, enabled=True, age=0.0, position=0.0):
    node = object.__new__(MotorControllerNode)
    motor = SimpleNamespace(
        SlaveID=motor_id,
        isEnable=enabled,
        last_feedback_time=time.monotonic() - age,
        state_q=position,
        state_dq=0.0,
        state_tau=0.0,
        NowControlMode=(
            Control_Type.POS_VEL if motor_id in (7, 8) else Control_Type.VEL
        ),
    )
    node.is_connected = True
    node.motor_control = FakeMotorControl()
    node.motors = {motor_id: motor}
    node.motor_states = {motor_id: state}
    node.recovery_attempts = {motor_id: 0}
    node.last_recovery_time = {motor_id: 0.0}
    node.neutral_received = {motor_id: False}
    node.watchdog_stopped = {motor_id: True}
    node.position_watchdog_held = {motor_id: True}
    node.motor_timers = {}
    node.last_velocity_command_time = {}
    node.last_position_command_time = {}
    node.latest_commands = {}
    values = {
        "feedback_timeout_sec": 0.5,
        "recovery_retry_sec": 2.0,
        "neutral_speed_threshold_rad_s": 0.02,
        "neutral_position_tolerance_rad": 0.05,
        "position_hold_speed_rad_s": 0.1,
        "position_mode_motor_ids": [7, 8],
    }
    node.get_parameter = lambda name: FakeParameter(values[name])
    node.get_logger = lambda: SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warn=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        debug=lambda *args, **kwargs: None,
    )
    return node, motor


def velocity_command(speed):
    return SimpleNamespace(data=[1.0, 3.0, float(speed), 0.0])


def position_command(motor_id, position, speed=0.3):
    return SimpleNamespace(
        data=[float(motor_id), 2.0, float(speed), float(position)]
    )


def test_nonzero_velocity_is_blocked_until_neutral_after_recovery():
    node, _ = make_node(STATE_WAIT_NEUTRAL)

    node.control_callback(velocity_command(1.0))
    assert node.motor_states[1] == STATE_WAIT_NEUTRAL
    assert node.motor_control.calls[-1] == ("vel", 0.0)

    node.control_callback(velocity_command(0.0))
    assert node.motor_states[1] == STATE_READY

    node.control_callback(velocity_command(1.0))
    assert node.motor_control.calls[-1] == ("vel", 1.0)


def test_velocity_feedback_timeout_restores_vel_mode_and_zero():
    node, _ = make_node(STATE_READY, enabled=False, age=1.0)

    node._recovery_watchdog()

    assert node.motor_states[1] == STATE_RECOVERING
    assert node.motor_control.calls == [
        ("mode", 3),
        ("enable", 1),
        ("vel", 0.0),
    ]


def test_motor8_uses_position_mode_and_neutral_current_position():
    node, _ = make_node(
        STATE_WAIT_NEUTRAL, motor_id=8, position=0.2
    )

    node.control_callback(position_command(8, 0.5))
    assert node.motor_states[8] == STATE_WAIT_NEUTRAL
    assert node.motor_control.calls[-1] == ("pos_vel", 0.2, 0.1)

    node.control_callback(position_command(8, 0.2))
    assert node.motor_states[8] == STATE_READY
    assert node.motor_control.calls[-1] == ("pos_vel", 0.2, 0.3)


def test_motor8_recovery_restores_pos_vel_without_old_target():
    node, _ = make_node(
        STATE_READY, motor_id=8, enabled=False, age=1.0, position=0.2
    )

    node._recovery_watchdog()

    assert node.motor_states[8] == STATE_RECOVERING
    assert node.motor_control.calls == [
        ("mode", 2),
        ("enable", 8),
    ]



def test_motor7_uses_position_mode_and_neutral_current_position():
    node, _ = make_node(
        STATE_WAIT_NEUTRAL, motor_id=7, position=-0.3
    )

    node.control_callback(position_command(7, 1.0))
    assert node.motor_states[7] == STATE_WAIT_NEUTRAL
    assert node.motor_control.calls[-1] == ("pos_vel", -0.3, 0.1)

    node.control_callback(position_command(7, -0.3))
    assert node.motor_states[7] == STATE_READY
    assert node.motor_control.calls[-1] == ("pos_vel", -0.3, 0.3)
