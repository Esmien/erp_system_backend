.PHONY: migrate make_migrations run get_key

migrate:
	docker compose exec backend alembic -c backend/alembic.ini upgrade head

make_migrations:
	docker compose exec backend alembic -c backend/alembic.ini revision --autogenerate -m "$(m)"

run:
	docker compose up -d --build

get_key:
	poetry run python3 ./backend/core/utils/secret_key_generator.py
