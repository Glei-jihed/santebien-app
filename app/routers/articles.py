from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cache import Cache
from app.database import get_db
from app.dependencies import current_user, doctor_user
from app.models import Article, Comment, User
from app.schemas import ArticleCreate, CommentCreate
from app.serializers import article_detail, article_summary, comment_data

router = APIRouter(prefix="/articles", tags=["articles"])
cache = Cache()


async def load_article(db: AsyncSession, article_id: str) -> Article:
    result = await db.execute(
        select(Article)
        .options(
            selectinload(Article.author),
            selectinload(Article.comments).selectinload(Comment.author),
        )
        .where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return article


@router.get("")
async def list_articles(
    search: str = "",
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    key = f"santebien:articles:{search}:{limit}"
    cached = await cache.get(key)
    if cached is not None:
        return cached

    statement = (
        select(Article)
        .options(
            selectinload(Article.author),
            selectinload(Article.comments).selectinload(Comment.author),
        )
        .order_by(desc(Article.created_at))
    )
    if search:
        statement = statement.where(
            or_(Article.title.ilike(f"%{search}%"), Article.summary.ilike(f"%{search}%"))
        )
    articles = list((await db.execute(statement.limit(limit))).scalars().unique())
    data = [article_summary(item) for item in articles]
    await cache.set(key, data, ttl=180)
    return data


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: ArticleCreate,
    user: User = Depends(doctor_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    article = Article(
        title=payload.title.strip(),
        summary=payload.summary.strip(),
        content=payload.content.strip(),
        tags=[tag.strip().lower() for tag in payload.tags if tag.strip()][:5],
        author_id=user.id,
    )
    db.add(article)
    await db.commit()
    await cache.delete_pattern("santebien:articles:*")
    return article_summary(await load_article(db, article.id))


@router.get("/{article_id}")
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    key = f"santebien:article:{article_id}"
    cached = await cache.get(key)
    if cached is not None:
        return cached
    article = await load_article(db, article_id)
    article.view_count += 1
    await db.commit()
    data = article_detail(article)
    await cache.set(key, data, ttl=300)
    return data


@router.post("/{article_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_article_comment(
    article_id: str,
    payload: CommentCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await load_article(db, article_id)
    comment = Comment(content=payload.content.strip(), author_id=user.id, article_id=article_id)
    db.add(comment)
    await db.commit()
    await cache.delete_pattern("santebien:articles:*")
    await cache.delete_pattern(f"santebien:article:{article_id}*")
    result = await db.execute(select(Comment).options(selectinload(Comment.author)).where(Comment.id == comment.id))
    return comment_data(result.scalar_one())
