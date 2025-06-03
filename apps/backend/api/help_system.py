"""
Help System API

Provides in-application help content and documentation endpoints.
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Optional
from pydantic import BaseModel

from auth.jwt import get_current_user
from db.models import User

router = APIRouter(prefix="/api/help", tags=["Help System"])


class HelpTopic(BaseModel):
    """Help topic model."""
    id: str
    title: str
    category: str
    content: str
    related_features: List[str]
    keywords: List[str]


class QuickHelp(BaseModel):
    """Quick help tooltip model."""
    feature: str
    title: str
    description: str
    tips: List[str]


class FAQItem(BaseModel):
    """FAQ item model."""
    question: str
    answer: str
    category: str
    related_topics: List[str]


# Static help content based on actual features
HELP_TOPICS = {
    "getting-started": HelpTopic(
        id="getting-started",
        title="Getting Started with Web+",
        category="basics",
        content="""
        # Getting Started
        
        1. **Login**: Use your credentials at the login page
        2. **Navigate**: Use the main menu to access different features
        3. **Select Model**: Choose an AI model from available providers
        4. **Start Chatting**: Type your message and press Enter
        5. **View Response**: Watch as the AI responds in real-time
        """,
        related_features=["auth", "models", "chat"],
        keywords=["start", "begin", "new", "first"]
    ),
    "models": HelpTopic(
        id="models",
        title="Model Management",
        category="features",
        content="""
        # Model Management
        
        View and manage AI models from multiple providers:
        - **OpenAI**: GPT-4, GPT-3.5-Turbo
        - **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
        - **Google**: Gemini Pro, PaLM
        - **Cohere**: Command R+, Command
        - **Ollama**: Local models (free)
        
        Only Ollama models can be started/stopped. External models are always available.
        """,
        related_features=["providers", "chat"],
        keywords=["model", "ai", "llm", "gpt", "claude", "gemini", "ollama"]
    ),
    "chat": HelpTopic(
        id="chat",
        title="Chat Interface",
        category="features",
        content="""
        # Chat Interface
        
        Features:
        - Real-time streaming responses
        - Markdown rendering with syntax highlighting
        - File attachments (up to 10MB)
        - Multi-line input (Shift+Enter)
        - Conversation threading
        - Message export
        """,
        related_features=["models", "files", "export"],
        keywords=["chat", "conversation", "message", "talk", "ask"]
    ),
    "pipelines": HelpTopic(
        id="pipelines",
        title="Pipeline Builder",
        category="features",
        content="""
        # Pipeline Builder
        
        Create automated workflows with these steps:
        - **LLM Step**: Call AI models with prompts
        - **Code Step**: Execute Python or JavaScript
        - **API Step**: Make HTTP requests
        - **Condition Step**: Add if/else logic
        - **Transform Step**: Modify data between steps
        
        Connect steps visually and configure parameters for each.
        """,
        related_features=["models", "execution"],
        keywords=["pipeline", "workflow", "automation", "chain", "flow"]
    ),
    "files": HelpTopic(
        id="files",
        title="File Management",
        category="features",
        content="""
        # File Management
        
        Supported file types:
        - Text: .txt, .md
        - Documents: .pdf, .doc, .docx
        - Code: .py, .js, .ts, .jsx, .tsx
        - Data: .json, .yaml, .xml, .csv
        - Logs: .log
        
        Maximum file size: 10MB per file
        Files are automatically analyzed upon upload.
        """,
        related_features=["chat", "analysis"],
        keywords=["file", "upload", "attachment", "document", "analyze"]
    ),
    "auth": HelpTopic(
        id="auth",
        title="Authentication & Security",
        category="security",
        content="""
        # Authentication & Security
        
        Authentication methods:
        - **JWT Tokens**: 30-minute access, 7-day refresh
        - **API Keys**: For programmatic access
        
        Security features:
        - Role-based access control (RBAC)
        - Workspace isolation
        - Audit logging
        - Encrypted credentials
        - Rate limiting (10 req/min default)
        """,
        related_features=["profile", "api"],
        keywords=["login", "security", "auth", "jwt", "api key", "rbac"]
    )
}

QUICK_HELPS = {
    "model-select": QuickHelp(
        feature="model-select",
        title="Model Selection",
        description="Choose an AI model for your conversation",
        tips=[
            "GPT-4: Best for complex reasoning",
            "Claude: Great for long conversations",
            "Gemini: Good for general tasks",
            "Ollama: Free local models"
        ]
    ),
    "message-input": QuickHelp(
        feature="message-input",
        title="Message Input",
        description="Type your message to the AI",
        tips=[
            "Press Enter to send",
            "Shift+Enter for new line",
            "Attach files with the clip icon",
            "Use markdown for formatting"
        ]
    ),
    "pipeline-step": QuickHelp(
        feature="pipeline-step",
        title="Pipeline Steps",
        description="Add functionality to your pipeline",
        tips=[
            "Drag to reorder steps",
            "Click to configure",
            "Connect outputs to inputs",
            "Use conditions for branching"
        ]
    )
}

FAQ_ITEMS = [
    FAQItem(
        question="How do I start a new conversation?",
        answer="Navigate to Chat page, select a model from the dropdown, type your message and press Enter.",
        category="chat",
        related_topics=["chat", "models"]
    ),
    FAQItem(
        question="What file types can I upload?",
        answer="Text files (.txt, .md), documents (.pdf, .doc, .docx), code files (.py, .js, .ts, .jsx, .tsx), data files (.json, .yaml, .xml, .csv), and log files (.log).",
        category="files",
        related_topics=["files", "chat"]
    ),
    FAQItem(
        question="How long are JWT tokens valid?",
        answer="Access tokens expire after 30 minutes. Refresh tokens are valid for 7 days. The system automatically refreshes tokens when needed.",
        category="auth",
        related_topics=["auth", "security"]
    ),
    FAQItem(
        question="What's the API rate limit?",
        answer="Default rate limit is 10 requests per minute. This can be configured by administrators.",
        category="api",
        related_topics=["api", "auth"]
    ),
    FAQItem(
        question="Can I use multiple AI providers?",
        answer="Yes, you can configure and use multiple providers. The system tracks costs separately for each provider.",
        category="providers",
        related_topics=["models", "providers"]
    )
]


@router.get("/topics", response_model=List[HelpTopic])
async def get_help_topics(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in content"),
    current_user: User = Depends(get_current_user)
):
    """Get all help topics, optionally filtered."""
    topics = list(HELP_TOPICS.values())
    
    # Filter by category
    if category:
        topics = [t for t in topics if t.category == category]
    
    # Search in content and keywords
    if search:
        search_lower = search.lower()
        topics = [
            t for t in topics
            if search_lower in t.title.lower()
            or search_lower in t.content.lower()
            or any(search_lower in k for k in t.keywords)
        ]
    
    return topics


@router.get("/topics/{topic_id}", response_model=HelpTopic)
async def get_help_topic(
    topic_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific help topic."""
    topic = HELP_TOPICS.get(topic_id)
    if not topic:
        return {"error": "Topic not found"}
    return topic


