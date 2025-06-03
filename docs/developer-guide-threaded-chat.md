# Developer Guide: Implementing Threaded Chat

This guide provides detailed information for developers working with the threaded chat functionality in Web+. It covers the architecture, components, and implementation details of the message threading system.

## Architecture Overview

The threaded chat system consists of these main components:

1. **Backend Models**: Database models for threads and messages
2. **API Layer**: Endpoints for thread operations
3. **Frontend Components**: React components for thread visualization and interaction
4. **State Management**: Logic for managing threads and messages in the UI

## Database Models

### MessageThread Model

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

### Message Model Thread-Related Fields

```python
class Message(Base):
    # ... other fields
    parent_id = Column(String, ForeignKey("messages.id"), nullable=True)
    thread_id = Column(String, ForeignKey("message_threads.id"), nullable=True)
    
    # Relationships
    parent = relationship("Message", remote_side=[id], backref="replies")
    thread = relationship("MessageThread", back_populates="messages")
```

### Conversation Thread Relationship

```python
class Conversation(Base):
    # ... other fields
    threads = relationship("MessageThread", back_populates="conversation", cascade="all, delete-orphan")
```

## API Endpoints

### Thread Creation

```python
@router.post("/threads")
async def create_thread(
    thread_data: schemas.ThreadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.Thread:
    """Create a new message thread."""
    # Implementation details...
```

### Get Thread by ID

```python
@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.Thread:
    """Get a thread by ID with its messages."""
    # Implementation details...
```

### Get Threads for Conversation

```python
@router.get("/conversations/{conversation_id}/threads")
async def get_conversation_threads(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.ThreadList:
    """Get all threads for a conversation."""
    # Implementation details...
```

### Send Message to Thread

```python
@router.post("/threads/{thread_id}/completions")
async def thread_completion(
    thread_id: str,
    request: schemas.ChatCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.ChatCompletionResponse:
    """Send a message to a thread and get a completion."""
    # Implementation details...
```

## Frontend Components

### ThreadedMessageList

The `ThreadedMessageList` component displays both regular messages and threaded messages:

```tsx
export const ThreadedMessageList: React.FC<ThreadedMessageListProps> = ({
  messages,
  threads = [],
  activeThreadId,
  userInitials,
  modelInitials,
  // ... other props
}) => {
  // Implementation logic...
  
  return (
    <div className={cn("flex-1 overflow-y-auto", className)}>
      {/* Root messages */}
      {rootMessages.map((message, index) => (
        <div key={message.id} className="message-container">
          <MessageWithAttachments
            message={message}
            // ... props
            threadActionButton={
              onCreateThread && (
                <Button onClick={() => onCreateThread(message)}>
                  New Thread
                </Button>
              )
            }
          />
          
          {/* Display replies if any */}
          {message.replies && message.replies.length > 0 && (
            <div className="ml-10 pl-6 border-l-2 border-muted mt-2">
              {/* Replies rendering */}
            </div>
          )}
        </div>
      ))}
      
      {/* Thread section */}
      {threads.length > 0 && (
        <div className="mt-6">
          <h3>Discussion Threads</h3>
          
          {threads.map(thread => (
            <Collapsible
              key={thread.id}
              open={openThreads[thread.id] || false}
              onOpenChange={() => toggleThread(thread.id)}
            >
              {/* Thread rendering */}
            </Collapsible>
          ))}
        </div>
      )}
    </div>
  );
};
```

### CreateThreadDialog

```tsx
export const CreateThreadDialog: React.FC<CreateThreadDialogProps> = ({
  conversationId,
  basedOnMessage,
  open,
  onOpenChange,
  onCreateThread,
  trigger,
}) => {
  const [title, setTitle] = useState('');
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onCreateThread(title, basedOnMessage?.id);
    setTitle('');
    onOpenChange(false);
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* Dialog content */}
      <form onSubmit={handleSubmit}>
        {/* Form fields */}
      </form>
    </Dialog>
  );
};
```

## Thread State Management

The main page component (`EnhancedChatWithThreadsPage`) manages thread state:

```tsx
// Thread state
const [threads, setThreads] = useState<MessageThread[]>([]);
const [activeThreadId, setActiveThreadId] = useState<string | null>(null);

// Load threads for a conversation
const loadThreads = async (conversationId: string) => {
  try {
    const response = await conversationsApi.threads.getByConversation(conversationId);
    
    if (response.success) {
      setThreads(response.data.threads || []);
    }
  } catch (err) {
    console.error("Error loading threads:", err);
  }
};

// Load a specific thread
const loadThread = async (threadId: string) => {
  try {
    setActiveThreadId(threadId);
    
    const response = await conversationsApi.threads.getById(threadId);
    
    if (response.success) {
      // Update the thread in our thread list
      setThreads(prev => prev.map(t => 
        t.id === threadId ? response.data : t
      ));
    }
  } catch (err) {
    console.error("Error loading thread:", err);
  }
};

// Create a new thread
const handleCreateThread = async (title: string, basedOnMessageId?: string) => {
  try {
    const response = await conversationsApi.threads.create({
      conversation_id: conversation.id,
      title: title
    });
    
    if (response.success) {
      setThreads(prev => [...prev, response.data]);
      setActiveThreadId(response.data.id);
      
      // If based on a message, reply to it in the new thread
      if (basedOnMessageId) {
        // Implementation details...
      }
    }
  } catch (err) {
    console.error("Error creating thread:", err);
  }
};
```

