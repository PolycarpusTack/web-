# Testing Guide for Web+

This guide covers the comprehensive testing setup for the Web+ application, including backend and frontend testing strategies, tools, and best practices.

## Table of Contents

- [Overview](#overview)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Web+ uses a comprehensive testing strategy covering:

- **Unit Tests**: Individual components and functions
- **Integration Tests**: API endpoints and component interactions
- **End-to-End Tests**: Full user workflows
- **Performance Tests**: Load and lighthouse testing
- **Security Tests**: Vulnerability scanning

### Tech Stack

**Backend Testing:**
- pytest (async support)
- pytest-cov (coverage)
- faker (test data)
- httpx (API testing)

**Frontend Testing:**
- Jest (test runner)
- React Testing Library (component testing)
- @testing-library/user-event (user interactions)
- MSW (API mocking)

## Backend Testing

### Setup

```bash
cd apps/backend

# Install dependencies
pip install -r requirements.txt

# Set up test database
python -m db.init_db

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test types
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m slow           # Long-running tests
```

### Test Structure

```
apps/backend/tests/
├── conftest.py                 # Shared fixtures
├── mocks/
│   └── ollama_mock.py         # External service mocks
├── db/
│   ├── test_crud.py           # Database operations
│   ├── test_models.py         # Model validation
│   └── test_integration.py   # Database integration
├── pipeline/
│   ├── test_engine.py         # Pipeline execution
│   └── test_router.py         # Pipeline API
└── test_api_endpoints.py      # API integration tests
```

### Key Features

1. **Async Support**: Full async/await testing
2. **Database Isolation**: Each test gets a fresh database
3. **Mock External Services**: Ollama API is mocked
4. **Comprehensive Fixtures**: User, model, conversation, message fixtures
5. **Coverage Reporting**: HTML and XML coverage reports

### Example Test

```python
@pytest.mark.asyncio
async def test_create_conversation(client, auth_headers, test_model):
    """Test creating a new conversation."""
    conversation_data = {
        "model_id": test_model.id,
        "title": "Test Conversation",
        "system_prompt": "You are a helpful assistant."
    }
    
    response = await client.post(
        "/api/conversations", 
        json=conversation_data, 
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Conversation"
```

## Frontend Testing

### Setup

```bash
cd apps/frontend

# Install dependencies
npm install

# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui
```

### Test Structure

```
apps/frontend/src/
├── test-utils/
│   └── index.tsx              # Custom render and utilities
├── components/
│   ├── ui/__tests__/
│   │   └── button.test.tsx    # UI component tests
│   └── auth/__tests__/
│       └── LoginForm.test.tsx # Complex component tests
├── hooks/__tests__/
│   └── use-toast.test.ts      # Custom hook tests
├── api/__tests__/
│   └── conversations.test.ts  # API integration tests
└── pages/__tests__/
    └── EnhancedChatPage.test.tsx # Page component tests
```

### Key Features

1. **Custom Render**: Includes all providers (Auth, Theme, Router)
2. **Mock Utilities**: Pre-configured mocks for APIs and external dependencies
3. **User Event Testing**: Realistic user interactions
4. **Accessibility Testing**: Built-in a11y checks
5. **TypeScript Support**: Full type safety in tests

### Example Component Test

```typescript
describe('Button Component', () => {
  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies destructive variant styles', () => {
    render(<Button variant="destructive">Delete</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-destructive');
  });
});
```

### Example Hook Test

```typescript
describe('useToast Hook', () => {
  it('creates a toast with custom duration', () => {
    const { result } = renderHook(() => useToast());
    
    act(() => {
      result.current.toast({
        title: 'Custom Duration Toast',
        duration: 2000,
      });
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].duration).toBe(2000);
  });
});
```

### API Testing

```typescript
describe('Conversations API', () => {
  it('fetches conversations successfully', async () => {
    const mockConversations = [
      createMockConversation({ id: '1', title: 'Test' })
    ];

    mockApi.get.mockResolvedValue({ data: mockConversations });

    const result = await getConversations();

    expect(mockApi.get).toHaveBeenCalledWith('/api/conversations');
    expect(result).toEqual(mockConversations);
  });
});
```

## Coverage Configuration

### Backend Coverage (pytest-cov)

```ini
# pytest.ini
[pytest]
addopts = --cov=db --cov=auth --cov=pipeline --cov-report=term-missing --cov-report=xml --cov-report=html
```

### Frontend Coverage (Jest)

```javascript
// jest.config.js
collectCoverageFrom: [
  'src/**/*.{ts,tsx}',
  '!src/**/*.d.ts',
  '!src/**/index.{ts,tsx}',
  '!src/main.tsx',
  '!src/registry/**',
],
coverageThreshold: {
  global: {
    branches: 75,
    functions: 75,
    lines: 75,
    statements: 75
  }
}
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI pipeline includes:

1. **Backend Tests**: Python tests with PostgreSQL
2. **Frontend Tests**: Jest tests with coverage
3. **Security Scan**: Trivy vulnerability scanning
4. **Code Quality**: Linting, formatting, type checking
5. **Integration Tests**: E2E tests with Playwright
6. **Performance Tests**: Lighthouse CI (production only)

### Running CI Locally

```bash
# Backend tests (requires Docker for PostgreSQL)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:14
cd apps/backend
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/webplus_test
pytest --cov=. --cov-report=xml

# Frontend tests
cd apps/frontend
npm test -- --coverage --watchAll=false
npm run lint
npm run typecheck
npm run build
```

## Best Practices

### 1. Test Structure

- **Arrange, Act, Assert**: Clear test structure
- **Descriptive Names**: Test names explain what is being tested
- **Single Responsibility**: Each test verifies one thing
- **Test Categories**: Use markers (unit, integration, slow)

### 2. Mock Strategy

- **External Services**: Always mock external APIs
- **Database**: Use test database, not production
- **Time**: Mock Date.now() for consistent tests
- **File System**: Mock file operations when possible

### 3. Test Data

- **Factories**: Use factory functions for test data
- **Isolation**: Each test should be independent
- **Cleanup**: Automatically clean up after tests
- **Realistic Data**: Use faker for realistic test data

### 4. Assertions

- **Specific**: Assert exact values when possible
- **Accessible**: Test accessibility features
- **Error Cases**: Test error handling and edge cases
- **User Perspective**: Test from user's point of view

## Troubleshooting

### Common Issues

**Backend Tests**

```bash
# Database connection issues
export DATABASE_URL=sqlite+aiosqlite:///:memory:

# Import errors
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Async test issues
pytest-asyncio>=0.21.1
```

**Frontend Tests**

```bash
# Module resolution
# Check moduleNameMapper in jest.config.js

# Mock issues
# Reset mocks in beforeEach blocks

# TypeScript errors
# Update @types packages
```

### Performance

**Speed Up Tests**

```bash
# Backend: Use SQLite for faster tests
DATABASE_URL=sqlite+aiosqlite:///:memory:

# Frontend: Run tests in parallel
npm test -- --maxWorkers=4

# Skip slow tests in development
pytest -m "not slow"
```

### Debugging

**Backend Debug**

```bash
# Debug specific test
pytest -xvs tests/test_specific.py::test_function

# Debug with pdb
pytest --pdb tests/test_specific.py
```

**Frontend Debug**

```bash
# Debug in browser
npm run test:ui

# Verbose output
npm test -- --verbose

# Debug specific test
npm test Button.test.tsx
```

## Code Quality Gates

### Required Coverage

- **Backend**: 90% line coverage
- **Frontend**: 75% line coverage
- **Critical Paths**: 95% coverage (auth, payments)

### Quality Checks

- **No TODO/FIXME**: In production code
- **Type Safety**: All TypeScript strict mode
- **Security**: No high/critical vulnerabilities
- **Performance**: Lighthouse score > 90

## Integration with IDEs

### VS Code

Install extensions:
- Python Test Explorer
- Jest Runner
- Coverage Gutters
- SonarLint

### WebStorm

- Built-in Jest integration
- Python test runner
- Coverage display
- Code quality inspections

## Monitoring and Reporting

### Coverage Reports

- **Backend**: `apps/backend/htmlcov/index.html`
- **Frontend**: `apps/frontend/coverage/lcov-report/index.html`
- **Combined**: Codecov.io dashboard

### Test Reports

- **JUnit XML**: For CI integration
- **HTML Reports**: For detailed analysis
- **Slack/Discord**: Automated notifications

---

This testing setup ensures high code quality, catches regressions early, and provides confidence for rapid development and deployment of the Web+ platform.