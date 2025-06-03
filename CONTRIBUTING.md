# Contributing to Web+

Thank you for your interest in contributing to Web+! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing opinions and experiences
- Show empathy towards other community members

## Getting Started

1. **Fork the Repository**
   ```bash
   # Fork via GitHub UI, then clone your fork
   git clone https://github.com/yourusername/web-plus.git
   cd web-plus
   ```

2. **Set Up Development Environment**
   ```bash
   # Backend setup
   cd apps/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Frontend setup
   cd ../frontend
   npm install
   ```

3. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- Clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, browser, versions)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- Clear and descriptive title
- Detailed description of the proposed enhancement
- Use cases and examples
- Potential implementation approach (if you have ideas)

### Your First Code Contribution

1. **Find an Issue**
   - Look for issues labeled `good first issue` or `help wanted`
   - Comment on the issue to indicate you're working on it

2. **Understand the Codebase**
   - Read relevant documentation
   - Explore the code structure
   - Run the application locally

3. **Make Your Changes**
   - Follow the style guidelines
   - Write tests for new functionality
   - Update documentation as needed

## Development Process

### 1. Setting Up Your Development Environment

See the [Getting Started](#getting-started) section and the individual README files:
- [Frontend README](apps/frontend/README.md)
- [Backend README](apps/backend/README.md)

### 2. Making Changes

- Keep changes focused and atomic
- One feature or fix per pull request
- Write descriptive commit messages
- Add tests for new functionality
- Update documentation

### 3. Running Tests

```bash
# Backend tests
cd apps/backend
pytest

# Frontend tests
cd apps/frontend
npm test
```

### 4. Code Quality Checks

```bash
# Backend linting
cd apps/backend
ruff check .
mypy .

# Frontend linting
cd apps/frontend
npm run lint
npm run type-check
```

## Style Guidelines

### Python (Backend)

- Follow PEP 8
- Use type hints for function parameters and returns
- Maximum line length: 88 characters (Black formatter)
- Use async/await for asynchronous operations

```python
async def get_user_by_id(user_id: int) -> User | None:
    """Get a user by their ID.
    
    Args:
        user_id: The ID of the user to retrieve
        
    Returns:
        The user object if found, None otherwise
    """
    return await db.get(User, user_id)
```

### TypeScript/React (Frontend)

- Use functional components with hooks
- Define interfaces for component props
- Use proper TypeScript types (avoid `any`)
- Follow ESLint configuration

```typescript
interface UserCardProps {
  user: User;
  onEdit?: (user: User) => void;
}

export function UserCard({ user, onEdit }: UserCardProps) {
  return (
    <Card>
      <CardHeader>{user.name}</CardHeader>
      {onEdit && (
        <Button onClick={() => onEdit(user)}>Edit</Button>
      )}
    </Card>
  );
}
```

### General Guidelines

- Use meaningful variable and function names
- Write self-documenting code
- Add comments for complex logic
- Keep functions small and focused
- Follow DRY (Don't Repeat Yourself) principle

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Examples
```bash
feat(auth): add password reset functionality

fix(chat): resolve message ordering issue in threads

docs(api): update endpoint documentation for file uploads

refactor(frontend): consolidate duplicate API calls
```

## Pull Request Process

1. **Before Submitting**
   - Ensure all tests pass
   - Run linters and fix any issues
   - Update documentation
   - Add entries to CHANGELOG.md if significant

2. **Pull Request Title**
   - Use conventional commit format
   - Be clear and descriptive

3. **Pull Request Description**
   - Link related issues using "Fixes #123" or "Relates to #456"
   - Describe what changes were made and why
   - Include screenshots for UI changes
   - List any breaking changes

4. **Review Process**
   - Address reviewer feedback promptly
   - Keep discussions focused and professional
   - Update your branch with main if needed

5. **After Approval**
   - Squash commits if requested
   - Ensure CI passes
   - Project maintainers will merge

## Testing

### Writing Tests

- Write tests for all new functionality
- Follow the existing test patterns
- Aim for high code coverage
- Test edge cases and error conditions

### Backend Testing
```python
# Example test
async def test_create_user(client: AsyncClient):
    response = await client.post("/users", json={
        "username": "testuser",
        "email": "test@example.com"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
```

### Frontend Testing
```typescript
// Example test
describe('UserCard', () => {
  it('displays user name', () => {
    const user = { id: 1, name: 'John Doe' };
    render(<UserCard user={user} />);
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});
```

## Documentation

### When to Update Documentation

- Adding new features
- Changing existing functionality
- Modifying API endpoints
- Updating configuration options
- Adding new dependencies

### Documentation Standards

- Use clear and concise language
- Include code examples
- Keep documentation up-to-date
- Use proper markdown formatting
- Add diagrams where helpful

### Where to Document

- **Code**: Inline comments and docstrings
- **API**: Update api-reference.md
- **Features**: Update user guides
- **Architecture**: Update developer guides
- **Changes**: Update CHANGELOG.md

## Community

### Getting Help

- Check existing documentation
- Search through issues and discussions
- Ask questions in discussions
- Join our community chat (if available)

### Helping Others

- Answer questions in discussions
- Review pull requests
- Improve documentation
- Share your experiences

### Recognition

We value all contributions, including:
- Code contributions
- Bug reports
- Documentation improvements
- Helping other users
- Spreading the word about the project

## License

By contributing to Web+, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Web+! Your efforts help make this project better for everyone.