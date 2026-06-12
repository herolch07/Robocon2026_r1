"""No-hardware tests for shared Motor 7/8 position control calculations."""

import pytest

from r1_arm_control.motor7_position_controller_node import (
    Motor7PositionControllerNode,
)
from r1_arm_control.motor8_position_controller_node import (
    Motor8PositionControllerNode,
)
from r1_arm_control.motor_position_selector_joystick_bridge_node import (
    MotorPositionSelectorJoystickBridgeNode,
)


def test_x_rising_edge_only_triggers_once_while_held():
    edge, held = MotorPositionSelectorJoystickBridgeNode.rising_edge(True, False)
    assert edge is True
    edge, held = MotorPositionSelectorJoystickBridgeNode.rising_edge(True, held)
    assert edge is False
    edge, _ = MotorPositionSelectorJoystickBridgeNode.rising_edge(False, held)
    assert edge is False


def test_l2_r2_trim_depth_and_cancellation():
    trim = MotorPositionSelectorJoystickBridgeNode.trigger_trim
    assert trim(512, 0, 24) == pytest.approx(-1.0)
    assert trim(0, 512, 24) == pytest.approx(1.0)
    assert trim(512, 512, 24) == pytest.approx(0.0)
    assert trim(10, 10, 24) == pytest.approx(0.0)


def test_start_switch_requires_shared_controls_released():
    neutral = MotorPositionSelectorJoystickBridgeNode.controls_are_neutral
    assert neutral(False, 0, 0, 24) is True
    assert neutral(True, 0, 0, 24) is False
    assert neutral(False, 24, 0, 24) is False
    assert neutral(False, 0, 24, 24) is False


def test_selector_toggles_motor_7_and_8():
    next_id = MotorPositionSelectorJoystickBridgeNode.next_motor_id
    assert next_id(7) == 8
    assert next_id(8) == 7


def test_x_cycles_three_positions():
    assert Motor8PositionControllerNode.next_position_index(0) == 1
    assert Motor8PositionControllerNode.next_position_index(1) == 2
    assert Motor8PositionControllerNode.next_position_index(2) == 0


def test_trim_integration_obeys_soft_limits():
    assert Motor8PositionControllerNode.integrate_trim(
        34.0, 1.0, 2.0, 1.0, -35.0, 35.0
    ) == pytest.approx(35.0)
    assert Motor8PositionControllerNode.integrate_trim(
        -34.0, -1.0, 2.0, 1.0, -35.0, 35.0
    ) == pytest.approx(-35.0)


def test_motor7_reuses_motor8_controller_implementation():
    assert issubclass(Motor7PositionControllerNode, Motor8PositionControllerNode)
