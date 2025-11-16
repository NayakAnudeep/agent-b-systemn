.PHONY: install test clean run example

# Install dependencies
install:
	pip install -r requirements.txt
	playwright install chromium

# Run tests
test:
	pytest tests/ -v

# Clean generated files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf output/
	rm -rf .pytest_cache/
	rm -rf *.egg-info/

# Run example
example:
	python examples/basic_usage.py

# Run main demo
run:
	python src/main.py

# Setup environment
setup:
	cp .env.example .env
	@echo "Please edit .env and add your API keys"

# Format code
format:
	black src/ tests/ examples/

# Lint code
lint:
	flake8 src/ tests/ examples/

# Help
help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies and Playwright browsers"
	@echo "  make setup    - Copy .env.example to .env"
	@echo "  make test     - Run test suite"
	@echo "  make example  - Run example usage script"
	@echo "  make run      - Run main demo"
	@echo "  make clean    - Remove generated files"
	@echo "  make format   - Format code with black"
	@echo "  make lint     - Lint code with flake8"
