async def test_get_my_info_success(client):
    response = await client.get("/api/v1/users/me/")
    data = response.json()

    assert response.status_code == 200
    assert data.get("email") == "admin@admin.com"
    assert "id" in data
    assert data.get("is_active") is True


async def test_update_my_info_success(client):
    update_data = {"name": "UpdatedAdmin", "surname": "NewSurname"}

    response = await client.patch("/api/v1/users/me/", json=update_data)
    data = response.json()

    assert response.status_code == 200
    assert data.get("name") == "UpdatedAdmin"
    assert data.get("surname") == "NewSurname"
    assert data.get("email") == "admin@admin.com"


async def test_update_my_info_forbidden_fields(client):
    update_data = {"name": "Hacker", "email": "hacker@hack.com"}

    response = await client.patch("/api/v1/users/me/", json=update_data)

    assert response.status_code == 422


async def test_delete_me_success(client):
    response = await client.delete("/api/v1/users/me/")

    assert response.status_code == 200
    assert "удален" in response.json()["message"]


async def test_get_my_statistics_empty(client):
    response = await client.get("/api/v1/users/me/statistics/")

    assert response.status_code == 200
    data = response.json()
    assert data["average_evaluation"] == 0
    assert data["tasks_evaluated_count"] == 0


async def test_get_my_statistics_with_data(client, closed_task_json, evaluation_data):
    me_response = await client.get("/api/v1/users/me/")
    my_id = me_response.json()["id"]

    task_create_response = await client.post("/api/v1/tasks/", json=closed_task_json)
    assert task_create_response.status_code == 201
    task_id = task_create_response.json()["id"]

    update_response = await client.patch(f"/api/v1/tasks/{task_id}/", json={"executor_id": my_id})
    assert update_response.status_code == 200

    eval_response = await client.post(f"/api/v1/tasks/{task_id}/evaluation/", json=evaluation_data)
    assert eval_response.status_code == 201

    stats_response = await client.get("/api/v1/users/me/statistics/")
    data = stats_response.json()

    assert stats_response.status_code == 200
    assert data["average_evaluation"] == evaluation_data["value"]

    assert data["tasks_evaluated_count"] >= 1
