# Phase 3: AI Development Prompts

## 🔧 Pipeline Engine Prompts

### Prompt 1: Pipeline Execution Engine
```
Design and implement a robust pipeline execution engine:

Requirements:
1. Execute steps in sequence/parallel
2. Pass data between steps
3. Handle errors gracefully
4. Support async operations
5. Track execution state
6. Enable step retry

Pipeline structure:
{
  id: string,
  name: string,
  steps: Step[],
  connections: Connection[],
  variables: Variable[]
}

Implement:
- Execution orchestrator
- Step executor interface
- Context management
- Result storage
- Progress tracking
- Error recovery

Include TypeScript types and Python backend.
```

### Prompt 2: LLM Step Implementation
```
Implement a comprehensive LLM step for pipelines:

Features needed:
1. Multiple model support
2. Prompt templates with variables
3. Streaming responses
4. Token counting
5. Response parsing
6. Retry with backoff

Current model structure: [paste Model interface]

Create:
- LLM step component
- Configuration UI
- Execution logic
- Response handling
- Error management
- Cost tracking

Support variable interpolation: {{variableName}}
```

### prompt 3: Code Execution Step
```
Build a secure code execution step:

Requirements:
1. Python and JavaScript support
2. Sandboxed execution
3. Variable access (read/write)
4. Output capture
5. Error handling
6. Timeout control

Security considerations:
- No file system access
- Limited memory/CPU
- No network access
- Safe built-ins only

Implement:
- Code editor component
- Execution backend
- Variable binding
- Output formatting
- Security sandbox
```

## 🎨 Visual Builder Prompts

### Prompt 4: React Flow Pipeline Builder
```
Create a visual pipeline builder using React Flow:

Requirements:
1. Drag-and-drop nodes from palette
2. Connect nodes with validation
3. Pan/zoom with minimap
4. Node grouping/ungrouping
5. Copy/paste support
6. Undo/redo functionality

Node types:
- LLM (multiple inputs/outputs)
- Code (single input/output)
- API (configurable I/O)
- Transform (single I/O)
- Condition (branching)

Implement:
- Custom node components
- Connection validation
- Layout algorithm
- Keyboard shortcuts
- Touch support
- Performance optimization

Use React Flow with custom styling.
```

### Prompt 5: Node Connection System
```
Implement intelligent node connections:

Features:
1. Type-safe connections
2. Auto-routing around nodes
3. Connection previews
4. Multi-select connections
5. Connection labels
6. Animated data flow

Connection rules:
- Output → Input only
- Type compatibility check
- No circular dependencies
- Multiple inputs allowed
- Single output branching

Build:
- Connection validator
- Path calculation
- Interaction handlers
- Visual feedback
- Error indicators
```

### Prompt 6: Real-time Validation
```
Create comprehensive pipeline validation:

Validate:
1. Connection compatibility
2. Required fields
3. Circular dependencies
4. Resource requirements
5. Cost estimates
6. Execution time estimates

Provide:
- Inline error messages
- Visual error indicators
- Validation panel
- Quick fixes
- Warning vs errors
- Validation API

Real-time feedback as user builds.
```

## 🚀 Advanced Features Prompts

### Prompt 7: Conditional Logic System
```
Implement visual conditional logic:

Support:
1. If/else branches
2. Switch statements
3. Loop constructs
4. Boolean operators
5. Comparison operators
6. Merge points

Visual representation:
- Diamond decision nodes
- Branch paths
- Loop indicators
- Merge nodes
- Condition labels

Include:
- Visual condition builder
- Expression editor
- Test data preview
- Branch highlighting
- Execution path preview
```

### Prompt 8: Data Transformation UI
```
Build visual data transformation:

Features:
1. Drag-drop field mapping
2. JSONPath expressions
3. Function library
4. Preview with sample data
5. Type conversions
6. Custom functions

Transform types:
- Extract fields
- Rename keys
- Filter arrays
- Aggregate data
- Format strings
- Parse dates

Create intuitive UI for non-programmers.
```

### Prompt 9: Pipeline Templates
```
Implement pipeline template system:

Template features:
1. Parameterized pipelines
2. Template marketplace
3. Categories/tags
4. Preview mode
5. One-click deploy
6. Customization wizard

Common templates:
- Blog post generator
- Code reviewer
- Data analyzer
- Report builder
- Email composer
- API integrator

Include:
- Template creator
- Parameter definition
- Documentation
- Version control
- Rating system
```

## 📊 Management Prompts

### Prompt 10: Execution Monitoring
```
Create pipeline execution monitor:

Display:
1. Live execution status
2. Step-by-step progress
3. Timing information
4. Resource usage
5. Live logs
6. Result preview

Features:
- Pause/resume execution
- Step debugging
- Variable inspection
- Error details
- Performance metrics
- Export logs

Use WebSockets for real-time updates.
```

### Prompt 11: Pipeline Analytics
```
Build analytics dashboard for pipelines:

Metrics:
1. Execution count
2. Success/failure rates
3. Average duration
4. Cost analysis
5. Popular pipelines
6. Error patterns

Visualizations:
- Time series charts
- Success rate gauge
- Cost breakdown
- Usage heatmap
- Error frequency
- Performance trends

Include filtering, date ranges, export.
```

## 🧪 Testing Prompts

### Prompt 12: Pipeline Test Framework
```
Create testing framework for pipelines:

Test types:
1. Unit tests for steps
2. Integration tests
3. End-to-end tests
4. Performance tests
5. Error injection
6. Load testing

Features:
- Test data management
- Mock services
- Assertion library
- Test runner UI
- Coverage reports
- CI/CD integration

Make testing accessible to non-developers.
```

### Prompt 13: Visual Testing
```
Implement visual regression testing:

Test areas:
1. Node rendering
2. Connection paths
3. Zoom/pan behavior
4. Drag interactions
5. Layout consistency
6. Animation smoothness

Tools:
- Screenshot comparison
- Interaction recording
- Performance profiling
- Cross-browser testing
- Responsive testing

Automate visual quality assurance.
```

## 🐛 Debugging Prompts

### Prompt 14: Pipeline Debugger
```
Build interactive pipeline debugger:

Features:
1. Breakpoints on steps
2. Step-through execution
3. Variable watch
4. Execution timeline
5. Error diagnosis
6. Performance profiling

UI elements:
- Debug toolbar
- Variable inspector
- Call stack view
- Log console
- Breakpoint manager
- Time travel

Similar to browser DevTools.
```

### Prompt 15: Error Recovery System
```
Implement smart error recovery:

Recovery strategies:
1. Automatic retry
2. Fallback steps
3. Partial execution
4. Manual intervention
5. State restoration
6. Notification system

For each error type:
- Suggested fixes
- Recovery options
- Prevention tips
- Documentation links
- Support contact

Make pipelines resilient.
```

## ✅ Validation Prompts

### Prompt 16: Pipeline Complexity Analysis
```
Analyze pipeline complexity:

Metrics:
1. Cyclomatic complexity
2. Execution paths
3. Resource requirements
4. Cost estimates
5. Risk assessment
6. Optimization suggestions

Provide:
- Complexity score
- Optimization tips
- Risk warnings
- Cost breakdown
- Performance impact
- Simplification options

Help users build efficient pipelines.
```

### Prompt 17: Production Readiness Check
```
Validate pipeline for production:

Checklist:
1. Error handling complete
2. Timeouts configured
3. Rate limits set
4. Secrets secured
5. Monitoring enabled
6. Documentation complete

Automated checks:
- Security scan
- Performance test
- Cost analysis
- Dependency check
- Version compatibility
- Scale testing

Generate production readiness report.
```
