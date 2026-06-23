import json
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
env_path = BASE_DIR / ".env"

load_dotenv(dotenv_path=env_path)

from backend.api.main import app  # noqa: E402


def export_openapi():
    """
    Генерирует и сохраняет OpenAPI схему приложения в файл openapi.json
    """
    openapi_schema = app.openapi()

    # Сохраняем файл в корень проекта
    output_path = BASE_DIR / "openapi.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)

    print(f"Схема OpenAPI успешно сохранена в {output_path}")


if __name__ == "__main__":
    export_openapi()
