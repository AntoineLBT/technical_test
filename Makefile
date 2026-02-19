.PHONY: dev test docker-up docker-down docker-test

dev:
	uv sync
	docker compose up postgres mailhog -d
	cp .env.example .env
	uv run uvicorn app.main:app --reload

test:
	uv sync
	docker compose up postgres -d
	cp .env.example .env
	uv run pytest tests/ -v

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-test:
	docker compose down
	docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit
