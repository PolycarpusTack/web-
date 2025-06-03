// src/components/chat/EnhancedMessageInput.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Loader2, Mic, Send, Settings, Plus } from "lucide-react";
import { cn } from '@/components/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import FileUploadButton from './FileUploadButton';
import FileAttachments from './FileAttachments';

interface FileAttachment {
  id: string;
  filename: string;
  originalFilename?: string;
  contentType: string;
  size: number;
  url?: string;
}

interface EnhancedMessageInputProps {
  onSend: (message: string, files?: File[]) => Promise<void>;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  showModelSettings?: boolean;
  initialModelSettings?: ModelSettings;
  onModelSettingsChange?: (settings: ModelSettings) => void;
  conversationId?: string;
}

export interface ModelSettings {
  temperature: number;
  maxTokens: number;
  topP: number;
  streamResponse: boolean;
  systemPrompt?: string;
}

const DEFAULT_MODEL_SETTINGS: ModelSettings = {
  temperature: 0.7,
  maxTokens: 2000,
  topP: 0.95,
  streamResponse: true,
  systemPrompt: ''
};

export const EnhancedMessageInput: React.FC<EnhancedMessageInputProps> = ({
  onSend,
  placeholder = 'Type a message...',
  disabled = false,
  loading = false,
  className,
  showModelSettings = true,
  initialModelSettings,
  onModelSettingsChange,
  conversationId
}) => {
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [fileAttachments, setFileAttachments] = useState<FileAttachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [modelSettings, setModelSettings] = useState<ModelSettings>(
    initialModelSettings || DEFAULT_MODEL_SETTINGS
  );
  
  // Auto-resize textarea as content grows
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  // Handle files selected from FileUploadButton
  const handleFilesSelected = (selectedFiles: File[]) => {
    // Create temporary attachments with local URLs
    const newAttachments = selectedFiles.map(file => ({
      id: `temp-${Date.now()}-${file.name}`,
      filename: file.name,
      originalFilename: file.name,
      contentType: file.type,
      size: file.size,
      url: URL.createObjectURL(file)
    }));
    
    setFiles(prev => [...prev, ...selectedFiles]);
    setFileAttachments(prev => [...prev, ...newAttachments]);
  };

  // Remove a file from the selection
  const handleRemoveFile = (fileId: string) => {
    const index = fileAttachments.findIndex(attachment => attachment.id === fileId);
    if (index !== -1) {
      // Remove from files array
      setFiles(prev => prev.filter((_, i) => i !== index));
      
      // Remove from attachments
      setFileAttachments(prev => prev.filter(attachment => attachment.id !== fileId));
      
      // Revoke URL if it's a blob URL
      const attachment = fileAttachments[index];
      if (attachment.url?.startsWith('blob:')) {
        URL.revokeObjectURL(attachment.url);
      }
    }
  };

  // Handle message submission
  const handleSubmit = async () => {
    if ((!message.trim() && files.length === 0) || disabled) return;
    
    try {
      await onSend(message, files.length > 0 ? files : undefined);
      
      // Clean up
      setMessage('');
      
      // Revoke any blob URLs to prevent memory leaks
      fileAttachments.forEach(attachment => {
        if (attachment.url?.startsWith('blob:')) {
          URL.revokeObjectURL(attachment.url);
        }
      });
      
      setFiles([]);
      setFileAttachments([]);
      
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  // Handle keyboard shortcuts (Enter to send, Shift+Enter for new line)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Handle model settings changes
  const handleModelSettingChange = (key: keyof ModelSettings, value: any) => {
    const newSettings = { ...modelSettings, [key]: value };
    setModelSettings(newSettings);
    if (onModelSettingsChange) {
      onModelSettingsChange(newSettings);
    }
  };

  return (
    <div className={cn("p-4 border-t bg-background", className)}>
      {/* File attachments */}
      {fileAttachments.length > 0 && (
        <div className="mb-3">
          <FileAttachments
            files={fileAttachments}
            onRemove={handleRemoveFile}
            allowRemove={true}
            compact={true}
          />
        </div>
      )}
      
      {/* Main input area */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="min-h-[80px] pr-12 resize-none"
            disabled={disabled || loading}
          />
          
          {/* Emoji picker trigger (placeholder) */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 bottom-2 h-8 w-8 opacity-60 hover:opacity-100"
                  disabled={disabled || loading}
                >
                  <Plus className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Add emoji (coming soon)</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        
        {/* Button actions */}
        <div className="flex items-center gap-1">
          {/* File upload */}
          <FileUploadButton
            onFilesSelected={handleFilesSelected}
            disabled={disabled || loading}
            maxFiles={5}
          />
          
          {/* Voice input (placeholder) */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-10 w-10"
                  disabled={disabled || loading}
                >
                  <Mic className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Voice input (coming soon)</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          {/* Model settings */}
          {showModelSettings && (
            <Popover>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <PopoverTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-10 w-10"
                        disabled={disabled || loading}
                      >
                        <Settings className="h-5 w-5" />
                      </Button>
                    </PopoverTrigger>
                  </TooltipTrigger>
                  <TooltipContent>Model settings</TooltipContent>
                </Tooltip>
              </TooltipProvider>
              
              <PopoverContent className="w-72">
                <div className="space-y-4">
                  <h4 className="font-medium">Model Settings</h4>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="temperature">Temperature: {modelSettings.temperature}</Label>
                    </div>
                    <Slider
                      id="temperature"
                      min={0}
                      max={2}
                      step={0.1}
                      value={[modelSettings.temperature]}
                      onValueChange={([value]) => handleModelSettingChange('temperature', value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Controls randomness: Lower values are more deterministic, higher values more creative.
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="maxTokens">Max tokens: {modelSettings.maxTokens}</Label>
                    </div>
                    <Slider
                      id="maxTokens"
                      min={100}
                      max={4000}
                      step={100}
                      value={[modelSettings.maxTokens]}
                      onValueChange={([value]) => handleModelSettingChange('maxTokens', value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Maximum number of tokens to generate.
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="topP">Top P: {modelSettings.topP}</Label>
                    </div>
                    <Slider
                      id="topP"
                      min={0.1}
                      max={1}
                      step={0.05}
                      value={[modelSettings.topP]}
                      onValueChange={([value]) => handleModelSettingChange('topP', value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Controls diversity via nucleus sampling.
                    </p>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="stream"
                      checked={modelSettings.streamResponse}
                      onCheckedChange={(checked) => handleModelSettingChange('streamResponse', checked)}
                    />
                    <Label htmlFor="stream">Stream response</Label>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          )}
          
          {/* Send button */}
          <Button
            onClick={handleSubmit}
            disabled={(!message.trim() && files.length === 0) || disabled || loading}
            size="icon"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default EnhancedMessageInput;