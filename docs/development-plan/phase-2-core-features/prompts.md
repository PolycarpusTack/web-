# Phase 2: AI Development Prompts

## 🎨 Model Management Prompts

### Prompt 1: Advanced Model Search
```
Implement an advanced search system for AI models with these features:

Current models structure: [paste Model type definition]

Requirements:
1. Full-text search across name, description, tags
2. Filter by: provider, capabilities, context size, cost
3. Sort by: name, date added, popularity, cost
4. Fuzzy matching for typos
5. Search suggestions/autocomplete
6. Recent searches history

Provide:
- Backend search endpoint with query builder
- Frontend search component with filters
- Debounced search input
- Clear UI for active filters
- Performance optimizations for large datasets
```

### Prompt 2: Model Analytics Dashboard
```
Create a comprehensive analytics dashboard for model usage:

Data available:
- Usage logs with timestamps, tokens, duration
- User information
- Model performance metrics
- Cost data

Build:
1. Dashboard with multiple chart types
2. Time range selector (day/week/month/custom)
3. Model comparison view
4. Cost analysis with projections
5. Export functionality
6. Real-time updates via WebSocket

Use Recharts for visualization. Include:
- Usage over time (line chart)
- Top models (bar chart)
- Cost breakdown (pie chart)
- Performance metrics (scatter plot)
- Usage heatmap
```

## 💬 Chat System Prompts

### Prompt 3: Streaming Chat Implementation
```
Implement streaming chat responses with Server-Sent Events:

Current setup: [paste current chat implementation]

Requirements:
1. Backend SSE endpoint for streaming
2. Frontend EventSource handling
3. Progressive message rendering
4. Cancel streaming ability
5. Error handling and retry
6. Fallback to polling if SSE fails

Include:
- Token-by-token streaming
- Markdown rendering during stream
- Code syntax highlighting
- Stream progress indicator
- Smooth animations
```

### Prompt 4: Conversation Management System
```
Build a complete conversation management system:

Requirements:
1. Conversation list with search/filter
2. Folder organization
3. Branching conversations
4. Conversation sharing with permissions
5. Templates for common conversations
6. Bulk operations

Database schema: [paste conversation models]

Implement:
- RESTful API for all operations
- Optimistic UI updates
- Drag-and-drop for organization
- Context menu for quick actions
- Keyboard shortcuts
- Undo/redo functionality
```

### Prompt 5: Message Export System
```
Create a comprehensive export system for conversations:

Export formats needed:
1. Markdown with metadata
2. PDF with formatting
3. JSON for data portability
4. HTML for web viewing

Features:
- Single message export
- Full conversation export
- Bulk export with filters
- Custom templates
- Scheduled exports
- Export history

Include code highlighting, images, and formatting preservation.
```

## 📊 Real-time Monitoring Prompts

### Prompt 6: WebSocket Manager
```
Implement a robust WebSocket management system:

Requirements:
1. Automatic reconnection with exponential backoff
2. Connection state management
3. Message queuing while disconnected
4. Heartbeat/ping-pong
5. Multiple subscription management
6. TypeScript types for all messages

Current WebSocket usage: [paste current implementation]

Provide:
- WebSocket manager class
- React hooks for WebSocket
- Connection status component
- Reconnection UI
- Error handling
- Testing utilities
```

### Prompt 7: Real-time Dashboard
```
Create a real-time monitoring dashboard using WebSockets:

Metrics to display:
- Active models status
- Current API requests
- Memory/CPU usage
- Active users
- Request latency
- Error rates

Requirements:
1. Auto-updating charts (every 1s)
2. Historical view (last hour)
3. Alert thresholds
4. Metric drill-down
5. Export capabilities

Use D3.js or Recharts. Optimize for performance with:
- Efficient data structures
- Canvas rendering for high-frequency updates
- Data sampling for large datasets
```

## 🎯 UI/UX Enhancement Prompts

