"""No-hardware tests for coherent four-wheel acceleration limiting."""

import pytest

from base_omniwheel_r2_700.local_navigation_node import LocalNavigationNode


def test_shared_alpha_preserves_arbitrary_direction_ratio_from_rest():
    """A 22-degree-like unequal wheel vector keeps one common scale."""
    current = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    target = {1: -30.75, 2: 13.05, 3: 30.75, 4: -13.05}

    limited, alpha = LocalNavigationNode.limit_wheel_vector_delta(
        current, target, max_delta=2.5
    )

    assert alpha == pytest.approx(2.5 / 30.75)
    for motor_id in target:
        assert limited[motor_id] == pytest.approx(target[motor_id] * alpha)


def test_shared_alpha_limits_every_wheel_delta():
    """No wheel may exceed the configured acceleration step."""
    current = {1: -5.0, 2: 3.0, 3: 5.0, 4: -3.0}
    target = {1: -30.0, 2: 12.0, 3: 30.0, 4: -12.0}

    limited, alpha = LocalNavigationNode.limit_wheel_vector_delta(
        current, target, max_delta=1.25
    )

    assert alpha < 1.0
    assert max(
        abs(limited[motor_id] - current[motor_id]) for motor_id in target
    ) == pytest.approx(1.25)


def test_target_passes_through_when_inside_acceleration_step():
    """Commands already inside the step are not modified."""
    current = {1: 1.0, 2: -2.0, 3: 2.0, 4: -1.0}
    target = {1: 1.5, 2: -2.5, 3: 2.5, 4: -1.5}

    limited, alpha = LocalNavigationNode.limit_wheel_vector_delta(
        current, target, max_delta=1.0
    )

    assert alpha == 1.0
    assert limited == target


def test_independent_limit_keeps_ramp_without_shared_alpha():
    """Per-wheel mode keeps a ramp but does not preserve target ratios."""
    current = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    target = {1: -30.75, 2: 13.05, 3: 30.75, 4: -13.05}

    limited = LocalNavigationNode.limit_wheel_independent_delta(
        current, target, max_delta=2.5
    )

    assert limited == pytest.approx({1: -2.5, 2: 2.5, 3: 2.5, 4: -2.5})


def test_independent_limit_passes_small_targets_through():
    """Small wheel deltas still reach the target in one cycle."""
    current = {1: 1.0, 2: -2.0, 3: 2.0, 4: -1.0}
    target = {1: 1.5, 2: -2.5, 3: 2.5, 4: -1.5}

    limited = LocalNavigationNode.limit_wheel_independent_delta(
        current, target, max_delta=1.0
    )

    assert limited == target
