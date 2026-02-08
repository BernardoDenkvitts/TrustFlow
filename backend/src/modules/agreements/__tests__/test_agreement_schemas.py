"""Unit tests for agreement schemas.

Tests only for custom validation logic.
"""

import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.modules.agreements.core.enums import ArbitrationPolicy
from src.modules.agreements.schemas import CreateAgreementRequest


class TestCreateAgreementRequest:
    """Tests for CreateAgreementRequest schema custom validators."""

    def test_create_request_negative_amount(self) -> None:
        """Should reject negative amount via custom validator."""
        with pytest.raises(ValidationError) as exc_info:
            CreateAgreementRequest(
                payee_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                arbitration_policy=ArbitrationPolicy.NONE,
                amount_wei=Decimal("-1000000000000000000"),
            )

        assert "Amount must be positive" in str(exc_info.value)

    def test_create_request_zero_amount(self) -> None:
        """Should reject zero amount via custom validator."""
        with pytest.raises(ValidationError) as exc_info:
            CreateAgreementRequest(
                payee_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                arbitration_policy=ArbitrationPolicy.NONE,
                amount_wei=Decimal("0"),
            )

        assert "Amount must be positive" in str(exc_info.value)
