"""Session repository for database access."""

import uuid
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.core.exceptions import SessionAlreadyExistsError
from src.modules.auth.core.models.session import Session


class SessionRepository:
    """Repository for Session model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> Session:
        """Create a new session."""
        session = Session(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )
        self._session.add(session)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise SessionAlreadyExistsError() from e
        return session

    async def get_by_hash(self, refresh_token_hash: str) -> Session | None:
        """Get session by refresh token hash."""
        stmt = select(Session).where(Session.refresh_token_hash == refresh_token_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_rotation(
        self, session_id: uuid.UUID, new_hash: str, last_used_at: datetime
    ) -> None:
        """Update session with new refresh token hash and last used time."""
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(refresh_token_hash=new_hash, last_used_at=last_used_at)
        )
        await self._session.execute(stmt)

    async def revoke(self, session_id: uuid.UUID) -> None:
        """Revoke a session by setting revoked_at to current time."""
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(revoked_at=datetime.utcnow())
        )
        await self._session.execute(stmt)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Revoke all active sessions for a user."""
        stmt = (
            update(Session)
            .where(Session.user_id == user_id, Session.revoked_at.is_(None))
            .values(revoked_at=datetime.utcnow())
        )
        await self._session.execute(stmt)

    async def enforce_session_limit(self, user_id: uuid.UUID, limit: int) -> None:
        """
        Enforce the maximum number of active sessions for a user.
        Removes the oldest sessions if the count exceeds the limit.
        """
        # Count active sessions (not revoked, not expired)
        stmt_count = (
            select(func.count(Session.id))
            .where(
                Session.user_id == user_id,
                Session.revoked_at.is_(None),
                Session.expires_at > datetime.utcnow()
            )
        )
        count = await self._session.scalar(stmt_count) or 0

        if count >= limit:
            excess = count - limit + 1
            
            if excess > 0:
                stmt_oldest = (
                    select(Session.id)
                    .where(
                        Session.user_id == user_id,
                        Session.revoked_at.is_(None),
                        Session.expires_at > datetime.utcnow()
                    )
                    .order_by(
                        Session.last_used_at.asc().nullsfirst(), 
                        Session.created_at.asc()
                    )
                    .limit(excess)
                )
                result = await self._session.execute(stmt_oldest)
                ids_to_revoke = result.scalars().all()

                if ids_to_revoke:
                    stmt_revoke = (
                        update(Session)
                        .where(Session.id.in_(ids_to_revoke))
                        .values(revoked_at=datetime.utcnow())
                    )
                    await self._session.execute(stmt_revoke)

    async def delete_expired(self) -> int:
        """Delete expired sessions."""
        stmt = delete(Session).where(Session.expires_at < datetime.utcnow())
        result = await self._session.execute(stmt)
        return result.rowcount
