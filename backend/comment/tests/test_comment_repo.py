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
    result = await comment_repo.get_comments_by_task_id(task_id=task_id)

    assert isinstance(result, list)
    assert len(result) == 0
