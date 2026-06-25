"""No-hardware tests for direct STAFF/KFS mode selection."""

from operation_mode_control.operation_mode_selector_node import (
    MODE_KFS,
    MODE_STAFF,
    OperationModeSelectorNode,
)


def test_rising_edge_only_once_while_held():
    edge, held = OperationModeSelectorNode.rising_edge(True, False)
    assert edge is True
    edge, held = OperationModeSelectorNode.rising_edge(True, held)
    assert edge is False
    edge, _ = OperationModeSelectorNode.rising_edge(False, held)
    assert edge is False


def test_select_and_start_choose_modes_directly():
    assert OperationModeSelectorNode.resolve_mode(MODE_KFS, True, False) == MODE_STAFF
    assert OperationModeSelectorNode.resolve_mode(MODE_STAFF, False, True) == MODE_KFS


def test_simultaneous_mode_buttons_keep_current_mode():
    assert OperationModeSelectorNode.resolve_mode(MODE_STAFF, True, True) == MODE_STAFF
    assert OperationModeSelectorNode.resolve_mode(MODE_KFS, True, True) == MODE_KFS
