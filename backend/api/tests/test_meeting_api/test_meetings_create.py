from datetime import datetime, timezone, timedelta


from backend.api.tests.test_meeting_api.utils import get_future_times


async def test_create_meeting_success(client):
    start, end = get_future_times()
    payload = {
        "theme": "Обсуждение архитектуры",
        "datetime_start": start,
        "datetime_end": end,
        "participant_ids": [2, 3],
    }

    response = await client.post("/api/v1/meetings/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data.get("id") is not None
    assert data.get("theme") == "Обсуждение архитектуры"
    assert len(data.get("participants", [])) == 2


async def test_create_meeting_past_time_validation(client):
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=1)).isoformat()
    end = now.isoformat()

    response = await client.post(
        "/api/v1/meetings/",
        json={
            "theme": "Встреча в прошлом",
            "datetime_start": start,
            "datetime_end": end,
            "participant_ids": [],
        },
    )
    assert response.status_code == 400
    assert "раньше текущего времени" in response.json()["detail"].lower()


async def test_create_meeting_overlap(client):
    start, end = get_future_times(offset_hours=2)
    payload = {
        "theme": "Встреча первая",
        "datetime_start": start,
        "datetime_end": end,
        "participant_ids": [2],
    }

    await client.post("/api/v1/meetings/", json=payload)

    # Пытаемся создать вторую на то же время с тем же участником
    payload["theme"] = "Встреча с накладкой"
    response = await client.post("/api/v1/meetings/", json=payload)

    assert response.status_code in (400, 409)
    assert "заняты в это время" in response.json()["detail"].lower()
