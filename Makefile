# Local development: SQLite database and dev login, no Docker or GCP needed.
# Expects the core-library repo checked out next to this one (../core-library).
#
#   make run     first run creates .venv, .env and pizza.db with a sample menu,
#                then serves http://localhost:8000 (OpenAPI: /docs)
#   make test

VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup run test lint migrate seed reset-db

setup: $(VENV)/.installed .env migrate seed

$(VENV)/.installed: pyproject.toml ../core-library/pyproject.toml
	python3 -m venv $(VENV)
	$(BIN)/pip install --quiet --upgrade pip
	$(BIN)/pip install --quiet -e "../core-library[fastapi,pubsub]" -e ".[dev]"
	touch $@

.env:
	cp .env.example .env

migrate: $(VENV)/.installed .env
	$(BIN)/alembic upgrade head

seed: migrate
	$(BIN)/python -m scripts.seed

run: setup
	$(BIN)/uvicorn app.main:app --reload --port 8000

test: $(VENV)/.installed
	$(BIN)/pytest

lint: $(VENV)/.installed
	$(BIN)/ruff check .

reset-db:
	rm -f pizza.db
