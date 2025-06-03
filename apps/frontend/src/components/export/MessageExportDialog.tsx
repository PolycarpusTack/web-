import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import {
  Download,
  FileText,
  File,
  FileSpreadsheet,
  FileCode,
  Globe,
  Settings,
  Clock,
  Users,
  Brain,
  CheckCircle,
  AlertTriangle,
  Info,
  Calendar
} from 'lucide-react';

interface ExportFormat {
  name: string;
  description: string;
  supports_metadata: boolean;
  supports_formatting: boolean;
  file_extension: string;
  available: boolean;
}

interface ExportOptions {
  conversation_ids: string[];
  format: string;
  include_metadata: boolean;
  include_system_messages: boolean;
  include_timestamps: boolean;
  include_user_info: boolean;
  include_model_info: boolean;
  date_from?: string;
  date_to?: string;
  compress: boolean;
  custom_template?: string;
}

interface MessageExportDialogProps {
  conversationIds: string[];
  trigger?: React.ReactNode;
  onExportComplete?: (filename: string) => void;
}

const FORMAT_ICONS = {
  json: FileCode,
  csv: FileSpreadsheet,
  pdf: File,
  docx: File,
  md: FileText,
  html: Globe
};

const FORMAT_COLORS = {
  json: 'text-green-600',
  csv: 'text-blue-600',
  pdf: 'text-red-600',
  docx: 'text-blue-700',
  md: 'text-purple-600',
  html: 'text-orange-600'
};

