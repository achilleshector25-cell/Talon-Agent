dev:
	python -m venv .venv && .venv/bin/pip install -e ".[dev]"
	uvicorn talon.gateway.core:app --port 8443 --reload

test:
	pytest -q tests/

lint:
	ruff check talon/ && mypy talon/

scan:
	python -m talon.skills.scanner --all

lockdown:
	python -m talon.gateway.core lockdown
