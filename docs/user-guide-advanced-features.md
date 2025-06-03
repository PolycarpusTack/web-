# Web+ Advanced Features User Guide

This guide provides instructions on using the advanced features in Web+, focusing on message threading and file analysis capabilities.

## Table of Contents

1. [Message Threading](#message-threading)
2. [File Analysis](#file-analysis)
3. [Combined Workflows](#combined-workflows)
4. [Tips and Tricks](#tips-and-tricks)
5. [Troubleshooting](#troubleshooting)

## Message Threading

Message threading helps you organize conversations into focused topics, making complex discussions easier to follow.

### Creating a New Thread

There are two ways to create a new thread:

**Option 1: Create a thread from the conversation**

1. In any conversation, locate the "New Thread" button in the header
2. Click the button to open the Create Thread dialog
3. Enter a descriptive title for your thread (e.g., "Budget Discussion for Q3")
4. Click "Create Thread"

![Creating a new thread](../images/thread-creation.png)

**Option 2: Create a thread from a specific message**

1. Hover over any message in the conversation
2. Click the "..." menu that appears on the right side of the message
3. Select "New Thread" from the dropdown menu
4. Enter a title for the thread
5. The thread will be created with a reference to the original message

### Navigating Between Threads

The conversation interface shows both the main conversation and all threads:

1. The main conversation appears at the top
2. Threads are displayed in a collapsible section below
3. Click on any thread title to expand or collapse it
4. When a thread is expanded, you'll see all messages in that thread

### Responding in Threads

To respond in a thread:

1. Click on the thread to expand it
2. The message input at the bottom will show which thread you're currently in
3. Type your message and press Enter or click Send
4. Your message will appear in the thread, not in the main conversation

To exit a thread and return to the main conversation:

1. Click the "X" button next to the thread name in the message input
2. Or click anywhere in the main conversation

### Thread Organization

Threads are organized in these ways:

1. **Chronologically**: Newer threads appear at the top of the thread list
2. **Hierarchically**: Threads can contain parent-child relationships
3. **Visually**: Active threads are highlighted for easy identification

## File Analysis

File analysis allows you to extract insights from uploaded files using AI.

### Uploading Files

To upload files:

1. Click the file attachment button in the message input
2. Select one or more files from your device
3. The files will be attached to your next message
4. Type your message (optional) and send

Supported file types:
- Documents: PDF, DOCX, TXT
- Images: JPG, PNG
- Other: CSV, JSON

File size limit: 50MB per file

### Analyzing Files

To analyze an uploaded file:

1. Locate a message containing file attachments
2. Click on the file you want to analyze
3. In the file preview, click the "Analyze" button
4. Wait for the analysis to complete (this may take a few moments)

![Analyzing a file](../images/file-analysis.png)

### Viewing Analysis Results

Once analysis is complete:

1. Click on the analyzed file
2. The File Analysis dialog will open with two tabs:
   - "Extracted Text": Shows the text content extracted from the file
   - "Analysis": Shows AI-generated insights about the content

The analysis tab typically includes:
- Summary of the document
- Key points extracted
- Topics identified
- Entities mentioned
- Other relevant insights

### Using File Analysis in Conversations

To reference analyzed content in your conversations:

1. View the file analysis results
2. Quote or reference specific insights in your messages
3. The AI will understand the context from the analyzed file
4. Ask follow-up questions about the file content

Example: "Based on the budget report I uploaded, what are the main areas where we're over budget?"

## Combined Workflows

Thread and file analysis features work together for powerful workflows:

### Topic-Specific File Discussions

1. Upload a file in the main conversation
2. Create a new thread based on the file
3. Analyze the file within the thread
4. Discuss specific aspects of the file in focused threads

### Document Review Process

1. Upload a document for review
2. Analyze the document
3. Create separate threads for different sections or issues
4. Collaborators can respond in specific threads
5. Track the review process through thread organization

## Tips and Tricks

### Effective Threading

- **Use descriptive titles**: Thread titles should clearly indicate the topic
- **Keep threads focused**: Create new threads for different topics
- **Reference related threads**: Mention other threads when topics overlap
- **Thread cleanup**: Close or archive threads when a topic is resolved

### Optimizing File Analysis

- **Prepare files properly**: Use clear formatting for better text extraction
- **Split large documents**: Break very large documents into smaller parts
- **Provide context**: When uploading files, add a message explaining what's in them
- **Ask specific questions**: Direct questions about file content get better answers

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Create new thread | Alt+T |
| Navigate to next thread | Alt+↓ |
| Navigate to previous thread | Alt+↑ |
| Exit current thread | Alt+Esc |
| Upload file | Alt+U |
| Analyze selected file | Alt+A |

## Troubleshooting

### Threading Issues

**Problem**: Can't find a thread I created
- **Solution**: Use the search function at the top of the thread list or check the conversation history

**Problem**: Thread appears empty
- **Solution**: The thread may not have any messages yet. Send a message to the thread.

**Problem**: Can't exit a thread
- **Solution**: Click the "X" next to the thread name in the message input or refresh the page

### File Analysis Issues

**Problem**: File analysis is taking too long
- **Solution**: Large files (over 10MB) may take several minutes to analyze. Wait or try with a smaller file.

**Problem**: Analysis results are inaccurate
- **Solution**: File format or quality may affect analysis. Try converting to PDF or a more readable format.

**Problem**: Can't analyze a specific file type
- **Solution**: Ensure the file type is supported. Convert to a supported format if needed.

**Problem**: Analysis shows "Extraction Failed"
- **Solution**: The file may be password-protected, corrupted, or in an unsupported format. Check the file and try again.

## Feature Limitations

### Thread Limitations

- Maximum 100 threads per conversation
- Maximum 500 messages per thread
- Thread titles limited to 100 characters

### File Analysis Limitations

- Maximum file size: 50MB
- Supported formats: PDF, DOCX, TXT, JPG, PNG
- Text extraction limited to 1 million characters
- Analysis timeout: 5 minutes (standard), 15 minutes (large files)

## Getting Help

If you encounter issues not covered in this guide:

1. Click the Help icon (?) in the top-right corner of the application
2. Check the knowledge base for additional information
3. Contact support through the "Contact Support" option
4. Provide specific details about your issue for faster resolution