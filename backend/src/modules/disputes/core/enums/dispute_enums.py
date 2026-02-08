"""Dispute enums matching database schema."""

from enum import Enum


class DisputeStatus(str, Enum):
    """Status of a dispute in the system.

    Values:
        OPEN: Dispute has been opened, awaiting resolution.
        RESOLVED: Dispute has been resolved by the arbitrator.
    """

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class DisputeResolution(str, Enum):
    """Resolution outcome of a dispute.

    Values:
        RELEASE: Funds released to payee.
        REFUND: Funds refunded to payer.
    """

    RELEASE = "RELEASE"
    REFUND = "REFUND"