export const MessageExportDialog: React.FC<MessageExportDialogProps> = ({
  conversationIds,
  trigger,
  onExportComplete
}) => {
  const [open, setOpen] = useState(false);
  const [formats, setFormats] = useState<Record<string, ExportFormat>>({});
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [options, setOptions] = useState<ExportOptions>({
    conversation_ids: conversationIds,
    format: 'json',
    include_metadata: true,
    include_system_messages: false,
    include_timestamps: true,
    include_user_info: false,
    include_model_info: true,
    compress: false
  });
  
  const { toast } = useToast();
  
  // Load supported formats on mount
  useEffect(() => {
    loadFormats();
  }, []);
  
  // Update conversation IDs when prop changes
  useEffect(() => {
    setOptions(prev => ({ ...prev, conversation_ids: conversationIds }));
  }, [conversationIds]);
  
  const loadFormats = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/export/formats');
      if (response.ok) {
        const data = await response.json();
        setFormats(data.supported_formats);
        
        // Set default format to first available format
        const availableFormats = Object.entries(data.supported_formats)
          .filter(([_, format]) => (format as any)?.available);
        
        if (availableFormats.length > 0 && !options.format) {
          setOptions(prev => ({ ...prev, format: availableFormats[0][0] }));
        }
      }
    } catch (error) {
      console.error('Failed to load export formats:', error);
      toast({
        title: "Failed to load export formats",
        description: "Please refresh and try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleExport = async () => {
    if (options.conversation_ids.length === 0) {
      toast({
        title: "No conversations selected",
        description: "Please select at least one conversation to export.",
        variant: "destructive",
      });
      return;
    }
    
    setExporting(true);
    
    try {
      const response = await fetch('/api/export/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      });
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }
      
      // Get filename from response headers
      const contentDisposition = response.headers.get('content-disposition');
      const filenameMatch = contentDisposition?.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      const filename = filenameMatch ? filenameMatch[1].replace(/['"]/g, '') : `export.${options.format}`;
      
      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setOpen(false);
      onExportComplete?.(filename);
      
      toast({
        title: "Export completed",
        description: `Successfully exported ${options.conversation_ids.length} conversation(s) as ${options.format.toUpperCase()}`,
      });
      
    } catch (error: any) {
      console.error('Export failed:', error);
      toast({
        title: "Export failed",
        description: error.message || "Please try again.",
        variant: "destructive",
      });
    } finally {
      setExporting(false);
    }
  };
  
  const updateOption = <K extends keyof ExportOptions>(key: K, value: ExportOptions[K]) => {
    setOptions(prev => ({ ...prev, [key]: value }));
  };
  
  const getFormatDescription = (formatKey: string) => {
    const format = formats[formatKey];
    if (!format) return '';
    
    const features = [];
    if (format.supports_metadata) features.push('Metadata');
    if (format.supports_formatting) features.push('Rich formatting');
    
    return `${format.description}${features.length > 0 ? ` • Supports: ${features.join(', ')}` : ''}`;
  };
  
  const getEstimatedFileSize = () => {
    const avgMessageSize = 200; // bytes
    const messagesCount = options.conversation_ids.length * 20; // estimate 20 messages per conversation
    let baseSize = messagesCount * avgMessageSize;
    
    // Adjust based on format
    const multipliers = {
      json: 1.5,
      csv: 0.8,
      pdf: 3.0,
      docx: 2.5,
      md: 1.2,
      html: 2.0
    };
    
    baseSize *= multipliers[options.format as keyof typeof multipliers] || 1;
    
    if (options.include_metadata) baseSize *= 1.3;
    if (options.include_timestamps) baseSize *= 1.1;
    if (options.include_user_info) baseSize *= 1.1;
    
    // Format size
    if (baseSize < 1024) return `${Math.round(baseSize)} B`;
    if (baseSize < 1024 * 1024) return `${Math.round(baseSize / 1024)} KB`;
    return `${Math.round(baseSize / (1024 * 1024))} MB`;
  };
  
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Export Conversations
          </DialogTitle>
          <DialogDescription>
            Export {conversationIds.length} conversation{conversationIds.length !== 1 ? 's' : ''} in your preferred format
          </DialogDescription>
        </DialogHeader>
        
        {loading ? (
          <div className="space-y-4">
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-muted rounded w-3/4"></div>
              <div className="h-4 bg-muted rounded w-1/2"></div>
              <div className="h-4 bg-muted rounded w-5/6"></div>
            </div>
          </div>
        ) : (
          <Tabs defaultValue="format" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="format">Format</TabsTrigger>
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="filters">Filters</TabsTrigger>
            </TabsList>
            
            <TabsContent value="format" className="space-y-4">
              <div>
                <Label className="text-base font-medium">Export Format</Label>
                <p className="text-sm text-muted-foreground mb-3">
                  Choose the format for your exported conversations
                </p>
                
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(formats).map(([key, format]) => {
                    const IconComponent = FORMAT_ICONS[key as keyof typeof FORMAT_ICONS] || FileText;
                    const colorClass = FORMAT_COLORS[key as keyof typeof FORMAT_COLORS] || 'text-gray-600';
                    
                    return (
                      <div
                        key={key}
                        className={`relative p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                          options.format === key
                            ? 'border-primary bg-primary/5'
                            : format.available
                            ? 'border-border hover:border-primary/50'
                            : 'border-muted bg-muted/50 cursor-not-allowed'
                        }`}
                        onClick={() => format.available && updateOption('format', key)}
                      >
                        <div className="flex items-start gap-3">
                          <IconComponent className={`h-5 w-5 mt-0.5 ${colorClass}`} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{format.name}</span>
                              {!format.available && (
                                <Badge variant="secondary" className="text-xs">
                                  Unavailable
                                </Badge>
                              )}
                              {options.format === key && (
                                <CheckCircle className="h-4 w-4 text-primary" />
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                              {getFormatDescription(key)}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                {/* Format preview */}
                {options.format && formats[options.format] && (
                  <Alert className="mt-4">
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      <strong>{formats[options.format].name} Export:</strong>{' '}
                      {formats[options.format].description}
                      <br />
                      <span className="text-xs">
                        Estimated file size: {getEstimatedFileSize()}
                      </span>
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </TabsContent>
            
            <TabsContent value="content" className="space-y-4">
              <div>
                <Label className="text-base font-medium">Content Options</Label>
                <p className="text-sm text-muted-foreground mb-4">
                  Customize what information to include in the export
                </p>
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="include_timestamps"
                        checked={options.include_timestamps}
                        onCheckedChange={(checked) => updateOption('include_timestamps', !!checked)}
                      />
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor="include_timestamps" className="text-sm">
                          Include timestamps
                        </Label>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="include_user_info"
                        checked={options.include_user_info}
                        onCheckedChange={(checked) => updateOption('include_user_info', !!checked)}
                      />
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor="include_user_info" className="text-sm">
                          Include user info
                        </Label>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="include_model_info"
                        checked={options.include_model_info}
                        onCheckedChange={(checked) => updateOption('include_model_info', !!checked)}
                      />
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor="include_model_info" className="text-sm">
                          Include model info
                        </Label>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="include_metadata"
                        checked={options.include_metadata}
                        onCheckedChange={(checked) => updateOption('include_metadata', !!checked)}
                      />
                      <div className="flex items-center gap-2">
                        <Settings className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor="include_metadata" className="text-sm">
                          Include metadata
                        </Label>
                      </div>
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="include_system_messages"
                        checked={options.include_system_messages}
                        onCheckedChange={(checked) => updateOption('include_system_messages', !!checked)}
                      />
                      <Label htmlFor="include_system_messages" className="text-sm">
                        Include system messages
                      </Label>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="compress"
                        checked={options.compress}
                        onCheckedChange={(checked) => updateOption('compress', !!checked)}
                      />
                      <Label htmlFor="compress" className="text-sm">
                        Compress as ZIP file
                      </Label>
                    </div>
                  </div>
                  
                  {options.include_metadata && (
                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription className="text-xs">
                        Metadata includes token counts, costs, processing times, and other technical information.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="filters" className="space-y-4">
              <div>
                <Label className="text-base font-medium">Date Filters</Label>
                <p className="text-sm text-muted-foreground mb-4">
                  Filter messages by date range (optional)
                </p>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="date_from" className="text-sm">From Date</Label>
                    <Input
                      id="date_from"
                      type="date"
                      value={options.date_from || ''}
                      onChange={(e) => updateOption('date_from', e.target.value || undefined)}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="date_to" className="text-sm">To Date</Label>
                    <Input
                      id="date_to"
                      type="date"
                      value={options.date_to || ''}
                      onChange={(e) => updateOption('date_to', e.target.value || undefined)}
                    />
                  </div>
                </div>
                
                {(options.date_from || options.date_to) && (
                  <Alert className="mt-4">
                    <Calendar className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      Only messages within the specified date range will be included in the export.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
              
              <Separator />
              
              <div>
                <Label htmlFor="custom_template" className="text-sm font-medium">
                  Custom Template (Advanced)
                </Label>
                <p className="text-sm text-muted-foreground mb-2">
                  Custom formatting template for supported formats
                </p>
                <Textarea
                  id="custom_template"
                  placeholder="Enter custom template (format-specific)"
                  value={options.custom_template || ''}
                  onChange={(e) => updateOption('custom_template', e.target.value || undefined)}
                  rows={3}
                />
              </div>
            </TabsContent>
          </Tabs>
        )}
        
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={exporting}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={loading || exporting || !options.format}>
            {exporting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Exporting...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Export {conversationIds.length} Conversation{conversationIds.length !== 1 ? 's' : ''}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};