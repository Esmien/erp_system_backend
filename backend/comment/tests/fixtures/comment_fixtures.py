from datetime import datetime, timezone

import pytest

from backend.comment.repository import CommentRepository
from backend.comment.schemas import CommentRead
from backend.comment.service import CommentService


@pytest.fixture
def comment_service(mock_uow):
    return CommentService(uow=mock_uow)


@pytest.fixture
def comment_repo(db_session):
    return CommentRepository(session=db_session)


@pytest.fixture
def sample_comment():
    return CommentRead(
        id=1,
        task_id=1,
        author_id=1,
        text="Тестовый комментарий",
        created_at=datetime.now(timezone.utc),
    )
