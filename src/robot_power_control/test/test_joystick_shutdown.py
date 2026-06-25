"""No-hardware tests for joystick long-press shutdown detection."""

from robot_power_control.joystick_shutdown_node import LongPressShutdownDetector


def test_four_button_hold_triggers_once_after_duration():
    detector = LongPressShutdownDetector(["x", "y", "b", "a"], 5.0)
    assert not detector.update(True, 10.0)
    assert not detector.update(True, 14.9)
    assert detector.update(True, 15.0)
    assert not detector.update(True, 16.0)


def test_release_resets_hold_timer():
    detector = LongPressShutdownDetector(["x", "y", "b", "a"], 5.0)
    assert not detector.update(True, 1.0)
    assert not detector.update(False, 3.0)
    assert not detector.update(True, 4.0)
    assert not detector.update(True, 8.9)
    assert detector.update(True, 9.0)


def test_zero_hold_triggers_on_second_pressed_sample():
    detector = LongPressShutdownDetector(["x"], 0.0)
    assert not detector.update(True, 1.0)
    assert detector.update(True, 1.0)
