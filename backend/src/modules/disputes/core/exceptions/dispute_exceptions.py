"""Dispute domain exceptions."""

import uuid


class DisputeNotFoundError(Exception):
    """Raised when a dispute is not found."""

    def __init__(self, agreement_id: str) -> None:
        self.agreement_id = agreement_id
        super().__init__(f"Dispute not found for agreement: {agreement_id}")


class DisputeAlreadyExistsError(Exception):
    """Raised when attempting to create a dispute that already exists."""

    def __init__(self, agreement_id: str) -> None:
        self.agreement_id = agreement_id
        super().__init__(f"Dispute already exists for agreement: {agreement_id}")


class DisputeAlreadyResolvedError(Exception):
    """Raised when attempting to resolve an already resolved dispute."""

    def __init__(self, dispute_id: uuid.UUID | str) -> None:
        self.dispute_id = dispute_id
        super().__init__(f"Dispute already resolved: {dispute_id}")


class UnauthorizedDisputeAccessError(Exception):
    """Raised when a user attempts to access a dispute they're not part of."""

    def __init__(self, user_id: str, agreement_id: str) -> None:
        self.user_id = user_id
        self.agreement_id = agreement_id
        super().__init__(
            f"User {user_id} is not authorized to access "
            f"dispute for agreement {agreement_id}"
        )


class UnauthorizedArbitratorError(Exception):
    """Raised when a non-arbitrator attempts to resolve a dispute."""

    def __init__(self, user_id: str, agreement_id: str) -> None:
        self.user_id = user_id
        self.agreement_id = agreement_id
        super().__init__(
            f"User {user_id} is not the arbitrator for agreement {agreement_id}"
        )
