# Message Threading and File Analysis

This document provides detailed information about the message threading and file analysis features in Web+.

## Message Threading

### Overview

Message threading allows users to organize conversations into logical threads, enabling better discussion flow and topic organization. Threads can be created from any message and can contain multiple nested replies.

### Features

- **Thread Creation**: Create threads from any message or start new threads in a conversation
- **Nested Replies**: Support for replies within threads, preserving conversation context
- **Thread Navigation**: Easily navigate between different threads in a conversation
- **Thread Collapsing**: Collapse and expand threads to manage screen space
- **Parent-Child Relationships**: Messages can have parent-child relationships for nested replies

### Technical Implementation

#### Database Structure

Threads are implemented using the `MessageThread` model:

```python
class MessageThread(Base):
    __tablename__ = "message_threads"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    creator_id = Column(String, ForeignKey("users.id"), nullable=True)
    parent_thread_id = Column(String, ForeignKey("message_threads.id"), nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="threads")
    messages = relationship("Message", back_populates="thread")
    creator = relationship("User")
    parent_thread = relationship("MessageThread", remote_side=[id], backref="child_threads")
```

Messages are linked to threads via the `thread_id` field in the `Message` model:

```python
class Message(Base):
    # ... existing fields
    parent_id = Column(String, ForeignKey("messages.id"), nullable=True)
    thread_id = Column(String, ForeignKey("message_threads.id"), nullable=True)
    
    # Relationships
    parent = relationship("Message", remote_side=[id], backref="replies")
    thread = relationship("MessageThread", back_populates="messages")
```

#### API Endpoints

The following API endpoints support thread operations:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/threads` | POST | Create a new thread |
| `/api/chat/threads/{thread_id}` | GET | Get thread by ID with messages |
| `/api/chat/conversations/{conversation_id}/threads` | GET | Get all threads for a conversation |
| `/api/chat/threads/{thread_id}/completions` | POST | Send a message to a thread |

#### Frontend Components

Key components for thread functionality:

- `ThreadedMessageList.tsx`: Display messages and threads with proper organization
- `CreateThreadDialog.tsx`: Dialog for creating new threads
- `EnhancedChatWithThreadsPage.tsx`: Main page component integrating thread features

### Usage

1. **Create a Thread**:
   - Click the "New Thread" button in the thread section
   - Or use the context menu on a message and select "New Thread"
   - Provide a title for the thread

2. **Reply in a Thread**:
   - Click on a thread to view its messages
   - Type your message in the input bar (which shows the current thread)
   - Submit to send your reply within the thread

3. **Navigate Between Threads**:
   - The thread section shows all threads in the conversation
   - Click on a thread to view and interact with it
   - Click the "X" on the input bar to exit the thread

## File Analysis

### Overview

File analysis allows the system to extract and analyze content from uploaded files, providing valuable insights and making the content available for AI interaction.

### Features

- **Text Extraction**: Extract text content from various file types (PDFs, documents, images with text, etc.)
- **Content Analysis**: AI-powered analysis of file contents
- **Searchable Content**: Make file contents searchable and accessible
- **Visual Insights**: Display analysis results in a user-friendly interface
- **Multi-format Support**: Support for various file types including documents, images, and PDFs

### Technical Implementation

#### Database Structure

File analysis features are implemented in the `File` model:

```python
class File(Base):
    # ... existing fields
    analyzed = Column(Boolean, default=False)
    analysis_result = Column(JSON, nullable=True)  # Results of AI analysis
    extracted_text = Column(Text, nullable=True)  # Text extracted from file
```

#### API Endpoints

The following API endpoints support file analysis:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/files/{file_id}/analyze` | POST | Request file analysis |
| `/api/files/{file_id}/analysis` | GET | Get analysis results for a file |

#### Frontend Components

Key components for file analysis:

- `FileAnalysisDisplay.tsx`: Component to display file analysis results
- `FileAnalysisModal.tsx`: Modal dialog for viewing file analysis
- `MessageWithAttachments.tsx`: Enhanced to support file analysis options

### Analysis Process

1. **Upload Phase**:
   - Files are uploaded and stored securely
   - Basic metadata (size, type, name) is captured

2. **Analysis Request**:
   - User can request analysis of a file
   - System queues the file for processing

3. **Processing**:
   - Text extraction from the file content
   - AI analysis of the extracted content
   - Generation of insights and summaries

4. **Results**:
   - Analysis results stored in the database
   - Results made available through the UI
   - Content becomes available for AI interactions

### Usage

1. **Analyze a File**:
   - Upload a file in a conversation
   - Click the "Analyze" button on the file card
   - Wait for analysis to complete

2. **View Analysis Results**:
   - Click on an analyzed file to open the analysis modal
   - Switch between "Extracted Text" and "Analysis" tabs
   - Read AI-generated insights about the file

3. **Use File Content in Conversations**:
   - Reference analyzed file content in your messages
   - The AI can understand and use the extracted content

## Integration with Chat Interface

Both message threading and file analysis are fully integrated with the chat interface:

- Threaded conversations appear in the main message list with visual indicators
- Files can be uploaded directly in threads
- File analysis can be requested from any message containing files
- Thread navigation is available from the chat input component
- Context management tracks token usage across threads

## Best Practices

### For Threading

- Use threads for distinct subtopics within a conversation
- Keep thread titles descriptive but concise
- Don't nest replies too deeply (2-3 levels is optimal)
- Use the main conversation for general discussion

### For File Analysis

- Analysis works best on text-heavy files (PDFs, documents)
- Large files (>50MB) may take longer to analyze
- For complex documents, consider analyzing sections separately
- Review extracted text to ensure accuracy before relying on it

## Limitations

### Threading Limitations

- Maximum of 100 threads per conversation
- Maximum of 500 messages per thread
- Thread titles limited to 100 characters

### File Analysis Limitations

- File size limit: 50MB
- Supported formats: PDF, DOCX, TXT, JPG, PNG
- Text extraction from images limited by image quality
- Analysis processing time increases with file size and complexity

## Future Enhancements

### Planned Threading Enhancements

- Thread search and filtering
- Thread bookmarking
- Thread templates for common discussion patterns
- Thread sharing and export

### Planned File Analysis Enhancements

- More comprehensive multimedia analysis
- Custom analysis pipelines
- Support for additional file formats
- Real-time collaborative analysis