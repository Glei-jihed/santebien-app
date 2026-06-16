from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cache import Cache
from app.database import get_db
from app.dependencies import current_user
from app.models import Comment, Question, User
from app.schemas import CommentCreate, QuestionCreate
from app.serializers import comment_data, question_detail, question_summary

router = APIRouter(prefix="/questions", tags=["questions"])
cache = Cache()


async def load_question(db: AsyncSession, question_id: str) -> Question:
    result = await db.execute(
        select(Question)
        .options(
            selectinload(Question.author),
            selectinload(Question.comments).selectinload(Comment.author),
        )
        .where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question introuvable")
    return question


@router.get("")
async def list_questions(
    search: str = "",
    tag: str = "",
    sort: str = Query(default="recent", pattern="^(recent|popular|unanswered)$"),
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    cache_key = f"santebien:questions:{search}:{tag}:{sort}:{limit}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    statement = select(Question).options(
        selectinload(Question.author),
        selectinload(Question.comments).selectinload(Comment.author),
    )
    if search:
        statement = statement.where(
            or_(
                Question.title.ilike(f"%{search}%"),
                Question.description.ilike(f"%{search}%"),
            )
        )
    if sort == "popular":
        statement = statement.order_by(desc(Question.vote_count), desc(Question.view_count))
    else:
        statement = statement.order_by(desc(Question.created_at))

    result = list((await db.execute(statement.limit(limit))).scalars().unique())
    if tag:
        result = [item for item in result if tag.lower() in [value.lower() for value in item.tags]]
    if sort == "unanswered":
        result = [item for item in result if not item.comments]

    data = [question_summary(item) for item in result]
    await cache.set(cache_key, data, ttl=90)
    return data


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: QuestionCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    question = Question(
        title=payload.title.strip(),
        description=payload.description.strip(),
        tags=[tag.strip().lower() for tag in payload.tags if tag.strip()][:5],
        author_id=user.id,
    )
    db.add(question)
    await db.commit()
    await cache.delete_pattern("santebien:questions:*")
    return question_summary(await load_question(db, question.id))


@router.get("/{question_id}")
async def get_question(
    question_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    cache_key = f"santebien:question:{question_id}"
    cached = await cache.get(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return cached

    question = await load_question(db, question_id)
    question.view_count += 1
    await db.commit()
    data = question_detail(question)
    await cache.set(cache_key, data, ttl=180)
    response.headers["X-Cache"] = "MISS"
    return data


@router.post("/{question_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(
    question_id: str,
    payload: CommentCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await load_question(db, question_id)
    comment = Comment(content=payload.content.strip(), author_id=user.id, question_id=question_id)
    db.add(comment)
    await db.commit()
    await cache.delete_pattern("santebien:questions:*")
    await cache.delete_pattern(f"santebien:question:{question_id}*")
    result = await db.execute(select(Comment).options(selectinload(Comment.author)).where(Comment.id == comment.id))
    return comment_data(result.scalar_one())


@router.post("/{question_id}/vote")
async def vote_question(
    question_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    del user
    question = await load_question(db, question_id)
    question.vote_count += 1
    await db.commit()
    await cache.delete_pattern("santebien:questions:*")
    await cache.delete_pattern(f"santebien:question:{question_id}*")
    return {"vote_count": question.vote_count}