### Prompt 8: Responsive Design Audit
```
Audit and fix responsive design issues:

Current breakpoints: [paste current setup]

Tasks:
1. Test all pages on mobile/tablet/desktop
2. Fix navigation on mobile
3. Optimize touch targets (48px minimum)
4. Implement swipe gestures
5. Fix table layouts for mobile
6. Add responsive images

Provide:
- List of issues found
- CSS/component fixes
- New responsive utilities
- Testing checklist
```

### Prompt 9: Loading States System
```
Implement comprehensive loading states:

Create:
1. Skeleton screens for all major components
2. Progress indicators for long operations
3. Optimistic updates where appropriate
4. Loading placeholders
5. Shimmer effects
6. Stagger animations

Current components: [list main components]

Provide:
- Reusable skeleton components
- Loading state management
- Animation utilities
- Usage examples
- Performance considerations
```

### Prompt 10: Keyboard Shortcuts
```
Implement a comprehensive keyboard shortcut system:

Required shortcuts:
- Navigation (j/k for up/down)
- Actions (n for new, e for edit)
- Search (/ to focus search)
- Modal management (ESC to close)
- Help (? for shortcuts modal)

Build:
1. Shortcut registration system
2. Conflict detection
3. Customization UI
4. Context-aware shortcuts
5. Visual hints in UI
6. Accessibility compliance

Include React hooks and proper cleanup.
```

## 🚀 Performance Optimization Prompts

### Prompt 11: Frontend Performance Audit
```
Perform comprehensive frontend performance optimization:

Current issues:
- Bundle size: [current size]
- First paint: [current time]
- Lighthouse score: [current score]

Optimize:
1. Implement code splitting by route
2. Lazy load heavy components
3. Optimize images with next-gen formats
4. Add resource hints (preconnect, prefetch)
5. Implement service worker
6. Reduce JavaScript execution time

Provide:
- Specific optimizations with impact
- Before/after metrics
- Implementation code
- Testing approach
```

### Prompt 12: Backend Query Optimization
```
Optimize database queries for performance:

Problem queries: [paste slow queries]

Tasks:
1. Add appropriate indexes
2. Optimize N+1 queries
3. Implement query result caching
4. Add database connection pooling
5. Optimize pagination
6. Add query analysis logging

Provide:
- Optimized queries with explanations
- Index creation scripts
- Caching strategy
- Performance benchmarks
```

## 🐛 Debugging & Refactoring Prompts

### Prompt 13: WebSocket Debugging
```
Debug WebSocket connection issues:

Issues:
- Connections dropping randomly
- Messages not delivered
- Memory leaks suspected

Current implementation: [paste code]

Diagnose and fix:
1. Connection stability
2. Message delivery guarantees
3. Memory leak detection
4. Error handling
5. Logging improvements

Provide debugging tools and fixes.
```

### Prompt 14: Performance Profiling
```
Profile and fix performance bottlenecks:

Areas to profile:
1. React component renders
2. API response times
3. Database query performance
4. WebSocket message processing
5. Memory usage patterns

Tools to use:
- React DevTools Profiler
- Chrome DevTools Performance
- Backend APM tools

Provide:
- Profiling results
- Identified bottlenecks
- Optimization solutions
- Before/after comparisons
```

## ✅ Phase 2 Validation Prompts

### Prompt 15: Feature Completeness Check
```
Validate Phase 2 feature completeness:

Required features: [paste feature list]

For each feature, verify:
1. Fully implemented
2. Tested (unit + integration)
3. Documented
4. Performs well
5. Accessible
6. Error handling complete

Provide:
- Feature checklist with status
- Any gaps found
- Remediation plan
- Test results summary
```

### Prompt 16: Production Readiness Audit
```
Audit codebase for production readiness:

Check:
1. Security vulnerabilities
2. Performance issues
3. Error handling
4. Logging completeness
5. Configuration management
6. Deployment readiness

Current state: [describe implementation]

Provide:
- Detailed audit results
- Critical issues found
- Recommended fixes
- Production checklist
- Deployment guide
```