## Message Sending with Thread Support

Messages can be sent to either the main conversation or a specific thread:

```tsx
// Send message
const sendMessage = async (content: string, files?: File[], threadId?: string) => {
  // ... implementation details
  
  // Determine API call based on whether it's a thread message
  const apiCall = threadId 
    ? conversationsApi.threads.sendMessage(threadId, {
        model_id: conversation.model_id,
        prompt: content,
        // ... other params
      })
    : conversationsApi.sendMessage({
        model_id: conversation.model_id,
        prompt: content,
        // ... other params
      });
  
  const response = await apiCall;
  
  // ... handle response
  
  if (threadId) {
    // Update thread messages
    setThreads(prev => prev.map(thread => {
      if (thread.id === threadId) {
        return {
          ...thread,
          messages: [...updatedMessages, userMessage, assistantMessage]
        };
      }
      return thread;
    }));
  } else {
    // Update main conversation messages
    setMessages([...updatedMessages, userMessage, assistantMessage]);
  }
};
```

## Thread API Client

The thread-related API client extensions:

```typescript
// Message Thread API Request Types
export interface CreateThreadRequest {
  conversation_id: string;
  title?: string;
  parent_thread_id?: string;
}

export interface ThreadListResponse {
  threads: MessageThread[];
}

// Threads API
threads: {
  // Create a new thread
  create: (data: CreateThreadRequest, signal?: AbortSignal): Promise<APIResponse<MessageThread>> => {
    return authSafeFetch<MessageThread>(
      `/api/chat/threads`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        signal
      }
    );
  },

  // Get thread by ID
  getById: (id: string, signal?: AbortSignal): Promise<APIResponse<MessageThread>> => {
    return authSafeFetch<MessageThread>(
      `/api/chat/threads/${id}`,
      { signal }
    );
  },

  // Get threads for a conversation
  getByConversation: (conversationId: string, signal?: AbortSignal): Promise<APIResponse<ThreadListResponse>> => {
    return authSafeFetch<ThreadListResponse>(
      `/api/chat/conversations/${conversationId}/threads`,
      { signal }
    );
  },

  // Send a message to a thread
  sendMessage: (threadId: string, data: ChatCompletionRequest, signal?: AbortSignal): Promise<APIResponse<ChatCompletionResponse>> => {
    return authSafeFetch<ChatCompletionResponse>(
      `/api/chat/threads/${threadId}/completions`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        signal
      }
    );
  }
}
```

## Working with Threads

### Creating a New Thread

```typescript
// Create a new thread
const newThread = await conversationsApi.threads.create({
  conversation_id: "conversation-id-here",
  title: "Discussion about new feature"
});

// Get the thread ID
const threadId = newThread.data.id;
```

### Sending a Message to a Thread

```typescript
// Send a message to a thread
const response = await conversationsApi.threads.sendMessage(
  "thread-id-here",
  {
    model_id: "gpt-4",
    prompt: "This is a message in a thread",
    options: {
      temperature: 0.7
    }
  }
);
```

### Loading Thread Messages

```typescript
// Get thread with all its messages
const threadResponse = await conversationsApi.threads.getById("thread-id-here");
const threadMessages = threadResponse.data.messages;
```

## Best Practices

1. **Thread Organization**:
   - Keep related messages in the same thread
   - Use descriptive thread titles
   - Don't create too many threads (becomes hard to manage)

2. **Thread UI**:
   - Provide clear visual distinction between main conversation and threads
   - Use collapsible UI for threads to save space
   - Show thread titles and message counts for easier navigation

3. **Performance Considerations**:
   - Load thread messages on demand (not all at once)
   - Implement pagination for long threads
   - Consider caching thread data for better performance

4. **Error Handling**:
   - Handle thread loading failures gracefully
   - Provide feedback when thread operations fail
   - Implement retry mechanisms for failed thread operations

## Common Issues and Solutions

### Thread Not Updating After Message Send

Ensure you're updating the thread's messages array after sending a message:

```typescript
setThreads(prev => prev.map(thread => {
  if (thread.id === threadId) {
    return {
      ...thread,
      messages: [...thread.messages, newMessage]
    };
  }
  return thread;
}));
```

### Messages Appearing in Wrong Thread

Check the `thread_id` field when creating messages:

```typescript
const userMessage = {
  // ... other fields
  thread_id: activeThreadId, // Make sure this is set correctly
};
```

### Thread List Not Refreshing

Manually reload threads after operations:

```typescript
// After creating a thread or sending a message
await loadThreads(conversationId);
```

## Future Enhancements

Planned enhancements to the threading system:

1. **Thread Search**: Ability to search within threads
2. **Thread Sorting/Filtering**: Sort and filter threads by various criteria
3. **Thread Sharing**: Share specific threads with other users
4. **Thread Templates**: Predefined thread structures for common scenarios
5. **Thread Analytics**: Track engagement and activity within threads