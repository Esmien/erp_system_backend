from datetime import UTC, datetime

import pytest

from backend.comment.repository import CommentRepository
from backend.comment.schemas import CommentRead
from backend.comment.service import CommentService


@pytest.fixture
def comment_service(mock_uow, mock_rbac_service):
    return CommentService(uow=mock_uow, rbac_service=mock_rbac_service)


@pytest.fixture
def comment_repo(db_session):
    return CommentRepository(session=db_session)


@pytest.fixture
def sample_comment():
    return CommentRead(
        id=1,
        task_id=1,
        author_id=2,
        text="Тестовый комментарий",
        created_at=datetime.now(UTC),
    )
