"""No-hardware tests for the KFS staff gripper Y-button toggle."""

from kfs_staff_gripper.kfs_staff_gripper_joystick_bridge_node import (
    KfsStaffGripperJoystickBridgeNode,
)


def test_y_changes_once_per_press():
    """Y toggles once and a held button does not toggle repeatedly."""
    apply_toggle = KfsStaffGripperJoystickBridgeNode.apply_staff_toggle

    state, previous = apply_toggle(0, True, False)
    assert state == 1

    state, previous = apply_toggle(state, True, previous)
    assert state == 1

    state, previous = apply_toggle(state, False, previous)
    state, previous = apply_toggle(state, True, previous)
    assert state == 0


def test_held_y_after_timeout_requires_release():
    """A held Y cannot reopen the KFS gripper after timeout closes it."""
    state, previous = KfsStaffGripperJoystickBridgeNode.apply_staff_toggle(
        0, True, True
    )

    assert state == 0
    assert previous is True
