"""Tests for KFS-gripper-based operator-frame direction conversion."""

import math

import pytest

from joystick_bridge.joystick_bridge import (
    JoystickBridge,
    VIEW_BACK,
    VIEW_FRONT,
    VIEW_LEFT,
    VIEW_RIGHT,
)


def test_dpad_selects_absolute_kfs_gripper_direction():
    map_view = JoystickBridge.orientation_from_dpad
    assert map_view(0, -512, VIEW_LEFT, 15) == VIEW_FRONT
    assert map_view(512, 0, VIEW_FRONT, 15) == VIEW_RIGHT
    assert map_view(0, 512, VIEW_FRONT, 15) == VIEW_BACK
    assert map_view(-512, 0, VIEW_FRONT, 15) == VIEW_LEFT


def test_dpad_neutral_and_diagonal_keep_current_view():
    map_view = JoystickBridge.orientation_from_dpad
    assert map_view(0, 0, VIEW_LEFT, 15) == VIEW_LEFT
    assert map_view(512, -512, VIEW_BACK, 15) == VIEW_BACK


@pytest.mark.parametrize(
    ("view", "expected_body_direction"),
    [
        (VIEW_FRONT, math.pi / 2.0),
        (VIEW_RIGHT, 0.0),
        (VIEW_BACK, -math.pi / 2.0),
        (VIEW_LEFT, math.pi),
    ],
)
def test_operator_forward_converts_to_expected_body_direction(
    view, expected_body_direction
):
    actual = JoystickBridge.operator_to_body_direction(0.0, view)
    assert math.cos(actual) == pytest.approx(math.cos(expected_body_direction))
    assert math.sin(actual) == pytest.approx(math.sin(expected_body_direction))


def test_operator_direction_rotation_preserves_magnitude_independent_angle():
    operator_right = math.pi / 2.0
    actual = JoystickBridge.operator_to_body_direction(operator_right, VIEW_LEFT)
    assert math.cos(actual) == pytest.approx(math.cos(-math.pi / 2.0))
    assert math.sin(actual) == pytest.approx(math.sin(-math.pi / 2.0))
