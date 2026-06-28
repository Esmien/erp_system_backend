.PHONY: migrate make_migrations run

migrate:
	docker compose exec backend alembic -c backend/alembic.ini upgrade head

make_migrations:
	docker compose exec backend alembic -c backend/alembic.ini revision --autogenerate -m "$(m)"

run:
	docker compose up -d --build