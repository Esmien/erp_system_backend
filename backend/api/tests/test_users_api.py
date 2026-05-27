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
