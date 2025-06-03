# Phase 1: AI Development Prompts

## 🤖 How to Use These Prompts

1. Copy the exact prompt
2. Provide any requested context
3. Review AI output carefully
4. Test the implementation
5. Iterate if needed

## 🔧 Database Fix Prompts

### Prompt 1: Fix SQLite Connection Error
```
I'm getting this error: "Can't load plugin: sqlalchemy.dialects:sqlite.sqlite"

Current database.py configuration:
[paste current database.py content]

Requirements:
1. Fix the SQLite dialect loading error
2. Ensure async SQLite support works
3. Maintain compatibility with PostgreSQL for production
4. Add proper error handling
5. Include connection testing

Please provide the corrected database.py file and any additional dependencies needed.
```

### Prompt 2: Create Database Migration Script
```
Create a complete database initialization and migration script for Web+ that:

1. Checks if database exists
2. Creates all tables from these models: [paste models.py]
3. Adds initial seed data for testing
4. Handles both SQLite (dev) and PostgreSQL (prod)
5. Includes rollback capability
6. Has proper logging

Include error handling and make it idempotent (safe to run multiple times).
```

## 🔄 TypeScript Migration Prompts

### Prompt 3: Complete TypeScript Migration
```
I need to complete the TypeScript migration for Web+. Current status:
- Mixed .js and .tsx files exist
- Some imports are broken
- Type definitions are incomplete

Tasks:
1. Analyze these files: [list files]
2. Convert all .js to .tsx
3. Add proper type definitions
4. Fix all import statements
5. Ensure no any types remain

For each file, provide:
- The converted TypeScript code
- Explanation of type choices
- Any potential issues found
```

### Prompt 4: Create Type Definitions
```
Create comprehensive TypeScript type definitions for Web+ API:

Based on this OpenAPI spec: [paste API endpoints]
And these database models: [paste models.py]

Generate:
1. API request/response types
2. Model interfaces
3. Utility types
4. Type guards
5. Enum definitions

Ensure all types are:
- Strictly typed (no any)
- Well documented
- Following naming conventions
- Exportable as a package
```

## 🧪 Testing Setup Prompts

### Prompt 5: Backend Test Suite
```
Create a comprehensive test suite for the Web+ backend:

Current structure:
[paste backend file structure]

Requirements:
1. Pytest configuration with async support
2. Test fixtures for database and models
3. Unit tests for all CRUD operations
4. Integration tests for all API endpoints
5. Mock external services (Ollama)
6. Coverage reporting setup

Include:
- conftest.py with fixtures
- Example tests for each category
- GitHub Actions CI configuration
- Documentation for running tests
```

### Prompt 6: Frontend Test Suite
```
Set up complete frontend testing for Web+:

Tech stack:
- React 19
- TypeScript
- Vite
- Tailwind CSS

Create:
1. Jest configuration for Vite
2. React Testing Library setup
3. Component test examples
4. Hook testing utilities
5. API mocking strategy
6. Coverage configuration

Provide working examples for:
- Component with props
- Component with state
- Custom hook
- API integration
- User interaction
```

## 🔌 Integration Prompts

### Prompt 7: Fix Frontend-Backend Communication
```
The frontend isn't properly communicating with the backend. 

Current setup:
- Frontend: [paste API client code]
- Backend: [paste CORS configuration]
- Auth: JWT + API keys

Issues:
- CORS errors
- Authentication not working
- WebSocket connection fails

Fix:
1. CORS configuration
2. Authentication flow
3. Error handling
4. Request/response logging
5. WebSocket setup

Provide complete working code for both frontend and backend.
```

### Prompt 8: Implement Real-time Updates
```
Implement WebSocket-based real-time updates for model status:

Requirements:
1. Backend WebSocket endpoint for model status
2. Frontend WebSocket client with reconnection
3. Real-time model status updates
4. Connection state management
5. Error handling and fallbacks

Current code:
[paste relevant code]

Provide:
- Complete WebSocket implementation
- State management solution
- UI components for status display
- Testing approach
```

## 🛠️ Refactoring Prompts

### Prompt 9: Code Quality Improvement
```
Refactor this code for better quality:
[paste code section]

Requirements:
1. Follow SOLID principles
2. Improve error handling
3. Add proper logging
4. Optimize performance
5. Enhance readability

For each change:
- Explain why it's better
- Show before/after
- Note any tradeoffs
- Suggest tests needed
```

### Prompt 10: Performance Optimization
```
Analyze and optimize this code for performance:
[paste code section]

Focus on:
1. Database query optimization
2. Caching opportunities
3. Async/await usage
4. Memory efficiency
5. Bundle size (frontend)

Provide:
- Specific optimizations
- Performance impact estimates
- Implementation code
- Benchmark approach
```

## 🐛 Debugging Prompts

### Prompt 11: Debug Database Issues
```
I'm experiencing these database issues:
[paste error logs]

Current configuration:
[paste database.py and models.py]

Steps to reproduce:
[list steps]

Please:
1. Identify root cause
2. Provide fix
3. Explain why it happened
4. Suggest prevention measures
5. Add appropriate logging
```

### Prompt 12: Fix TypeScript Errors
```
Getting these TypeScript errors:
[paste errors]

Code context:
[paste relevant code]

Fix:
1. Resolve all type errors
2. Improve type safety
3. Add missing types
4. Document complex types
5. Ensure no any types
```

## 📋 Validation Prompts

### Prompt 13: Security Audit
```
Perform a security audit on this code:
[paste authentication/API code]

Check for:
1. SQL injection
2. XSS vulnerabilities
3. Authentication bypasses
4. Rate limiting issues
5. Data exposure risks

Provide:
- Vulnerabilities found
- Severity ratings
- Fixes for each issue
- Best practices
- Testing approach
```

### Prompt 14: Final Phase Validation
```
Validate Phase 1 completion checklist:

Requirements:
[paste phase 1 success criteria]

Current state:
[describe current implementation]

Verify:
1. All features work as expected
2. Tests pass with >90% coverage
3. No critical bugs
4. Documentation complete
5. Performance acceptable

Provide:
- Detailed validation results
- Any gaps found
- Remediation steps
- Sign-off recommendation
```
