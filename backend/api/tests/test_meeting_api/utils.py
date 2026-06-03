from datetime import datetime, timezone, timedelta


def get_future_times(offset_hours: int = 1, duration_hours: int = 1):
    """Вспомогательная функция: генерирует безопасное время в будущем без секунд."""
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = now + timedelta(hours=offset_hours)
    end = start + timedelta(hours=duration_hours)
    return start.isoformat(), end.isoformat()
