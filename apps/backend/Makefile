.PHONY: test test-models test-crud test-optimized-crud test-integration test-all test-cov clean

# Environment variables
PYTHONPATH := $(shell pwd)
export PYTHONPATH

# Default target
test:
	pytest tests/db/test_models.py tests/db/test_crud.py -v

# Test specific components
test-models:
	pytest tests/db/test_models.py -v

test-crud:
	pytest tests/db/test_crud.py -v

test-optimized-crud:
	pytest tests/db/test_optimized_crud.py -v

test-integration:
	pytest tests/db/test_integration.py -v

# Test all with tags
test-unit:
	pytest -m unit -v

test-integration-only:
	pytest -m integration -v

# Run all tests
test-all:
	pytest

# Generate coverage report
test-cov:
	pytest --cov=db --cov-report=term-missing --cov-report=html

# Clean up generated files
clean:
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.xml
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -rf tests/db/__pycache__/
	find . -name "*.pyc" -delete