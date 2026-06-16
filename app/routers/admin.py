from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import admin_user
from app.models import DoctorApplication, User, now_utc
from app.schemas import DoctorApplicationReview
from app.serializers import doctor_application_data

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/doctor-applications")
async def list_doctor_applications(
    status: str = "pending",
    admin: User = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    del admin
    statement = select(DoctorApplication).options(selectinload(DoctorApplication.user))
    if status != "all":
        statement = statement.where(DoctorApplication.status == status)
    applications = list((await db.execute(statement.order_by(DoctorApplication.created_at))).scalars())
    return [doctor_application_data(item) for item in applications]


@router.patch("/doctor-applications/{application_id}")
async def review_doctor_application(
    application_id: str,
    payload: DoctorApplicationReview,
    admin: User = Depends(admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    del admin
    result = await db.execute(
        select(DoctorApplication)
        .options(selectinload(DoctorApplication.user))
        .where(DoctorApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Demande introuvable")

    application.status = payload.status
    application.admin_note = payload.admin_note.strip()
    application.reviewed_at = now_utc()
    if payload.status == "approved":
        application.user.role = "doctor"
        application.user.specialty = application.specialty
    await db.commit()
    return doctor_application_data(application)
