"""Agreement domain exceptions."""

from decimal import Decimal

from src.modules.agreements.core.enums import AgreementStatus, ArbitrationPolicy


class AgreementNotFoundError(Exception):
    """Raised when an agreement is not found."""

    def __init__(self, agreement_id: Decimal | str) -> None:
        self.agreement_id = agreement_id
        super().__init__(f"Agreement not found: {agreement_id}")


class InvalidStateTransitionError(Exception):
    """Raised when attempting an invalid status transition."""

    def __init__(
        self,
        current_status: AgreementStatus,
        target_status: AgreementStatus,
        reason: str | None = None,
    ) -> None:
        self.current_status = current_status
        self.target_status = target_status
        self.reason = reason
        message = (
            f"Invalid state transition from {current_status.value} "
            f"to {target_status.value}"
        )
        if reason:
            message += f": {reason}"
        super().__init__(message)


class SelfDealError(Exception):
    """Raised when payer and payee are the same user."""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"Payer and payee cannot be the same user: {user_id}")


class InvalidArbitrationPolicyError(Exception):
    """Raised when arbitration policy constraints are violated."""

    def __init__(
        self,
        policy: ArbitrationPolicy,
        has_arbitrator: bool,
    ) -> None:
        self.policy = policy
        self.has_arbitrator = has_arbitrator
        if policy == ArbitrationPolicy.NONE and has_arbitrator:
            message = "Policy NONE cannot have an arbitrator"
        elif policy == ArbitrationPolicy.WITH_ARBITRATOR and not has_arbitrator:
            message = "Policy WITH_ARBITRATOR requires an arbitrator"
        else:
            message = f"Invalid arbitration policy configuration: {policy.value}"
        super().__init__(message)


class UnauthorizedAgreementAccessError(Exception):
    """Raised when a user attempts to access an agreement they're not part of."""

    def __init__(self, user_id: str, agreement_id: Decimal | str) -> None:
        self.user_id = user_id
        self.agreement_id = agreement_id
        super().__init__(
            f"User {user_id} is not authorized to access agreement {agreement_id}"
        )
