# Web+ Backend Testing Guide

This directory contains tests for the Web+ backend, focusing on database models, CRUD operations, and API endpoints.

## Test Structure

- `tests/conftest.py` - Contains fixtures and test database setup
- `tests/db/` - Database tests
  - `test_models.py` - Tests for database models
  - `test_crud.py` - Tests for basic CRUD operations
  - `test_optimized_crud.py` - Tests for optimized query operations
  - `test_integration.py` - Integration tests for database functionality
  - `test_indexes.py` - Performance tests for database indexes

## Running Tests

To run the tests, use pytest from the backend directory:

```bash
cd apps/backend
python -m pytest
```

### Running Specific Test Categories

Run unit tests only:

```bash
python -m pytest -m unit
```

Run integration tests only:

```bash
python -m pytest -m integration
```

Run tests for specific components:

```bash
python -m pytest -m models  # Database model tests
python -m pytest -m crud    # CRUD operation tests
```

Skip slow tests:

```bash
python -m pytest -k "not slow"
```

### Generating Coverage Reports

To generate a test coverage report:

```bash
python -m pytest --cov=db --cov-report=term-missing
```

For an HTML coverage report:

```bash
python -m pytest --cov=db --cov-report=html
```

This will create a `htmlcov` directory with the coverage report.

## Adding New Tests

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Add appropriate markers for test categorization
3. Create fixtures in `conftest.py` if needed
4. Use pytest-asyncio for asynchronous tests

## Test Database

Tests use an in-memory SQLite database by default. The database is recreated for each test function, ensuring test isolation.

## Continuous Integration

These tests are intended to be run in a CI/CD pipeline to ensure code quality and prevent regressions.