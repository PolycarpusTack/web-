import React from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { HelpCircle } from 'lucide-react';

interface QuickHelpProps {
  feature: string;
  children?: React.ReactNode;
}

const helpContent: Record<string, { title: string; description: string; tips: string[] }> = {
  'model-select': {
    title: 'Model Selection',
    description: 'Choose an AI model for your conversation',
    tips: [
      'GPT-4: Best for complex reasoning',
      'Claude: Great for long conversations',
      'Gemini: Good for general tasks',
      'Ollama: Free local models'
    ]
  },
  'message-input': {
    title: 'Message Input',
    description: 'Type your message to the AI',
    tips: [
      'Press Enter to send',
      'Shift+Enter for new line',
      'Attach files with the clip icon',
      'Use markdown for formatting'
    ]
  },
  'file-upload': {
    title: 'File Upload',
    description: 'Attach files to your message',
    tips: [
      'Max size: 10MB per file',
      'Supports text, code, documents',
      'Files are analyzed automatically',
      'Reference files in your message'
    ]
  },
  'pipeline-step': {
    title: 'Pipeline Steps',
    description: 'Add functionality to your pipeline',
    tips: [
      'Drag to reorder steps',
      'Click to configure',
      'Connect outputs to inputs',
      'Use conditions for branching'
    ]
  },
  'export-format': {
    title: 'Export Format',
    description: 'Choose how to save your conversation',
    tips: [
      'Markdown: Formatted text',
      'JSON: Structured data',
      'Text: Plain conversation',
      'Select specific messages'
    ]
  },
  'model-status': {
    title: 'Model Status',
    description: 'Current state of the AI model',
    tips: [
      'Green: Running and ready',
      'Yellow: Starting up',
      'Red: Stopped or error',
      'Gray: External provider'
    ]
  },
  'conversation-folder': {
    title: 'Conversation Folders',
    description: 'Organize your conversations',
    tips: [
      'Create folders by topic',
      'Drag to move conversations',
      'Share entire folders',
      'Color-code for quick access'
    ]
  },
  'api-key': {
    title: 'API Key Management',
    description: 'Secure access to the API',
    tips: [
      'Generate in profile settings',
      'Use for programmatic access',
      'Revoke compromised keys',
      'Set expiration dates'
    ]
  },
  'rate-limit': {
    title: 'Rate Limiting',
    description: 'API request restrictions',
    tips: [
      'Default: 10 requests/minute',
      'Resets every 60 seconds',
      'Higher limits for premium',
      'Check headers for status'
    ]
  },
  'cost-tracking': {
    title: 'Cost Tracking',
    description: 'Monitor AI usage costs',
    tips: [
      'Automatic token counting',
      'Per-provider breakdown',
      'Daily/monthly summaries',
      'Set budget alerts'
    ]
  }
};

export function QuickHelp({ feature, children }: QuickHelpProps) {
  const help = helpContent[feature];
  
  if (!help) {
    return <>{children}</>;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="inline-flex items-center gap-1 cursor-help">
            {children}
            <HelpCircle className="h-3 w-3 text-muted-foreground" />
          </span>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <div className="space-y-2">
            <div>
              <h4 className="font-semibold">{help.title}</h4>
              <p className="text-sm text-muted-foreground">{help.description}</p>
            </div>
            <ul className="text-sm space-y-0.5">
              {help.tips.map((tip, index) => (
                <li key={index} className="text-muted-foreground">• {tip}</li>
              ))}
            </ul>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}