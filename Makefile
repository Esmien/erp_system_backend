.PHONY: migrate make_migrations run

migrate:
	alembic -c backend/alembic.ini upgrade head

make_migrations:
	alembic -c backend/alembic.ini revision --autogenerate -m "$(m)"

run:
	docker compose up -d --build