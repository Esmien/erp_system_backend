import pytest


async def test_create_comment(comment_repo):

    comment_text = "Test comment"
    comment = await comment_repo.create(task_id=1, author_id=1, text=comment_text)

    assert comment.id is not None
    assert comment.task_id == 1
    assert comment.author_id == 1
    assert comment.text == comment_text


@pytest.mark.parametrize("task_id", [1, 999])
async def test_get_comments_by_task_id(comment_repo, task_id):
    items, total = await comment_repo.get_comments_by_task_id(task_id=task_id, offset=0, limit=20)

    assert isinstance(items, list)
    assert len(items) == 0
    assert total == 0
