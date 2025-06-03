import React from 'react';
import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';

export function HelpContent() {
  return (
    <>
      <AccordionItem value="models">
        <AccordionTrigger>Model Management</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">What it does:</h4>
              <p className="text-sm text-muted-foreground">
                View and manage AI models from multiple providers including OpenAI, Anthropic, Google, Cohere, and local Ollama models.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">How to use:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Navigate to Models page from the main menu</li>
                <li>• Use search bar to filter by name or provider</li>
                <li>• Click Start/Stop buttons to control Ollama models</li>
                <li>• Auto-refresh updates status every 30 seconds</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Note:</h4>
              <p className="text-sm text-muted-foreground">
                Only local Ollama models can be started/stopped. External provider models are always available.
              </p>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="chat">
        <AccordionTrigger>Chat Interface</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">What it does:</h4>
              <p className="text-sm text-muted-foreground">
                Interactive chat with AI models featuring real-time streaming responses, markdown rendering, and file attachments.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">How to use:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Select a model from the dropdown menu</li>
                <li>• Type your message in the input field</li>
                <li>• Press Enter or click Send to submit</li>
                <li>• Watch the response stream in real-time</li>
                <li>• Use Shift+Enter for multi-line messages</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Features:</h4>
              <div className="flex flex-wrap gap-1 mt-1">
                <Badge variant="secondary">Streaming</Badge>
                <Badge variant="secondary">Markdown</Badge>
                <Badge variant="secondary">Code Highlighting</Badge>
                <Badge variant="secondary">File Attachments</Badge>
                <Badge variant="secondary">Threading</Badge>
              </div>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="files">
        <AccordionTrigger>File Management</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">What it does:</h4>
              <p className="text-sm text-muted-foreground">
                Upload and analyze files to reference in conversations. Supports documents, code files, and text formats.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">How to use:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Click the attachment icon in chat</li>
                <li>• Select or drag files (max 10MB each)</li>
                <li>• View file preview and analysis</li>
                <li>• Reference uploaded files in messages</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Supported formats:</h4>
              <p className="text-sm text-muted-foreground font-mono">
                .txt .md .pdf .doc .docx .py .js .ts .tsx .jsx .json .yaml .yml .xml .csv .log
              </p>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="pipelines">
        <AccordionTrigger>Pipeline Builder</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">What it does:</h4>
              <p className="text-sm text-muted-foreground">
                Create automated workflows by connecting different steps like LLM calls, code execution, API requests, and data transformations.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">Available steps:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• <strong>LLM Step:</strong> Call AI models with prompts</li>
                <li>• <strong>Code Step:</strong> Execute Python/JavaScript code</li>
                <li>• <strong>API Step:</strong> Make HTTP requests</li>
                <li>• <strong>Condition Step:</strong> Add if/else logic</li>
                <li>• <strong>Transform Step:</strong> Modify data between steps</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">How to build:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Drag steps from the sidebar to canvas</li>
                <li>• Connect steps by dragging between ports</li>
                <li>• Click steps to configure parameters</li>
                <li>• Use Preview to test without execution</li>
                <li>• Save pipelines for reuse</li>
              </ul>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="conversations">
        <AccordionTrigger>Conversation Management</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">What it does:</h4>
              <p className="text-sm text-muted-foreground">
                Organize, search, and manage all your chat conversations with folders, bookmarks, and sharing capabilities.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">Features:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Create folders to organize conversations</li>
                <li>• Search by title, content, or model used</li>
                <li>• Bookmark important conversations</li>
                <li>• Share conversations with team members</li>
                <li>• Export to Markdown, JSON, or Text</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Sharing options:</h4>
              <div className="flex flex-wrap gap-1 mt-1">
                <Badge variant="outline">Private</Badge>
                <Badge variant="outline">Team</Badge>
                <Badge variant="outline">Link Share</Badge>
                <Badge variant="outline">Public</Badge>
              </div>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="providers">
        <AccordionTrigger>AI Providers</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">What it does:</h4>
              <p className="text-sm text-muted-foreground">
                Configure and manage connections to different AI providers with automatic cost tracking.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">Supported providers:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• <strong>OpenAI:</strong> GPT-4, GPT-3.5, DALL-E</li>
                <li>• <strong>Anthropic:</strong> Claude 3 Opus, Sonnet, Haiku</li>
                <li>• <strong>Google:</strong> Gemini Pro, PaLM</li>
                <li>• <strong>Cohere:</strong> Command R+, Command</li>
                <li>• <strong>Ollama:</strong> Local models (free)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Cost tracking:</h4>
              <p className="text-sm text-muted-foreground">
                Automatic tracking of token usage and costs per provider with daily/monthly summaries.
              </p>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="auth">
        <AccordionTrigger>Authentication & Security</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">Authentication methods:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• <strong>JWT Tokens:</strong> 30-minute access, 7-day refresh</li>
                <li>• <strong>API Keys:</strong> Generate in profile settings</li>
                <li>• <strong>Session:</strong> Automatic token refresh</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Security features:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Role-based access control (RBAC)</li>
                <li>• Workspace isolation</li>
                <li>• Audit logging for compliance</li>
                <li>• Encrypted credential storage</li>
                <li>• Rate limiting (10 requests/minute default)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">User roles:</h4>
              <div className="flex flex-wrap gap-1 mt-1">
                <Badge>Admin</Badge>
                <Badge>Manager</Badge>
                <Badge>User</Badge>
                <Badge>Viewer</Badge>
              </div>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="export">
        <AccordionTrigger>Export & Analytics</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">Export options:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• <strong>Markdown:</strong> Formatted conversation export</li>
                <li>• <strong>JSON:</strong> Structured data with metadata</li>
                <li>• <strong>Text:</strong> Plain text conversation</li>
                <li>• <strong>Selection:</strong> Choose specific messages</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Analytics features:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Model usage statistics</li>
                <li>• Token consumption tracking</li>
                <li>• Cost analysis by provider</li>
                <li>• Response time metrics</li>
                <li>• Daily/monthly summaries</li>
              </ul>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="performance">
        <AccordionTrigger>Performance & Caching</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">Performance features:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Redis caching for fast responses</li>
                <li>• WebSocket for real-time updates</li>
                <li>• Streaming responses for long outputs</li>
                <li>• Background job processing</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Cache behavior:</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Models: 5-10 minute cache</li>
                <li>• User data: 15 minute cache</li>
                <li>• Analytics: 1 hour cache</li>
                <li>• Automatic fallback to memory cache</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Performance targets:</h4>
              <p className="text-sm text-muted-foreground">
                API responses &lt;200ms, real-time streaming, 2-10x improvement with cache hits.
              </p>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
    </>
  );
}