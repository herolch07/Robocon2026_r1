"""No-hardware tests for the arm height single-button toggle."""

from arduino_pneumatic_driver.pneumatic_gripper_joystick_bridge_node import (
    PneumaticGripperJoystickBridgeNode,
)


def test_height_changes_once_per_press():
    """Holding the button must not repeatedly toggle at joystick publish rate."""
    apply_toggle = PneumaticGripperJoystickBridgeNode.apply_height_toggle

    height, previous = apply_toggle(0, True, False)
    assert height == 1

    height, previous = apply_toggle(height, True, previous)
    assert height == 1

    height, previous = apply_toggle(height, False, previous)
    height, previous = apply_toggle(height, True, previous)
    assert height == 0


def test_released_button_does_not_change_height():
    """A released button only updates edge memory."""
    height, previous = (
        PneumaticGripperJoystickBridgeNode.apply_height_toggle(1, False, True)
    )

    assert height == 1
    assert previous is False


def test_held_button_after_timeout_requires_release():
    """A held button is suppressed when timeout edge memory is set to pressed."""
    height, previous = (
        PneumaticGripperJoystickBridgeNode.apply_height_toggle(0, True, True)
    )

    assert height == 0
    assert previous is True


def test_gripper_changes_once_per_b_press():
    """B toggles OPEN/CLOSE once per press and ignores a held button."""
    apply_toggle = PneumaticGripperJoystickBridgeNode.apply_gripper_toggle

    gripper, previous = apply_toggle(0, True, False)
    assert gripper == 1

    gripper, previous = apply_toggle(gripper, True, previous)
    assert gripper == 1

    gripper, previous = apply_toggle(gripper, False, previous)
    gripper, previous = apply_toggle(gripper, True, previous)
    assert gripper == 0


def test_held_b_after_timeout_requires_release():
    """A held B button cannot change the default OPEN state after timeout."""
    gripper, previous = (
        PneumaticGripperJoystickBridgeNode.apply_gripper_toggle(0, True, True)
    )

    assert gripper == 0
    assert previous is True
