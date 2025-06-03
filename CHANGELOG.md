# Changelog

All notable changes to the Web+ project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive project documentation including frontend and backend READMEs
- CHANGELOG.md for tracking project changes
- Centralized API client module for frontend
- Reusable UI components (LoadingButton, FilePreviewList, UnifiedMessageInput)
- Custom React hooks (useModelSettings)
- Type guard utilities for runtime type checking
- Shared file preview components for chat interface

### Changed
- Consolidated TypeScript type definitions using api-definitions.ts as single source of truth
- Refactored duplicate code across chat pages (ChatPage, EnhancedChatPage, EnhancedChatWithThreadsPage)
- Updated all API calls to use centralized API client
- Improved component structure with better code reuse
- Migrated to ES modules configuration in package.json

### Fixed
- Resolved 48 TypeScript compilation errors
- Fixed MessageRole enum type issues
- Corrected metadata property naming inconsistencies
- Fixed lucide-react icon imports (FileArchive → Archive)
- Resolved apiClient parameter handling issues

### Security
- Implemented proper authentication token handling in centralized API client
- Added secure file upload validation

## [0.2.0] - 2024-05-30

### Added
- Phase 2 Authentication System
  - JWT-based authentication with refresh tokens
  - API key support for programmatic access
  - User registration and login flows
  - Protected routes and authentication middleware
  - User profile management

- Enhanced Chat Interface
  - Rich message formatting with markdown support
  - File upload and attachment handling
  - Message threading support
  - Context window management
  - Token usage tracking

- Testing Infrastructure
  - Jest configuration for React components
  - Pytest setup for backend API tests
  - Component testing utilities
  - API integration tests

### Changed
- Upgraded to React 19.0.0
- Migrated to SQLAlchemy 2.0 with async support
- Refactored API structure for better organization
- Improved error handling throughout the application

### Fixed
- Database connection pooling issues
- WebSocket connection stability
- File upload size limitations
- CORS configuration for local development

## [0.1.0] - 2024-05-20

### Added
- Initial project setup with monorepo structure
- Basic FastAPI backend with SQLAlchemy
- React frontend with TypeScript and Vite
- Ollama integration for model management
- Basic chat completion functionality
- PostgreSQL database support
- shadcn/ui component library integration
- Tailwind CSS styling
- Basic routing with React Router

### Infrastructure
- Docker support for containerization
- Development environment configuration
- ESLint and Prettier setup
- Git repository initialization

## [0.0.1] - 2024-05-15

### Added
- Project initialization
- Basic project structure
- Initial documentation
- License selection
- README with project overview

[Unreleased]: https://github.com/yourusername/web-plus/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/yourusername/web-plus/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/web-plus/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/yourusername/web-plus/releases/tag/v0.0.1