# Phase 4: AI Development Prompts

## 🤖 AI Provider Integration Prompts

### Prompt 1: OpenAI Integration
```
Implement comprehensive OpenAI integration:

Requirements:
1. Support all GPT models
2. Streaming responses
3. Function calling
4. Image generation (DALL-E)
5. Audio transcription (Whisper)
6. Embeddings API
7. Fine-tuning support

Current model structure: [paste Model interface]

Create:
- OpenAI provider class
- Model configuration UI
- Streaming handler
- Cost tracking
- Error handling
- Rate limit management

Include proper TypeScript types.
```

### Prompt 2: Provider Abstraction Layer
```
Design a unified provider interface:

Providers to support:
- OpenAI
- Anthropic
- Google AI
- Cohere
- Hugging Face

Common interface:
interface AIProvider {
  listModels(): Promise<Model[]>
  chat(params: ChatParams): Promise<ChatResponse>
  stream(params: ChatParams): AsyncGenerator<Token>
  embed(text: string): Promise<number[]>
  getUsage(): Promise<Usage>
}

Requirements:
1. Provider registration
2. Capability detection
3. Automatic fallbacks
4. Cost normalization
5. Response standardization
6. Error mapping

Make it extensible for new providers.
```

### Prompt 3: Multi-Modal Support
```
Implement multi-modal AI capabilities:

Support:
1. Text input/output
2. Image input (vision)
3. Image generation
4. Audio transcription
5. Audio generation
6. Video analysis

For each provider that supports it:
- Unified interface
- Format conversion
- Size optimization
- Preview generation
- Storage handling
- Cost calculation

Handle provider differences gracefully.
```

## 🔧 Development Tools Prompts

### Prompt 4: GitHub Integration
```
Build comprehensive GitHub integration:

Features:
1. OAuth2 authentication
2. Repository management
3. Issue creation/updates
4. PR automation
5. Code search
6. Webhook handling
7. Actions triggering

Use Octokit. Implement:
- Repository browser UI
- Issue creation from pipeline
- PR review automation
- Code snippet extraction
- Commit creation
- Branch management
- Release automation

Include error handling and rate limits.
```

### Prompt 5: CI/CD Integration
```
Create CI/CD pipeline triggers:

Support:
1. GitHub Actions
2. GitLab CI
3. Jenkins
4. CircleCI

Features:
- Trigger builds
- Monitor status
- Retrieve logs
- Parse test results
- Deploy commands
- Rollback support

Build generic interface with provider adapters.
```

## 📧 Communication Prompts

### Prompt 6: Slack Integration
```
Implement Slack integration:

Features:
1. OAuth2 flow
2. Channel posting
3. DM support
4. Slash commands
5. Interactive buttons
6. Scheduled messages
7. File uploads

Pipeline integration:
- Send notifications
- Await approvals
- Collect feedback
- Share results
- Error alerts
- Daily summaries

Use Slack SDK with proper error handling.
```

### Prompt 7: Email System
```
Build email integration system:

Providers:
1. SendGrid
2. AWS SES
3. SMTP generic

Features:
- Template management
- Batch sending
- Personalization
- Attachments
- Tracking
- Unsubscribe
- Bounce handling

Create email step for pipelines with:
- Rich HTML editor
- Variable substitution
- Preview mode
- Test sending
- Analytics
```

## ☁️ Storage Integration Prompts

### Prompt 8: Cloud Storage Abstraction
```
Create unified cloud storage interface:

Support:
1. AWS S3
2. Google Cloud Storage
3. Azure Blob Storage

Operations:
- List files/folders
- Upload/download
- Generate signed URLs
- Set permissions
- Manage lifecycle
- Handle large files

Pipeline integration:
- File input step
- File output step
- Batch operations
- Format conversion

Include progress tracking and resumable uploads.
```

### Prompt 9: File Processing Pipeline
```
Implement file processing in pipelines:

Operations:
1. Read from cloud storage
2. Process with AI
3. Transform formats
4. Apply filters
5. Save results

Support:
- Images (resize, convert, analyze)
- Documents (extract, convert, summarize)
- Audio (transcribe, analyze)
- Video (extract frames, analyze)
- Data files (parse, transform)

Handle large files with streaming.
```

## 🔐 Security Prompts

### Prompt 10: Credential Manager
```
Build secure credential management:

Requirements:
1. Encrypted storage
2. Access control
3. Audit logging
4. Rotation reminders
5. Expiry handling
6. Team sharing

Features:
- Add credentials UI
- Permission management
- Usage tracking
- Security scanning
- Backup/restore
- Import/export

Use encryption at rest and in transit.
```

### Prompt 11: OAuth2 Framework
```
Implement OAuth2 framework:

Support:
1. Authorization code flow
2. PKCE extension
3. Refresh tokens
4. Multiple providers
5. Scope management

Features:
- Provider registry
- Token storage
- Auto-refresh
- Error recovery
- Revocation
- Multi-tenant

Create reusable React components.
```

## 🔄 Integration Framework Prompts

### Prompt 12: Webhook System
```
Build robust webhook system:

Features:
1. Endpoint management
2. Signature verification
3. Event routing
4. Retry logic
5. Dead letter queue
6. Event replay

Security:
- HMAC validation
- IP whitelisting
- Rate limiting
- SSL verification
- Replay protection

Include webhook debugging tools.
```

### Prompt 13: API Gateway
```
Create API gateway for integrations:

Features:
1. Request routing
2. Authentication
3. Rate limiting
4. Transformation
5. Caching
6. Monitoring

Patterns:
- Circuit breaker
- Retry with backoff
- Request coalescing
- Response caching
- Load balancing

Build with Express/Fastify.
```

## 📊 Monitoring Prompts

### Prompt 14: Integration Dashboard
```
Build integration monitoring dashboard:

Metrics:
1. API health status
2. Request volumes
3. Error rates
4. Response times
5. Cost tracking
6. Rate limit usage

Visualizations:
- Status indicators
- Time series charts
- Error heatmaps
- Cost breakdown
- Usage trends
- Alerts config

Real-time updates via WebSocket.
```

### Prompt 15: Cost Optimization
```
Implement cost optimization system:

Features:
1. Track API costs
2. Suggest cheaper alternatives
3. Batch operation detection
4. Cache opportunities
5. Usage patterns
6. Budget alerts

Optimizations:
- Model selection
- Batch processing
- Caching strategy
- Rate limit planning
- Provider switching

Generate cost reports and recommendations.
```

## 🐛 Debugging Prompts

### Prompt 16: Integration Debugger
```
Create integration debugging tools:

Features:
1. Request/response logging
2. Header inspection
3. Replay requests
4. Mock responses
5. Latency analysis
6. Error simulation

UI components:
- Request inspector
- Response viewer
- Timeline view
- Error details
- Performance metrics

Similar to browser DevTools Network tab.
```

### Prompt 17: Error Recovery
```
Implement smart error recovery:

Scenarios:
1. API downtime
2. Rate limit exceeded
3. Authentication failure
4. Network timeout
5. Invalid response
6. Quota exceeded

Strategies:
- Automatic retry
- Exponential backoff
- Circuit breaker
- Fallback providers
- Queue and retry
- User notification

Make integrations resilient.
```
