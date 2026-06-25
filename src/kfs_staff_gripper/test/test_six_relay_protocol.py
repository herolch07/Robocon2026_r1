"""Tests for the confirmed five-relay Arduino protocol."""

import pytest

from kfs_staff_gripper.kfs_staff_gripper_arduino_node import (
    DEFAULT_SAFE_STATE,
    format_relay_command,
    normalize_relay_state,
)


def test_confirmed_five_relay_safe_state():
    assert DEFAULT_SAFE_STATE == [0, 1, 0, 1, 0]


def test_serial_line_has_exact_arduino_format():
    assert format_relay_command(DEFAULT_SAFE_STATE) == "[0,1,0,1,0]\n"

def test_protocol_rejects_old_three_relay_state():
    with pytest.raises(ValueError):
        normalize_relay_state([0, 0, 0])


def test_protocol_rejects_old_seven_relay_state():
    with pytest.raises(ValueError):
        normalize_relay_state([0, 0, 1, 0, 1, 1, 0])


def test_protocol_clamps_values_to_binary():
    assert normalize_relay_state([0, 2, -1, 7, 0]) == [0, 1, 1, 1, 0]
