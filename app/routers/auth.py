from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import current_user
from app.models import Session, User
from app.schemas import LoginRequest, ProfileUpdate, RegisterRequest
from app.security import (
    create_session_token,
    hash_password,
    hash_token,
    session_expiration,
    verify_password,
)
from app.serializers import user_private

router = APIRouter(prefix="/auth", tags=["auth"])


async def issue_session(db: AsyncSession, user: User) -> dict:
    token, token_hash = create_session_token()
    db.add(Session(token_hash=token_hash, user_id=user.id, expires_at=session_expiration()))
    await db.commit()
    return {"token": token, "user": user_private(user)}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    email = payload.email.lower().strip()
    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="Un compte existe deja avec cet email")

    user = User(
        email=email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()
    return await issue_session(db, user)


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    user = await db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte desactive")
    return await issue_session(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> None:
    if authorization and authorization.startswith("Bearer "):
        await db.execute(
            delete(Session).where(
                Session.token_hash == hash_token(authorization.removeprefix("Bearer ").strip())
            )
        )
        await db.commit()


@router.get("/me")
async def me(user: User = Depends(current_user)) -> dict:
    return user_private(user)


@router.patch("/me")
async def update_me(
    payload: ProfileUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user.display_name = payload.display_name.strip()
    user.bio = payload.bio.strip()
    user.specialty = payload.specialty.strip()
    await db.commit()
    await db.refresh(user)
    return user_private(user)
