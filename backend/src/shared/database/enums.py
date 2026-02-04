"""Database ENUMs"""

import enum


class ArbitrationPolicy(str, enum.Enum):
    """Arbitration policy for agreements."""

    NONE = "NONE"
    WITH_ARBITRATOR = "WITH_ARBITRATOR"


class AgreementStatus(str, enum.Enum):
    """Status of an agreement in the system."""

    DRAFT = "DRAFT"
    PENDING_FUNDING = "PENDING_FUNDING"
    CREATED = "CREATED"
    FUNDED = "FUNDED"
    DISPUTED = "DISPUTED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"


class DisputeStatus(str, enum.Enum):
    """Status of a dispute."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class DisputeResolution(str, enum.Enum):
    """Resolution outcome of a dispute."""

    RELEASE = "RELEASE"
    REFUND = "REFUND"


class OnchainEventName(str, enum.Enum):
    """Names of on-chain events emitted by the smart contract."""

    AGREEMENT_CREATED = "AGREEMENT_CREATED"
    PAYMENT_FUNDED = "PAYMENT_FUNDED"
    DISPUTE_OPENED = "DISPUTE_OPENED"
    PAYMENT_RELEASED = "PAYMENT_RELEASED"
    PAYMENT_REFUNDED = "PAYMENT_REFUNDED"
