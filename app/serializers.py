from app.models import Article, Comment, DoctorApplication, Question, User


def user_public(user: User) -> dict:
    return {
        "id": user.id,
        "display_name": user.display_name,
        "role": user.role,
        "bio": user.bio,
        "specialty": user.specialty,
        "created_at": user.created_at,
    }


def user_private(user: User) -> dict:
    return {**user_public(user), "email": user.email}


def comment_data(comment: Comment) -> dict:
    return {
        "id": comment.id,
        "content": comment.content,
        "vote_count": comment.vote_count,
        "created_at": comment.created_at,
        "author": user_public(comment.author),
    }


def question_summary(question: Question) -> dict:
    return {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "tags": question.tags,
        "vote_count": question.vote_count,
        "view_count": question.view_count,
        "comment_count": len(question.comments),
        "created_at": question.created_at,
        "author": user_public(question.author),
    }


def question_detail(question: Question) -> dict:
    return {**question_summary(question), "comments": [comment_data(item) for item in question.comments]}


def article_summary(article: Article) -> dict:
    return {
        "id": article.id,
        "title": article.title,
        "summary": article.summary,
        "tags": article.tags,
        "view_count": article.view_count,
        "comment_count": len(article.comments),
        "created_at": article.created_at,
        "author": user_public(article.author),
    }


def article_detail(article: Article) -> dict:
    return {
        **article_summary(article),
        "content": article.content,
        "comments": [comment_data(item) for item in article.comments],
    }


def doctor_application_data(application: DoctorApplication) -> dict:
    return {
        "id": application.id,
        "license_number": application.license_number,
        "specialty": application.specialty,
        "document_url": application.document_url,
        "motivation": application.motivation,
        "status": application.status,
        "admin_note": application.admin_note,
        "created_at": application.created_at,
        "reviewed_at": application.reviewed_at,
        "user": user_private(application.user),
    }
