"""Unit tests for user schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.modules.users.schemas import UpdateWalletRequest, UserResponse


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_from_attributes(self) -> None:
        """Should create response from ORM attributes."""

        # Simulating an ORM object
        class MockUser:
            id = uuid.UUID("00000000-0000-0000-0000-000000000001")
            email = "test@example.com"
            wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
            created_at = datetime(2026, 1, 1, tzinfo=UTC)
            updated_at = datetime(2026, 1, 2, tzinfo=UTC)

        response = UserResponse.model_validate(MockUser())

        assert response.id == MockUser.id
        assert response.email == MockUser.email
        assert response.wallet_address == MockUser.wallet_address
        assert response.created_at == MockUser.created_at
        assert response.updated_at == MockUser.updated_at


class TestUpdateWalletRequest:
    """Tests for UpdateWalletRequest schema."""

    def test_valid_lowercase_wallet(self) -> None:
        """Should accept valid lowercase wallet address."""
        request = UpdateWalletRequest(
            wallet_address="0x1234567890abcdef1234567890abcdef12345678"
        )
        assert request.wallet_address == "0x1234567890abcdef1234567890abcdef12345678"

    def test_valid_uppercase_wallet_normalized(self) -> None:
        """Should normalize uppercase wallet to lowercase."""
        request = UpdateWalletRequest(
            wallet_address="0xABCDEF1234567890ABCDEF1234567890ABCDEF12"
        )
        assert request.wallet_address == "0xabcdef1234567890abcdef1234567890abcdef12"

    def test_valid_mixed_case_wallet_normalized(self) -> None:
        """Should normalize mixed case wallet to lowercase."""
        request = UpdateWalletRequest(
            wallet_address="0xAbCdEf1234567890AbCdEf1234567890AbCdEf12"
        )
        assert request.wallet_address == "0xabcdef1234567890abcdef1234567890abcdef12"

    @pytest.mark.parametrize(
        "invalid_wallet,error_msg",
        [
            ("invalid", "String should have at least 42 characters"),
            ("0x123", "String should have at least 42 characters"),
            (
                "0x1234567890abcdef1234567890abcdef1234567890extra",
                "String should have at most 42 characters",
            ),
            (
                "0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
                "Invalid wallet address format",
            ),
            (
                "1234567890abcdef1234567890abcdef12345678ab",
                "Invalid wallet address format",
            ),
        ],
    )
    def test_invalid_wallet_address(self, invalid_wallet: str, error_msg: str) -> None:
        """Should reject invalid wallet addresses."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateWalletRequest(wallet_address=invalid_wallet)

        assert error_msg in str(exc_info.value)
