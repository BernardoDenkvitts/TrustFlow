"""OnchainEventName enum matching database schema."""

from enum import StrEnum


class OnchainEventName(StrEnum):
    """Names of on-chain events emitted by the smart contract.

    Values:
        AGREEMENT_CREATED: Agreement was created.
        PAYMENT_FUNDED: Payment was funded.
        DISPUTE_OPENED: Dispute was opened.
        PAYMENT_RELEASED: Payment was released.
        PAYMENT_REFUNDED: Payment was refunded.
    """

    AGREEMENT_CREATED = "AgreementCreated"
    PAYMENT_FUNDED = "PaymentFunded"
    DISPUTE_OPENED = "DisputeOpened"
    PAYMENT_RELEASED = "PaymentReleased"
    PAYMENT_REFUNDED = "PaymentRefunded"
