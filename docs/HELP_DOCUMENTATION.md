# Web+ Help

## Quick Reference
- **Purpose**: Enterprise AI model management and chat platform
- **Version**: 1.0.0
- **Last Updated**: January 2025

## Getting Started
1. Login with your credentials at `/login`
2. Navigate to Models page to view available AI models
3. Start a chat by clicking "Chat" in the navigation
4. Select a model and type your message
5. View the response in real-time as it streams

## Features

### Model Management
**What it does:** View and manage AI models from multiple providers including OpenAI, Anthropic, Google, Cohere, and local Ollama models.
**How to use:**
1. Navigate to Models page from main menu
2. Use search bar to filter by name or provider
3. Click Start/Stop buttons for Ollama models
**Note:** Only local Ollama models can be started/stopped

### Chat Interface
**What it does:** Interactive chat with AI models featuring real-time streaming responses and markdown rendering.
**How to use:**
1. Select a model from the dropdown menu
2. Type your message in the input field
3. Press Enter or click Send to submit
**Note:** Use Shift+Enter for multi-line messages

### File Management
**What it does:** Upload and analyze files to reference in conversations.
**How to use:**
1. Click the attachment icon in chat
2. Select or drag files (max 10MB each)
3. View file preview and analysis
**Note:** Supported formats: .txt .md .pdf .doc .docx .py .js .ts .tsx .jsx .json .yaml .yml .xml .csv .log

### Pipeline Builder
**What it does:** Create automated workflows by connecting different steps.
**How to use:**
1. Drag steps from sidebar to canvas
2. Connect steps by dragging between ports
3. Click steps to configure parameters
**Note:** Available steps: LLM, Code, API, Condition, Transform

### Conversation Management
**What it does:** Organize and manage all your chat conversations.
**How to use:**
1. Create folders to organize conversations
2. Search by title, content, or model used
3. Bookmark important conversations
**Note:** Export formats: Markdown, JSON, Text

### AI Providers
**What it does:** Configure connections to different AI providers.
**How to use:**
1. Navigate to Providers page
2. Add API keys for each provider
3. View cost tracking dashboard
**Note:** Supported: OpenAI, Anthropic, Google, Cohere, Ollama

## Common Questions

### How do I start a new conversation?
Navigate to Chat page, select a model from the dropdown, type your message and press Enter.

### What file types can I upload?
Text files (.txt, .md), documents (.pdf, .doc, .docx), code files (.py, .js, .ts, .jsx, .tsx), data files (.json, .yaml, .xml, .csv), and log files (.log).

### How do I export a conversation?
Open the conversation, click the Export button, choose format (Markdown/JSON/Text), select messages, and download.

### Can I share conversations with others?
Yes, use the Share button in conversation view. Options: Private, Team, Link Share, or Public.

### How long are JWT tokens valid?
Access tokens expire after 30 minutes. Refresh tokens are valid for 7 days. The system automatically refreshes tokens when needed.

### What's the API rate limit?
Default rate limit is 10 requests per minute. This can be configured by administrators.

### How do I create an API key?
Go to your Profile page, navigate to the API Keys section, and click "Generate New Key".

### Can I use multiple AI providers?
Yes, you can configure and use multiple providers. The system tracks costs separately for each provider.

## Error Messages

**"Model not found"**
The selected model is not available. Refresh the models list from the Models page.

**"Invalid API Key or JWT Token"**
Your authentication has failed. For API keys, generate a new one in settings. For JWT, try logging in again.

**"Rate limit exceeded"**
You've made too many requests. Default limit is 10/minute. Wait 60 seconds before retrying.

**"Insufficient permissions"**
Your user role doesn't have access to this feature. Contact your workspace administrator.

**"File too large"**
Maximum file size is 10MB. Try compressing the file or splitting it into smaller parts.

**"Ollama service unavailable"**
The local Ollama service is not running. Ensure Ollama is installed and running on port 11434.

**"Pipeline validation failed"**
Your pipeline has configuration errors. Check that all steps are properly connected and configured.

**"Conversation not found"**
The conversation ID is invalid or you don't have access. Verify the conversation exists and you have permission.

## System Requirements

### Backend
- Python 3.8+
- PostgreSQL or SQLite database
- Redis (optional, for caching)
- Ollama (optional, for local models)

### Frontend
- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Minimum 1024x768 screen resolution

### API Endpoints
- Base URL: `http://localhost:8000/api`
- Authentication: Bearer token or API key
- Content-Type: application/json