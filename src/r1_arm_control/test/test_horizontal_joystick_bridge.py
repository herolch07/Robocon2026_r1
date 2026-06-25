"""Tests for Motor 6 L3/R3 horizontal control."""

from r1_arm_control.horizontal_joystick_bridge_node import (
    HorizontalJoystickBridgeNode,
)


def test_r3_commands_negative_fixed_speed():
    assert HorizontalJoystickBridgeNode.speed_from_buttons(False, True, 10.0) == -10.0


def test_l3_commands_positive_fixed_speed():
    assert HorizontalJoystickBridgeNode.speed_from_buttons(True, False, 10.0) == 10.0


def test_both_or_neither_button_stops():
    speed = HorizontalJoystickBridgeNode.speed_from_buttons
    assert speed(False, False, 10.0) == 0.0
    assert speed(True, True, 10.0) == 0.0


def test_negative_parameter_is_normalized_to_positive_magnitude():
    assert HorizontalJoystickBridgeNode.speed_from_buttons(False, True, -10.0) == -10.0


def test_l2_r2_trigger_speed_for_kfs_horizontal():
    speed = HorizontalJoystickBridgeNode.speed_from_triggers
    assert speed(512, 0, 10.0, 24) == 10.0
    assert speed(0, 512, 10.0, 24) == -10.0
    assert speed(512, 512, 10.0, 24) == 0.0
    assert speed(10, 10, 10.0, 24) == 0.0
