"""No-hardware tests for KFS-mode elevator speed mapping."""

from r1_arm_control.elevator_joystick_bridge_node import ElevatorJoystickBridgeNode


def test_l1_r1_elevator_speed_mapping():
    speed = ElevatorJoystickBridgeNode.speed_from_buttons
    assert speed(False, True, 3.0) == 3.0
    assert speed(True, False, 3.0) == -3.0
    assert speed(True, True, 3.0) == 0.0
    assert speed(False, False, 3.0) == 0.0
