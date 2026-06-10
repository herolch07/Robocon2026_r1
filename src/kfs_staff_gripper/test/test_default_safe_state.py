"""No-hardware checks for the shared three-relay startup state."""

from kfs_staff_gripper.kfs_staff_gripper_arduino_node import DEFAULT_SAFE_STATE


def test_default_state_opens_arm_and_closes_kfs():
    """Relay order is arm height, arm gripper, then KFS gripper."""
    assert DEFAULT_SAFE_STATE == [0, 0, 0]
