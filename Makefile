.PHONY: run test eval install lint clean

VENV ?= backend/venv
PYTHON ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
UVICORN ?= $(VENV)/bin/uvicorn
PYTEST ?= $(VENV)/bin/pytest

install:
	@if [ ! -d "$(VENV)" ]; then python3 -m venv $(VENV); fi
	$(PIP) install -r backend/requirements.txt
	@if [ -f "backend/requirements-dev.txt" ]; then $(PIP) install -r backend/requirements-dev.txt; fi

run:
	./start.sh

test:
	@if [ -x "$(PYTEST)" ]; then \
		PYTHONPATH=backend $(PYTEST) backend/tests -v; \
	else \
		python3 -m pytest backend/tests -v; \
	fi

eval:
	PYTHONPATH=backend $(PYTHON) -m evaluation.runner

lint:
	@if [ -x "$(VENV)/bin/ruff" ]; then \
		$(VENV)/bin/ruff check backend; \
	elif command -v ruff >/dev/null 2>&1; then \
		ruff check backend; \
	else \
		echo "ruff not installed, skipping"; \
	fi

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
