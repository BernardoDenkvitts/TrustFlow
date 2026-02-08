"""Agreement enums matching database ENUMs."""

from enum import Enum


class ArbitrationPolicy(str, Enum):
    """Arbitration policy for an agreement.

    NONE: No arbitrator, only payer can release payment.
    WITH_ARBITRATOR: Has arbitrator who can resolve disputes.
    """

    NONE = "NONE"
    WITH_ARBITRATOR = "WITH_ARBITRATOR"


class AgreementStatus(str, Enum):
    """Status of an agreement in its lifecycle.

    DRAFT: Initial state, agreement created off-chain.
    PENDING_FUNDING: Submitted for on-chain creation, waiting for
    blockchain confirmation.
    CREATED: Agreement created on-chain, ready for funding.
    FUNDED: Payment deposited in escrow.
    DISPUTED: Dispute opened, funds locked.
    RELEASED: Payment released to payee.
    REFUNDED: Payment refunded to payer.
    """

    DRAFT = "DRAFT"
    PENDING_FUNDING = "PENDING_FUNDING"
    CREATED = "CREATED"
    FUNDED = "FUNDED"
    DISPUTED = "DISPUTED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
