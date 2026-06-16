from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Session, User
from app.security import hash_token


async def current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Connexion requise")

    token_hash = hash_token(authorization.removeprefix("Bearer ").strip())
    result = await db.execute(
        select(User)
        .join(Session, Session.user_id == User.id)
        .where(Session.token_hash == token_hash, Session.expires_at > datetime.now(timezone.utc))
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide")
    return user


async def optional_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not authorization:
        return None
    return await current_user(authorization, db)


async def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acces administrateur requis")
    return user


async def doctor_user(user: User = Depends(current_user)) -> User:
    if user.role not in {"doctor", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Profil medecin valide requis")
    return user
