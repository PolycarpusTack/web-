# Phase 5: AI Development Prompts

## 🔐 Enterprise Security Prompts

### Prompt 1: RBAC Implementation
```
Implement comprehensive Role-Based Access Control:

Requirements:
1. Hierarchical roles (Admin, Manager, User, Viewer)
2. Resource-level permissions
3. Dynamic permission checking
4. Role inheritance
5. Custom roles
6. Audit trail

Database schema:
- roles table
- permissions table
- role_permissions junction
- user_roles junction
- resource_permissions

Create:
- Permission decorator for endpoints
- React permission wrapper
- Role management UI
- Permission checking middleware
- Audit logging system

Include TypeScript types and examples.
```

### Prompt 2: SSO Integration
```
Implement Single Sign-On with SAML 2.0:

Support:
1. Okta
2. Auth0
3. Azure AD
4. Google Workspace
5. Custom SAML providers

Features:
- SP-initiated flow
- IdP-initiated flow
- Metadata exchange
- Attribute mapping
- Session management
- Logout flow

Build configuration UI for SSO setup.
```

### Prompt 3: Audit System
```
Build enterprise audit logging system:

Log these events:
1. Authentication (login/logout)
2. Authorization (permission checks)
3. Data access (read/write)
4. Configuration changes
5. API calls
6. Admin actions

Features:
- Structured logging
- User attribution
- IP tracking
- Change diffs
- Search interface
- Export options
- Retention policies

Store in separate audit database.
```

## 👥 Team Collaboration Prompts

### Prompt 4: Team Workspaces
```
Implement multi-tenant workspaces:

Features:
1. Workspace creation/deletion
2. Member invitation system
3. Role assignment
4. Resource isolation
5. Usage quotas
6. Billing separation

Architecture:
- Workspace context in all queries
- Row-level security
- Workspace switching UI
- Cross-workspace sharing
- Admin overview

Handle data isolation carefully.
```

### Prompt 5: Approval Workflows
```
Create approval workflow engine:

Support:
1. Sequential approvals
2. Parallel approvals
3. Conditional routing
4. Escalation rules
5. Delegation
6. Time limits

Components:
- Workflow designer
- Approval dashboard
- Email notifications
- Mobile interface
- Audit trail
- Analytics

Use state machine pattern.
```

### Prompt 6: Usage Analytics Dashboard
```
Build comprehensive analytics for teams:

Metrics:
1. User activity
2. Resource usage
3. Cost breakdown
4. Performance stats
5. Error rates
6. Compliance status

Visualizations:
- Time series charts
- Heat maps
- Sankey diagrams
- Cost allocation
- Trend analysis
- Forecasting

Include drill-down capabilities.
```

## 🚀 Scaling Prompts

### Prompt 7: Redis Caching Layer
```
Implement distributed caching with Redis:

Cache strategies:
1. Query results
2. Session data
3. API responses
4. Computed values
5. Rate limit counters
6. Real-time data

Features:
- Cache-aside pattern
- TTL management
- Cache invalidation
- Pub/sub for updates
- Cache warming
- Memory optimization

Monitor hit rates and performance.
```

### Prompt 8: Background Job System
```
Build scalable job processing with Bull/BullMQ:

Job types:
1. Email sending
2. Report generation
3. Data processing
4. Webhook delivery
5. Scheduled tasks
6. Batch operations

Features:
- Priority queues
- Job scheduling
- Progress tracking
- Retry logic
- Dead letter queue
- Job UI dashboard

Handle failures gracefully.
```

### Prompt 9: Database Optimization
```
Optimize PostgreSQL for scale:

Optimizations:
1. Query analysis and tuning
2. Index optimization
3. Table partitioning
4. Connection pooling
5. Read replicas
6. Materialized views

Implement:
- Query performance monitoring
- Automatic index suggestions
- Partition management
- Replica lag monitoring
- Query caching layer

Target sub-50ms query times.
```

## 🌍 Infrastructure Prompts

### Prompt 10: Kubernetes Deployment
```
Create production Kubernetes setup:

Components:
1. Deployment manifests
2. Service definitions
3. Ingress configuration
4. ConfigMaps/Secrets
5. HPA for auto-scaling
6. Health checks

Features:
- Rolling updates
- Blue-green deployments
- Canary releases
- Resource limits
- Network policies
- Monitoring integration

Use Helm for packaging.
```

### Prompt 11: Monitoring Stack
```
Implement observability with Prometheus/Grafana:

Metrics:
1. Application metrics
2. Business metrics
3. Infrastructure metrics
4. Custom metrics
5. SLI/SLO tracking
6. Error budgets

Dashboards:
- System overview
- User journey
- Performance
- Errors
- Business KPIs
- SLA compliance

Include alerting rules.
```

### Prompt 12: Multi-Region Architecture
```
Design multi-region deployment:

Requirements:
1. Active-active setup
2. Data replication
3. Traffic routing
4. Failover handling
5. Latency optimization
6. Compliance boundaries

Implementation:
- Database replication
- CDN configuration
- GeoDNS setup
- Cross-region backups
- Monitoring per region

Handle split-brain scenarios.
```

## 🛡️ Security Hardening Prompts

### Prompt 13: Security Scanning
```
Implement continuous security scanning:

Scan types:
1. SAST (static analysis)
2. DAST (dynamic testing)
3. Dependency scanning
4. Container scanning
5. Infrastructure scanning
6. Secret detection

Integration:
- CI/CD pipeline
- Pull request checks
- Scheduled scans
- Vulnerability database
- Auto-remediation
- Security dashboard

Use OWASP guidelines.
```

### Prompt 14: Data Encryption
```
Implement encryption everywhere:

Encryption layers:
1. Database encryption
2. File storage encryption
3. Transit encryption
4. Application-level encryption
5. Key rotation
6. HSM integration

Features:
- Transparent encryption
- Field-level encryption
- Encryption key management
- Compliance reporting
- Performance optimization

Follow industry standards.
```

## 📊 Operations Prompts

### Prompt 15: SRE Dashboard
```
Build SRE operations dashboard:

Sections:
1. Service health
2. SLO tracking
3. Incident timeline
4. Error budgets
5. Deployment status
6. On-call schedule

Features:
- Real-time updates
- Historical analysis
- Predictive alerts
- Runbook links
- Incident management
- Post-mortem tracking

Focus on MTTR reduction.
```

### Prompt 16: Disaster Recovery
```
Implement disaster recovery plan:

Components:
1. Automated backups
2. Cross-region replication
3. Failover procedures
4. Data validation
5. Recovery testing
6. Communication plan

Automation:
- Backup scheduling
- Integrity checks
- Recovery drills
- Failover scripts
- Status reporting
- Documentation

Meet RTO < 1hr, RPO < 15min.
```

## ✅ Validation Prompts

### Prompt 17: Load Testing at Scale
```
Perform enterprise load testing:

Scenarios:
1. 10,000 concurrent users
2. 1M requests/minute
3. Large data processing
4. Sustained load
5. Spike testing
6. Chaos engineering

Measure:
- Response times
- Error rates
- Resource usage
- Bottlenecks
- Breaking points
- Recovery time

Use k6 or Gatling.
```

### Prompt 18: Compliance Validation
```
Validate compliance requirements:

Standards:
1. SOC 2 Type II
2. GDPR
3. HIPAA
4. ISO 27001
5. PCI DSS
6. CCPA

Checklist:
- Data protection
- Access controls
- Audit logging
- Encryption
- Incident response
- Documentation

Generate compliance reports.
```
