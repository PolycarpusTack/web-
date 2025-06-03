import React, { useState, useRef, useEffect } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { File, Image, Loader2, Mic, Paperclip, Send, Settings, Plus, X } from "lucide-react";
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

interface MessageInputProps {
  onSend: (message: string, files?: File[]) => Promise<void>;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  showModelSettings?: boolean;
  initialModelSettings?: ModelSettings;
  onModelSettingsChange?: (settings: ModelSettings) => void;
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

export const MessageInput: React.FC<MessageInputProps> = ({
  onSend,
  placeholder = 'Type a message...',
  disabled = false,
  loading = false,
  className,
  showModelSettings = true,
  initialModelSettings,
  onModelSettingsChange
}) => {
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
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

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      // Convert FileList to array and add to state
      const newFiles = Array.from(e.target.files);
      setFiles(prevFiles => [...prevFiles, ...newFiles]);
    }
  };

  // Remove a file from the selection
  const handleRemoveFile = (index: number) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  // Handle message submission
  const handleSubmit = async () => {
    if ((!message.trim() && files.length === 0) || disabled) return;
    
    try {
      await onSend(message, files.length > 0 ? files : undefined);
      setMessage('');
      setFiles([]);
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
      {/* File previews */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {files.map((file, index) => (
            <div 
              key={index} 
              className="flex items-center bg-muted rounded-md p-2 pr-3 text-sm"
            >
              {file.type.startsWith('image/') ? (
                <Image className="h-4 w-4 mr-2 text-muted-foreground" />
              ) : (
                <File className="h-4 w-4 mr-2 text-muted-foreground" />
              )}
              <span className="max-w-[150px] truncate">{file.name}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-5 w-5 ml-1"
                onClick={() => handleRemoveFile(index)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ))}
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
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-10 w-10"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={disabled || loading}
                >
                  <Paperclip className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Upload files</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            multiple
            onChange={handleFileSelect}
            accept="image/*,.pdf,.doc,.docx,.txt,.md"
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

export default MessageInput;