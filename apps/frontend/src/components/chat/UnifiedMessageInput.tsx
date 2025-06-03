import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { 
  File as FileIcon, 
  Image, 
  Loader2, 
  Mic, 
  Paperclip, 
  Send, 
  Settings, 
  Plus, 
  X,
  FileText,
  FileCode,
  Archive
} from "lucide-react";
import { cn } from '@/lib/utils';
import { FilePreviewList, FileAttachment } from '@/components/shared/FilePreviewList';
import { LoadingButton } from '@/components/ui/loading-button';
import { useModelSettings } from '@/hooks/useModelSettings';
import { useToast } from '@/components/ui/use-toast';
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
import { filesApi } from '@/api';

interface UnifiedMessageInputProps {
  onSend: (message: string, files?: File[]) => Promise<void>;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  enhanced?: boolean;
  showModelSettings?: boolean;
  initialModelSettings?: Parameters<typeof useModelSettings>[0];
  onModelSettingsChange?: (settings: ReturnType<typeof useModelSettings>['settings']) => void;
  conversationId?: string;
  maxFiles?: number;
  maxFileSize?: number;
  acceptedFileTypes?: string[];
  showVoiceInput?: boolean;
}

const ACCEPTED_FILE_TYPES = [
  'text/plain',
  'text/markdown',
  'text/csv',
  'application/pdf',
  'application/json',
  'application/xml',
  'image/png',
  'image/jpeg',
  'image/gif',
  'image/webp',
  'application/zip',
  'application/x-zip-compressed'
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_FILES = 5;

export const UnifiedMessageInput: React.FC<UnifiedMessageInputProps> = ({
  onSend,
  placeholder = 'Type a message...',
  disabled = false,
  loading = false,
  className,
  enhanced = false,
  showModelSettings = false,
  initialModelSettings,
  onModelSettingsChange,
  conversationId,
  maxFiles = MAX_FILES,
  maxFileSize = MAX_FILE_SIZE,
  acceptedFileTypes = ACCEPTED_FILE_TYPES,
  showVoiceInput = false,
}) => {
  const [message, setMessage] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<FileAttachment[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [modelSettingsOpen, setModelSettingsOpen] = useState(false);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  
  const { settings, updateSetting, resetSettings } = useModelSettings(initialModelSettings);

  // Notify parent of settings changes
  useEffect(() => {
    if (onModelSettingsChange) {
      onModelSettingsChange(settings);
    }
  }, [settings, onModelSettingsChange]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 200)}px`;
    }
  }, [message]);

  const handleSend = async () => {
    if ((!message.trim() && attachedFiles.length === 0) || loading || isUploading) return;

    try {
      const filesToSend = attachedFiles.map(a => a.file);
      await onSend(message, filesToSend);
      setMessage('');
      setAttachedFiles([]);
    } catch (error) {
      console.error('Failed to send message:', error);
      toast({
        title: "Failed to send message",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles: FileAttachment[] = [];
    const errors: string[] = [];

    files.forEach(file => {
      if (attachedFiles.length + validFiles.length >= maxFiles) {
        errors.push(`Maximum ${maxFiles} files allowed`);
        return;
      }

      if (file.size > maxFileSize) {
        errors.push(`${file.name} exceeds ${maxFileSize / 1024 / 1024}MB limit`);
        return;
      }

      if (!acceptedFileTypes.includes(file.type)) {
        errors.push(`${file.name} has unsupported file type`);
        return;
      }

      const attachment: FileAttachment = {
        id: `${Date.now()}-${Math.random()}`,
        file,
        uploading: false
      };

      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setAttachedFiles(prev => 
            prev.map(a => a.id === attachment.id 
              ? { ...a, preview: e.target?.result as string }
              : a
            )
          );
        };
        reader.readAsDataURL(file);
      }

      validFiles.push(attachment);
    });

    if (errors.length > 0) {
      toast({
        title: "File upload errors",
        description: errors.join('\n'),
        variant: "destructive"
      });
    }

    setAttachedFiles(prev => [...prev, ...validFiles]);
    
    // Reset input
    if (e.target) {
      e.target.value = '';
    }
  };

  const removeFile = (id: string) => {
    setAttachedFiles(prev => prev.filter(f => f.id !== id));
  };

  const handleVoiceInput = async () => {
    if (!showVoiceInput) return;

    if (isRecording) {
      // Stop recording
      setIsRecording(false);
      toast({
        title: "Voice recording stopped",
        description: "Voice input feature coming soon!",
      });
    } else {
      // Start recording
      setIsRecording(true);
      toast({
        title: "Voice recording started",
        description: "Voice input feature coming soon!",
      });
    }
  };

  const ModelSettingsPopover = () => (
    <Popover open={modelSettingsOpen} onOpenChange={setModelSettingsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          disabled={disabled}
        >
          <Settings className="h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">Model Settings</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={resetSettings}
              className="h-7 text-xs"
            >
              Reset
            </Button>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between">
                <Label className="text-sm">Temperature</Label>
                <span className="text-xs text-muted-foreground">
                  {settings.temperature}
                </span>
              </div>
              <Slider
                value={[settings.temperature]}
                onValueChange={([v]) => updateSetting('temperature', v)}
                min={0}
                max={2}
                step={0.1}
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Controls randomness: 0 = focused, 2 = creative
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <Label className="text-sm">Max Tokens</Label>
                <span className="text-xs text-muted-foreground">
                  {settings.maxTokens}
                </span>
              </div>
              <Slider
                value={[settings.maxTokens]}
                onValueChange={([v]) => updateSetting('maxTokens', v)}
                min={100}
                max={4000}
                step={100}
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Maximum response length
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <Label className="text-sm">Top P</Label>
                <span className="text-xs text-muted-foreground">
                  {settings.topP}
                </span>
              </div>
              <Slider
                value={[settings.topP]}
                onValueChange={([v]) => updateSetting('topP', v)}
                min={0}
                max={1}
                step={0.05}
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Nucleus sampling threshold
              </p>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="stream" className="text-sm">
                Stream Response
              </Label>
              <Switch
                id="stream"
                checked={settings.streamResponse}
                onCheckedChange={(v) => updateSetting('streamResponse', v)}
              />
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );

  return (
    <div className={cn("relative", className)}>
      {/* File previews */}
      {attachedFiles.length > 0 && (
        <div className="mb-2">
          <FilePreviewList
            files={attachedFiles}
            onRemove={removeFile}
            compact={!enhanced}
          />
        </div>
      )}

      {/* Input area */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || loading || isUploading}
            className={cn(
              "min-h-[44px] max-h-[200px] resize-none pr-12",
              "scrollbar-thin scrollbar-thumb-muted",
              enhanced && "pr-24"
            )}
            rows={1}
          />
          
          {/* Inline action buttons */}
          <div className="absolute bottom-2 right-2 flex items-center gap-1">
            {enhanced && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={disabled || attachedFiles.length >= maxFiles}
                    >
                      <Paperclip className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Attach files</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            
            {showVoiceInput && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        "h-8 w-8",
                        isRecording && "text-red-500"
                      )}
                      onClick={handleVoiceInput}
                      disabled={disabled}
                    >
                      <Mic className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {isRecording ? "Stop recording" : "Start voice input"}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1">
          {showModelSettings && <ModelSettingsPopover />}
          
          <LoadingButton
            onClick={handleSend}
            disabled={(!message.trim() && attachedFiles.length === 0) || disabled || isUploading}
            loading={loading}
            size="icon"
            className="h-10 w-10"
          >
            <Send className="h-4 w-4" />
          </LoadingButton>
        </div>
      </div>

      {/* Hidden file input */}
      {enhanced && (
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedFileTypes.join(',')}
          onChange={handleFileSelect}
          className="hidden"
        />
      )}
    </div>
  );
};