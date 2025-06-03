# Web+ Frontend Application

## Overview

The Web+ frontend is a modern React application built with TypeScript, providing a comprehensive interface for managing and interacting with large language models, particularly Ollama models. It features a rich chat interface, model management, automated AI pipelines, and robust authentication.

## Architecture

### Technology Stack

- **React 19.0.0** - UI framework
- **TypeScript** - Type safety and better developer experience
- **Vite** - Build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Component library built on Radix UI
- **React Router** - Client-side routing
- **Axios** - HTTP client for API communication
- **Lucide React** - Icon library

### Project Structure

```
src/
├── api/              # API client modules
├── app/              # Application pages and components
├── components/       # Reusable UI components
│   ├── auth/        # Authentication components
│   ├── chat/        # Chat interface components
│   └── ui/          # Base UI components (shadcn/ui)
├── config/          # Configuration files
├── hooks/           # Custom React hooks
├── lib/             # Utility libraries and contexts
├── pages/           # Page components
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

### Key Features

- **Authentication System**: JWT-based auth with login/register flows
- **Chat Interface**: Multiple chat views with threading support
- **Model Management**: View and control Ollama models
- **File Handling**: Upload and analyze files in conversations
- **Pipeline Builder**: Visual pipeline creation and execution
- **Real-time Updates**: WebSocket support for live updates
- **Dark Mode**: Full theme support with mode switching

## Getting Started

### Prerequisites

- Node.js 18+ and npm/pnpm
- Backend API running on http://localhost:8002

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at http://localhost:5173

### Environment Configuration

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8002/api
VITE_WS_URL=ws://localhost:8002/ws
```

## Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler check
npm test             # Run tests
```

### Code Style

- Follow TypeScript best practices
- Use functional components with hooks
- Implement proper error boundaries
- Use semantic HTML elements
- Follow accessibility guidelines (WCAG 2.1)

### Component Guidelines

1. **Creating Components**
   - Place in appropriate directory under `src/components/`
   - Use TypeScript interfaces for props
   - Export from index files for clean imports
   - Include JSDoc comments for complex components

2. **Using UI Components**
   - Prefer shadcn/ui components over custom implementations
   - Follow the established pattern for component composition
   - Maintain consistent styling with Tailwind classes

3. **State Management**
   - Use React Context for global state (auth, theme)
   - Use local state for component-specific data
   - Consider React Query for server state management

### API Integration

All API calls should go through the centralized API client:

```typescript
import { api } from '@/api';

// Example usage
const response = await api.conversations.create({
  title: "New Chat",
  model_id: "llama2:latest"
});
```

### Testing

Tests are located alongside components in `__tests__` directories:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

### Building for Production

```bash
# Create production build
npm run build

# Preview production build locally
npm run preview
```

Build output will be in the `dist/` directory.

## Deployment

### Docker Deployment

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Environment Variables

Production environment variables:

- `VITE_API_URL` - Backend API URL
- `VITE_WS_URL` - WebSocket URL
- `VITE_ENABLE_ANALYTICS` - Enable analytics (optional)

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Ensure backend is running on correct port
   - Check CORS configuration
   - Verify environment variables

2. **Build Errors**
   - Clear node_modules and reinstall
   - Check for TypeScript errors with `npm run type-check`
   - Ensure all imports are correct

3. **Style Issues**
   - Run `npx tailwindcss init` if Tailwind not working
   - Check PostCSS configuration
   - Verify Tailwind config includes all content paths

## Contributing

See the main [CONTRIBUTING.md](../../CONTRIBUTING.md) for general guidelines.

### Frontend-Specific Guidelines

1. Create feature branches from `main`
2. Write tests for new components
3. Update TypeScript types as needed
4. Ensure no TypeScript or ESLint errors
5. Update relevant documentation

## License

This project is part of Web+ and follows the same license terms.