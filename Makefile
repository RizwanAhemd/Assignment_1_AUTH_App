.PHONY: install format lint security test run-backend run-frontend all ci

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	cd frontend && npm install

format:
	black src/ tests/

lint:
	ruff check src/
	black --check src/ tests/

security:
	bandit -r src/ -x tests/

test:
	pytest -v --asyncio-mode=strict

run-backend:
	uvicorn src.main:app --reload

run-frontend:
	cd frontend && npm run dev

ci: lint security test
