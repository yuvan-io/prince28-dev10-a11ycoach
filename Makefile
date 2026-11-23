.PHONY: install test test-unit test-integration lint format up down

install:
    uv sync --all-groups

test:
    uv run poe test

test-unit:
    uv run poe test-unit

test-integration:
    uv run poe test-integration

lint:
    uv run poe lint

format:
    uv run poe format

up:
    docker compose up --build -d

down:
    docker compose down
