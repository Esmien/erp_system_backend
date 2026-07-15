async def test_create_task_success(client, open_task_json):
    response = await client.post("/api/v1/tasks/", json=open_task_json)

    data = response.json()

    assert response.status_code == 201
    assert data.get("title") == open_task_json["title"]
    assert "id" in data
    assert data.get("author_id") == 1
