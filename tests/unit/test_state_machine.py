"""Unit tests for the EVIDA Investigation Lifecycle State Machine."""

from __future__ import annotations

import pytest
from app.domain.investigations.models import InvestigationStatus
from app.domain.investigations.state_machine import (
    TERMINAL_STATES,
    InvalidStateTransitionError,
    InvestigationAlreadyTerminalError,
    is_valid_transition,
    validate_transition,
)


class TestStateMachineValidTransitions:
    """Verify all canonical transitions allowed by EVIDA lifecycle."""

    @pytest.mark.parametrize(
        ("current_status", "target_status"),
        [
            (InvestigationStatus.CREATED, InvestigationStatus.INGESTING),
            (InvestigationStatus.INGESTING, InvestigationStatus.REPRODUCING),
            (InvestigationStatus.REPRODUCING, InvestigationStatus.INVESTIGATING),
            (InvestigationStatus.INVESTIGATING, InvestigationStatus.VERIFYING),
            (InvestigationStatus.VERIFYING, InvestigationStatus.COMPLETED),
            # Failure transitions from any active state
            (InvestigationStatus.CREATED, InvestigationStatus.FAILED),
            (InvestigationStatus.INGESTING, InvestigationStatus.FAILED),
            (InvestigationStatus.REPRODUCING, InvestigationStatus.FAILED),
            (InvestigationStatus.INVESTIGATING, InvestigationStatus.FAILED),
            (InvestigationStatus.VERIFYING, InvestigationStatus.FAILED),
        ],
    )
    def test_valid_transitions_pass(
        self, current_status: InvestigationStatus, target_status: InvestigationStatus
    ) -> None:
        assert is_valid_transition(current_status, target_status) is True
        # validate_transition must complete without raising exception
        validate_transition(current_status, target_status)


class TestStateMachineInvalidTransitions:
    """Verify disallowed transitions raise deterministic LifecycleException."""

    @pytest.mark.parametrize(
        ("current_status", "target_status"),
        [
            (InvestigationStatus.CREATED, InvestigationStatus.COMPLETED),
            (InvestigationStatus.CREATED, InvestigationStatus.VERIFYING),
            (InvestigationStatus.CREATED, InvestigationStatus.INVESTIGATING),
            (InvestigationStatus.CREATED, InvestigationStatus.REPRODUCING),
            (InvestigationStatus.INGESTING, InvestigationStatus.COMPLETED),
            (InvestigationStatus.INGESTING, InvestigationStatus.CREATED),
            (InvestigationStatus.REPRODUCING, InvestigationStatus.INGESTING),
            (InvestigationStatus.INVESTIGATING, InvestigationStatus.CREATED),
            (InvestigationStatus.INVESTIGATING, InvestigationStatus.INGESTING),
            (InvestigationStatus.VERIFYING, InvestigationStatus.CREATED),
            (InvestigationStatus.VERIFYING, InvestigationStatus.REPRODUCING),
        ],
    )
    def test_invalid_transitions_rejected(
        self, current_status: InvestigationStatus, target_status: InvestigationStatus
    ) -> None:
        assert is_valid_transition(current_status, target_status) is False
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            validate_transition(current_status, target_status)
        assert exc_info.value.code == "INVALID_STATE_TRANSITION"
        assert exc_info.value.status_code == 409


class TestStateMachineTerminalStates:
    """Verify terminal states (COMPLETED, FAILED) can never transition to any state."""

    @pytest.mark.parametrize("terminal_state", list(TERMINAL_STATES))
    @pytest.mark.parametrize(
        "target_state",
        [
            InvestigationStatus.CREATED,
            InvestigationStatus.INGESTING,
            InvestigationStatus.REPRODUCING,
            InvestigationStatus.INVESTIGATING,
            InvestigationStatus.VERIFYING,
            InvestigationStatus.COMPLETED,
            InvestigationStatus.FAILED,
        ],
    )
    def test_terminal_states_cannot_transition(
        self, terminal_state: InvestigationStatus, target_state: InvestigationStatus
    ) -> None:
        assert is_valid_transition(terminal_state, target_state) is False
        with pytest.raises(InvestigationAlreadyTerminalError) as exc_info:
            validate_transition(terminal_state, target_state)
        assert exc_info.value.code == "INVESTIGATION_ALREADY_TERMINAL"
        assert exc_info.value.status_code == 409