@router.get("/quick/{feature}", response_model=QuickHelp)
async def get_quick_help(
    feature: str,
    current_user: User = Depends(get_current_user)
):
    """Get quick help for a specific feature."""
    help_item = QUICK_HELPS.get(feature)
    if not help_item:
        return {"error": "Quick help not found"}
    return help_item


@router.get("/faq", response_model=List[FAQItem])
async def get_faq(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user)
):
    """Get frequently asked questions."""
    items = FAQ_ITEMS
    
    if category:
        items = [item for item in items if item.category == category]
    
    return items


@router.get("/search")
async def search_help(
    q: str = Query(..., description="Search query"),
    current_user: User = Depends(get_current_user)
):
    """Search across all help content."""
    query_lower = q.lower()
    results = []
    
    # Search in topics
    for topic in HELP_TOPICS.values():
        if (query_lower in topic.title.lower() or
            query_lower in topic.content.lower() or
            any(query_lower in k for k in topic.keywords)):
            results.append({
                "type": "topic",
                "id": topic.id,
                "title": topic.title,
                "category": topic.category,
                "excerpt": topic.content[:200] + "..."
            })
    
    # Search in FAQ
    for faq in FAQ_ITEMS:
        if (query_lower in faq.question.lower() or
            query_lower in faq.answer.lower()):
            results.append({
                "type": "faq",
                "question": faq.question,
                "answer": faq.answer,
                "category": faq.category
            })
    
    # Search in quick helps
    for qh in QUICK_HELPS.values():
        if (query_lower in qh.title.lower() or
            query_lower in qh.description.lower()):
            results.append({
                "type": "quick",
                "feature": qh.feature,
                "title": qh.title,
                "description": qh.description
            })
    
    return {
        "query": q,
        "count": len(results),
        "results": results[:20]  # Limit to 20 results
    }


@router.get("/categories")
async def get_help_categories(
    current_user: User = Depends(get_current_user)
):
    """Get all help categories."""
    categories = set()
    for topic in HELP_TOPICS.values():
        categories.add(topic.category)
    
    return {
        "categories": [
            {"id": "basics", "name": "Getting Started", "icon": "rocket"},
            {"id": "features", "name": "Features", "icon": "layers"},
            {"id": "security", "name": "Security", "icon": "shield"},
            {"id": "api", "name": "API", "icon": "code"}
        ]
    }