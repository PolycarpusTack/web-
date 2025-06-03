# User Guide

This guide will help you navigate and use the Codex Machina Web+ application effectively.

## Getting Started

### Accessing the Application

1. Open your web browser and navigate to the application URL (typically http://localhost:5173 in development)
2. You'll be presented with the main dashboard showing available LLM models

### Understanding the Interface

The application has three main components:

1. **LLM Manager** - For viewing and managing your LLM models
2. **Chat Interface** - For having conversations with LLMs
3. **Code Factory** - For creating automated pipelines of LLMs

## LLM Manager

The LLM Manager provides a visual interface to manage your LLM models.

### Viewing Models

- The main dashboard displays all available models with their status
- Models can be viewed in grid or list view
- You can search and filter models by name, provider, or status

### Managing Models

- **Starting a Model**: Toggle the switch next to a model to start it
- **Stopping a Model**: Toggle the switch next to a running model to stop it
- **Model Details**: Click on a model card to view detailed information
- **Chat with Model**: Click the "Chat" button to open a conversation with that model

### Adding External Models

To add external API-based models (like OpenAI or Anthropic):

1. Click the "Add Model" button
2. Select the provider from the dropdown
3. Enter your API key
4. Enter the model ID (e.g., "gpt-4", "claude-3-opus")
5. Click "Add Model"

## Chat Interface

The Chat Interface allows you to have conversations with LLMs.

### Starting a Conversation

1. Select a model from the dropdown or sidebar
2. Type your message in the input box at the bottom
3. Press Enter or click the Send button
4. The model will respond in the conversation area

### Chat Features

- **Message History**: Your conversation history is preserved
- **Code Highlighting**: Code blocks in responses are highlighted
- **Conversation Saving**: You can save and name conversations for later
- **Export**: Conversations can be exported as text or markdown files

### Advanced Settings

Click the Settings icon to access advanced chat options:

- **Temperature**: Controls randomness (0.0-1.0)
- **Max Tokens**: Controls response length
- **System Prompt**: Sets the initial context for the AI
- **Top-p & Frequency Penalty**: Advanced parameters for response generation

## Code Factory

The Code Factory feature allows you to create pipelines of specialized LLMs.

### Creating a Pipeline

1. Navigate to the Code Factory tab
2. Click "New Pipeline"
3. Add steps to your pipeline:
   - Click "Add Step"
   - Select a model
   - Choose a role (e.g., "Input Translator", "Code Generator")
   - Add instructions for the model
4. Arrange steps by dragging and dropping
5. Save your pipeline with a name and description

### Pipeline Roles

Typical pipeline roles include:

- **Input Translator**: Analyzes user input and converts it into a structured prompt
- **Code Generator**: Creates the initial code
- **Code Enhancer**: Improves the generated code and adds error handling
- **Code Reviewer**: Reviews for bugs, security issues, and best practices
- **Documentation Generator**: Creates documentation for the code

### Running a Pipeline

1. Navigate to the "Run" tab
2. Enter your request in the input box
3. Click "Run Pipeline"
4. The system will process your request through each step
5. You can view progress in real-time
6. Final output will be displayed when complete

### Managing Pipelines

- **Saving**: Pipelines are saved automatically
- **Editing**: You can edit any saved pipeline
- **Sharing**: Pipelines can be exported and shared with others
- **Templates**: You can create templates for common tasks

## User Settings

Access your settings by clicking the gear icon or your profile picture.

### Profile Settings

- Update your name and profile picture
- Change your email address
- Manage your account

### Appearance Settings

- Toggle between light and dark mode
- Adjust font size
- Choose layout preferences

### Model Preferences

- Set your default model
- Configure default parameters for each model
- Manage your API keys

### Notification Settings

- Enable or disable notifications for model updates
- Set alert thresholds for usage limits
- Configure email notifications

## Keyboard Shortcuts

For efficient usage, the following keyboard shortcuts are available:

- `Ctrl+Enter` or `Cmd+Enter`: Send message
- `Ctrl+/` or `Cmd+/`: Focus search
- `Ctrl+N` or `Cmd+N`: New conversation
- `Ctrl+S` or `Cmd+S`: Save conversation
- `Esc`: Close modal or cancel action

## Troubleshooting

### Common Issues

#### Model Won't Start

- Ensure Ollama is running
- Check that you have enough system resources
- Verify the model is properly installed in Ollama

#### Slow Responses

- Larger models require more resources
- Try reducing the max tokens parameter
- Consider using a smaller, faster model for quick queries

#### Error Messages

- "Model not found": Ensure the model is installed in Ollama
- "API key invalid": Check your external API key
- "Rate limit exceeded": Wait a moment and try again

### Getting Help

- Check the documentation
- Look for error details in the browser console
- Contact support with specific error messages

## Advanced Usage

### API Integration

The application provides an API that you can use to integrate with other tools:

- API documentation is available at `/docs`
- Use your API key for authentication
- Endpoints are available for all main functions

### Custom Models

To use custom models:

1. Add your model to Ollama first
2. Refresh the model list in the application
3. Your custom model should appear in the list

### Batch Processing

For processing multiple inputs:

1. Create a CSV file with your inputs
2. Use the Batch Processing feature in the Code Factory
3. Upload your CSV file
4. Configure the pipeline
5. Run the batch process
6. Download the results as CSV

## Best Practices

- **Start with small models** for quick tasks, larger models for complex ones
- **Save important conversations** to avoid losing information
- **Use system prompts** to guide the model's behavior
- **Create pipeline templates** for recurring tasks
- **Monitor usage** to control costs when using external API models
