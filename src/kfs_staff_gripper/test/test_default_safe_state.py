"""No-hardware checks for the shared five-relay startup state."""

from kfs_staff_gripper.kfs_staff_gripper_arduino_node import DEFAULT_SAFE_STATE


def test_default_state_matches_confirmed_five_relay_wiring():
    """KFS closes, staff gripper relays open, inclination relays stay OFF."""
    assert DEFAULT_SAFE_STATE == [0, 1, 0, 1, 0]
