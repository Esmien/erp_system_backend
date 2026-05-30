async def test_create_comment(comment_repo):

    comment_text = "Test comment"
    comment = await comment_repo.create_comment(
        task_id=1, author_id=1, text=comment_text
    )

    assert comment.id is not None
    assert comment.task_id == 1
    assert comment.author_id == 1
    assert comment.text == comment_text
