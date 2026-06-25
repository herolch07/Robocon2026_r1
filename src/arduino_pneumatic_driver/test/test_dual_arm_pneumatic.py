"""Tests for the five-relay staff pneumatic command layout."""

from arduino_pneumatic_driver.pneumatic_gripper_joystick_bridge_node import (
    DEFAULT_ARM_SAFE_STATE,
    PneumaticGripperJoystickBridgeNode,
)


def test_arm_safe_state_matches_relays_two_to_five():
    assert DEFAULT_ARM_SAFE_STATE == [1, 0, 1, 0]


def test_motor7_uses_first_gripper_channel():
    assert PneumaticGripperJoystickBridgeNode.selected_gripper_index(7) == 0


def test_motor8_uses_third_gripper_channel():
    assert PneumaticGripperJoystickBridgeNode.selected_gripper_index(8) == 2


def test_selected_inclination_indices():
    assert PneumaticGripperJoystickBridgeNode.selected_inclination_index(7) == 3
    assert PneumaticGripperJoystickBridgeNode.selected_inclination_index(8) == 1


def test_toggle_changes_once_per_press():
    toggle = PneumaticGripperJoystickBridgeNode.apply_toggle
    state, previous = toggle(1, True, False)
    assert (state, previous) == (0, True)
    state, previous = toggle(state, True, previous)
    assert (state, previous) == (0, True)


def test_l3_r3_inclination_indices_remain_available():
    assert PneumaticGripperJoystickBridgeNode.selected_inclination_index(7) == 3
    assert PneumaticGripperJoystickBridgeNode.selected_inclination_index(8) == 1


def test_view_down_swaps_staff_pneumatic_buttons():
    buttons = PneumaticGripperJoystickBridgeNode.maybe_swap_button_pairs(
        motor7_gripper=True,
        motor8_gripper=False,
        motor7_inclination=True,
        motor8_inclination=False,
        swap_enabled=True,
        view_orientation=2,
    )

    assert buttons == {
        "motor7_gripper": False,
        "motor8_gripper": True,
        "motor7_inclination": False,
        "motor8_inclination": True,
    }


def test_view_up_keeps_staff_pneumatic_buttons_normal():
    buttons = PneumaticGripperJoystickBridgeNode.maybe_swap_button_pairs(
        motor7_gripper=True,
        motor8_gripper=False,
        motor7_inclination=True,
        motor8_inclination=False,
        swap_enabled=True,
        view_orientation=0,
    )

    assert buttons == {
        "motor7_gripper": True,
        "motor8_gripper": False,
        "motor7_inclination": True,
        "motor8_inclination": False,
    }
