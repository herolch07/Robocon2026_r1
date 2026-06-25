"""Tests for confirmed 8BitDo/Xbox evdev device names."""

from my_joystick_driver.joystick_node import JoystickPublisher


def test_old_ultimate_24g_name_is_supported():
    assert JoystickPublisher._is_supported_device_name(
        '8BitDo Ultimate Wireless / Pro 2 Wired Controller', '8BitDo'
    )


def test_new_ultimate_3mode_xbox_name_is_supported():
    assert JoystickPublisher._is_supported_device_name(
        'Generic X-Box pad', '8BitDo'
    )


def test_custom_filter_remains_supported():
    assert JoystickPublisher._is_supported_device_name(
        'Xbox Wireless Controller', 'Xbox'
    )


def test_unrelated_input_device_is_rejected():
    assert not JoystickPublisher._is_supported_device_name(
        'vc4-hdmi-0', '8BitDo'
    )
