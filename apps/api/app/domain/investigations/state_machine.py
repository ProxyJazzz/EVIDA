"""Investigation Lifecycle State Machine

Enforces deterministic state transitions for the EVIDA investigation lifecycle.
"""

from __future__ import annotations

from typing import Final

from app.domain.investigations.models import InvestigationStatus


class LifecycleException(Exception):
    """Base class for all domain investigation lifecycle exceptions."""

    def __init__(self, message: str, code: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class InvestigationNotFoundError(LifecycleException):
    def __init__(self, investigation_id: str) -> None:
        super().__init__(
            message=f"Investigation with ID '{investigation_id}' was not found.",
            code="INVESTIGATION_NOT_FOUND",
            status_code=404,
        )


class InvalidStateTransitionError(LifecycleException):
    def __init__(
        self,
        current_status: InvestigationStatus,
        target_status: InvestigationStatus,
        reason: str | None = None,
    ) -> None:
        detail = reason or (
            f"Cannot transition investigation from '{current_status}' to '{target_status}'. "
            f"Allowed transitions from '{current_status}': "
            f"{sorted([s.value for s in VALID_TRANSITIONS.get(current_status, set())])}."
        )
        super().__init__(
            message=detail,
            code="INVALID_STATE_TRANSITION",
            status_code=409,
        )


class InvestigationAlreadyTerminalError(LifecycleException):
    def __init__(self, current_status: InvestigationStatus) -> None:
        super().__init__(
            message=(
                f"Investigation is already in terminal state '{current_status}' "
                "and cannot transition to any other state."
            ),
            code="INVESTIGATION_ALREADY_TERMINAL",
            status_code=409,
        )


class InvalidInvestigationRequestError(LifecycleException):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code="INVALID_INVESTIGATION_REQUEST",
            status_code=422,
        )


class InvestigationPersistenceError(LifecycleException):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code="INVESTIGATION_PERSISTENCE_ERROR",
            status_code=500,
        )


# Terminal states that cannot transition anywhere
TERMINAL_STATES: Final[set[InvestigationStatus]] = {
    InvestigationStatus.COMPLETED,
    InvestigationStatus.FAILED,
}

# Strict canonical transition mapping
VALID_TRANSITIONS: Final[dict[InvestigationStatus, set[InvestigationStatus]]] = {
    InvestigationStatus.CREATED: {
        InvestigationStatus.INGESTING,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.INGESTING: {
        InvestigationStatus.REPRODUCING,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.REPRODUCING: {
        InvestigationStatus.INVESTIGATING,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.INVESTIGATING: {
        InvestigationStatus.VERIFYING,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.VERIFYING: {
        InvestigationStatus.COMPLETED,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.COMPLETED: set(),
    InvestigationStatus.FAILED: set(),
    # Compatibility with Phase 0 seed/legacy status
    InvestigationStatus.PENDING: {
        InvestigationStatus.INGESTING,
        InvestigationStatus.REPRODUCING,
        InvestigationStatus.FAILED,
    },
}


def is_valid_transition(
    current_status: InvestigationStatus, target_status: InvestigationStatus
) -> bool:
    """Return True if the state transition from current_status to target_status is allowed."""
    if current_status in TERMINAL_STATES:
        return False
    allowed = VALID_TRANSITIONS.get(current_status, set())
    return target_status in allowed


def validate_transition(
    current_status: InvestigationStatus, target_status: InvestigationStatus
) -> None:
    """Validate transition or raise a deterministic LifecycleException.

    Raises:
        InvestigationAlreadyTerminalError: If the investigation is already in a terminal state.
        InvalidStateTransitionError: If the transition is not permitted by canonical rules.
    """
    if current_status in TERMINAL_STATES:
        raise InvestigationAlreadyTerminalError(current_status=current_status)

    allowed = VALID_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise InvalidStateTransitionError(
            current_status=current_status,
            target_status=target_status,
        )


def get_valid_next_states(current_status: InvestigationStatus) -> set[InvestigationStatus]:
    """Return the set of valid target states reachable from current_status."""
    return VALID_TRANSITIONS.get(current_status, set()).copy()
