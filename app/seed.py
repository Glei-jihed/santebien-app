from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article, Comment, DoctorApplication, Question, User, now_utc
from app.security import hash_password


async def seed_data(db: AsyncSession) -> None:
    if await db.scalar(select(func.count(User.id))):
        return

    admin = User(
        email="admin@santebien.fr",
        display_name="Admin SanteBien",
        password_hash=hash_password("Admin123!"),
        role="admin",
        bio="Équipe de modération SanteBien.",
    )
    doctor = User(
        email="medecin@santebien.fr",
        display_name="Dr. Camille Laurent",
        password_hash=hash_password("Doctor123!"),
        role="doctor",
        specialty="Médecine générale",
        bio="Médecin généraliste, profil vérifié par SanteBien.",
    )
    user = User(
        email="user@santebien.fr",
        display_name="Nora",
        password_hash=hash_password("User123!"),
        bio="Membre de la communauté SanteBien.",
    )
    candidate = User(
        email="candidat@santebien.fr",
        display_name="Dr. Malik Benali",
        password_hash=hash_password("Doctor123!"),
        specialty="Cardiologie",
    )
    db.add_all([admin, doctor, user, candidate])
    await db.flush()

    question_one = Question(
        title="Comment améliorer progressivement la qualité de mon sommeil ?",
        description=(
            "Depuis plusieurs semaines, je dors mal et je souhaite mettre en place des habitudes "
            "simples avant de consulter. Quels changements doux puis-je tester ?"
        ),
        tags=["sommeil", "habitudes", "bien-être"],
        author_id=user.id,
        vote_count=18,
        view_count=142,
    )
    question_two = Question(
        title="Comment distinguer une fatigue passagère d'un problème à surveiller ?",
        description=(
            "Je ressens de la fatigue depuis quelques jours. Je cherche des repères généraux pour "
            "savoir quand consulter, sans demander de diagnostic en ligne."
        ),
        tags=["fatigue", "prévention"],
        author_id=candidate.id,
        vote_count=11,
        view_count=96,
    )
    article = Article(
        title="Sept habitudes simples pour protéger son sommeil",
        summary="Des conseils progressifs et réalistes pour construire une routine de sommeil plus stable.",
        content=(
            "Le sommeil se travaille rarement avec une solution unique. Commencez par stabiliser "
            "vos horaires, réduire les excitants en fin de journée et créer une transition calme "
            "avant le coucher.\n\nUne exposition à la lumière naturelle le matin aide également "
            "à réguler le rythme veille-sommeil. En cas de symptômes persistants, consultez un professionnel."
        ),
        tags=["sommeil", "prévention"],
        author_id=doctor.id,
        view_count=210,
    )
    db.add_all([question_one, question_two, article])
    await db.flush()

    db.add_all(
        [
            Comment(
                content="Commencez par fixer une heure de lever régulière. C'est souvent plus simple que de forcer l'endormissement.",
                author_id=doctor.id,
                question_id=question_one.id,
                vote_count=24,
            ),
            Comment(
                content="Un carnet de sommeil pendant une semaine m'a aidé à identifier les habitudes qui me perturbaient.",
                author_id=user.id,
                question_id=question_one.id,
                vote_count=7,
            ),
            DoctorApplication(
                user_id=candidate.id,
                license_number="RPPS-DEMO-2026",
                specialty="Cardiologie",
                document_url="https://example.org/justificatif-demo.pdf",
                motivation="Je souhaite partager des conseils de prévention fiables et participer à la modération médicale.",
                status="pending",
                created_at=now_utc(),
            ),
        ]
    )
    await db.commit()
