.PHONY: run clean help

help:
	@echo "Available targets:"
	@echo "  make install   - Create a virtual environment and install dependencies"
	@echo "  make run       - Start the game"
	@echo "  make test      - Run tests"
	@echo "  make buzz-test - Check the Buzz controller"
	@echo "  make clean     - Clean temporary files and Python cache"
	@echo "  make help      - Display this help"

install:
	@echo "Creating virtual environment..."
	@uv venv
	@echo "Activating & Installing dependencies..."
	@. .venv/bin/activate && uv pip install --deps .

run:
	@echo "Starting Guess The Song Community Edition..."
	uv run src/main.py

buzz-test:
	@echo "You can test the Buzz controller now..."
	@uv run src/buzz_test.py

test:
	@echo "Running tests..."
	@uv run pytest

clean:
	@echo "Cleaning temporary files and cache..."
	@find . -type d -name ".mypy_cache" -exec rm -r {} +
	@find . -type d -name ".pytest_cache" -exec rm -r {} +
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".DS_Store" -delete

.DEFAULT_GOAL := help
