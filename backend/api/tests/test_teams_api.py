async def test_get_team_info_by_id_success(client, response_get_team_by_id):
    response = await client.get("/api/v1/teams/1")

    assert response.status_code == 200
    assert response_get_team_by_id == response.json()


async def test_get_team_info_by_id_not_exists(client):
    response = await client.get("/api/v1/teams/999")

    assert response.status_code == 404


async def test_create_team_success(
    client,
    request_body_for_create_team,
    response_data_by_create_team,
):
    response = await client.post("/api/v1/teams/", json=request_body_for_create_team)

    response_json = response.json()

    for key, value in response_data_by_create_team.items():
        assert response_json.get(key) == value

    assert response.status_code == 201


async def test_create_team_duplicate_name(
    client, request_duplicate, response_data_duplicate
):
    response = await client.post("/api/v1/teams/", json=request_duplicate)

    assert response.status_code == 400
    assert response.json() == response_data_duplicate


async def test_join_success(
    client, join_team_right_code_request, join_team_success_response
):
    response = await client.post(
        "/api/v1/teams/join", json=join_team_right_code_request
    )

    assert response.status_code == 200
    assert response.json() == join_team_success_response


async def test_join_already_in_team(
    client, join_team_right_code_request, join_team_already_exists_response
):
    await client.post("/api/v1/teams/join", json=join_team_right_code_request)
    response = await client.post(
        "/api/v1/teams/join", json=join_team_right_code_request
    )

    assert response.status_code == 400
    assert response.json() == join_team_already_exists_response


async def test_join_wrong_code(
    client, join_team_wrong_code_request, join_team_wrong_code_response
):
    response = await client.post(
        "/api/v1/teams/join", json=join_team_wrong_code_request
    )

    assert response.status_code == 404
    assert response.json() == join_team_wrong_code_response
