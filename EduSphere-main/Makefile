SHELL := /bin/zsh
PYTHON := backend/.venv/bin/python
PIP := backend/.venv/bin/pip
NPM := npm --prefix frontend --cache frontend/.npm-cache

.PHONY: dev worker check migrate install

install:
	python3 -m venv backend/.venv
	$(PIP) install -e 'backend[dev]'
	$(NPM) install


worker:
	$(PYTHON) -m app.workers.process

dev: migrate
	trap 'kill 0' INT TERM EXIT; \
	$(PYTHON) -m uvicorn app.main:app --app-dir backend --reload & \
	$(PYTHON) -m app.workers.process & \
	$(NPM) run dev -- --host 0.0.0.0 & \
	wait

check:
	cd backend && .venv/bin/python -m ruff check app tests alembic
	cd backend && .venv/bin/python -m mypy app
	$(PYTHON) -m pytest backend/tests
	$(NPM) run lint
	$(NPM) run format:check
	$(NPM) run build
	$(NPM) test

migrate:
	mkdir -p backend/storage
	$(PYTHON) -m alembic -c backend/alembic.ini upgrade head

