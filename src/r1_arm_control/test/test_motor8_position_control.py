"""No-hardware tests for Motor 8 two-position control calculations."""

import pytest

from r1_arm_control.motor8_position_controller_node import (
    Motor8PositionControllerNode,
)
from r1_arm_control.motor8_position_joystick_bridge_node import (
    Motor8PositionJoystickBridgeNode,
)


def test_x_rising_edge_only_triggers_once_while_held():
    edge, held = Motor8PositionJoystickBridgeNode.rising_edge(True, False)
    assert edge is True
    edge, held = Motor8PositionJoystickBridgeNode.rising_edge(True, held)
    assert edge is False
    edge, held = Motor8PositionJoystickBridgeNode.rising_edge(False, held)
    assert edge is False


def test_l3_r3_trim_buttons_cancel():
    assert Motor8PositionJoystickBridgeNode.signed_button_input(True, False) == -1.0
    assert Motor8PositionJoystickBridgeNode.signed_button_input(False, True) == 1.0
    assert Motor8PositionJoystickBridgeNode.signed_button_input(True, True) == 0.0


def test_x_toggles_between_two_positions():
    assert Motor8PositionControllerNode.next_position_index(0) == 1
    assert Motor8PositionControllerNode.next_position_index(1) == 0


def test_trim_integration_obeys_soft_limits():
    assert Motor8PositionControllerNode.integrate_trim(
        0.49, 1.0, 0.1, 1.0, -0.5, 0.5
    ) == pytest.approx(0.5)
    assert Motor8PositionControllerNode.integrate_trim(
        -0.49, -1.0, 0.1, 1.0, -0.5, 0.5
    ) == pytest.approx(-0.5)
