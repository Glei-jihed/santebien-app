from fastapi import APIRouter

from app.ai_model import analyze_question
from app.schemas import QuestionAnalysisRequest

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze-question")
async def analyze_question_content(payload: QuestionAnalysisRequest) -> dict:
    return analyze_question(
        title=payload.title,
        description=payload.description,
        tags=payload.tags,
        mode=payload.mode,
    )
