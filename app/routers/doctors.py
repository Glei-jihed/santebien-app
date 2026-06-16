from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import current_user
from app.models import DoctorApplication, User
from app.schemas import DoctorApplicationCreate
from app.serializers import doctor_application_data

router = APIRouter(prefix="/doctor-applications", tags=["doctor applications"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def apply_as_doctor(
    payload: DoctorApplicationCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if user.role in {"doctor", "admin"}:
        raise HTTPException(status_code=409, detail="Ce compte possede deja un role valide")
    existing = await db.scalar(select(DoctorApplication).where(DoctorApplication.user_id == user.id))
    if existing:
        raise HTTPException(status_code=409, detail="Une demande existe deja pour ce compte")

    application = DoctorApplication(user_id=user.id, **payload.model_dump())
    db.add(application)
    await db.commit()
    result = await db.execute(
        select(DoctorApplication)
        .options(selectinload(DoctorApplication.user))
        .where(DoctorApplication.id == application.id)
    )
    return doctor_application_data(result.scalar_one())


@router.get("/me")
async def my_application(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict | None:
    result = await db.execute(
        select(DoctorApplication)
        .options(selectinload(DoctorApplication.user))
        .where(DoctorApplication.user_id == user.id)
    )
    application = result.scalar_one_or_none()
    return doctor_application_data(application) if application else None
