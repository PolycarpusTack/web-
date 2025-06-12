import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useSearchParams, useParams } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { toast } from '@/components/ui/use-toast';
import { Skeleton } from '@/components/ui/skeleton';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

import { 
  MoreHorizontal,
  Settings,
  Save,
  Play,
  Pause,
  Square,
  Download,
  Upload,
  Copy,
  Eye,
  EyeOff,
  Plus,
  X,
  Sliders,
  Code,
  Globe,
  Bot,
  Zap,
  GitBranch,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Info,
  ChevronLeft,
  ChevronRight,
  FlaskConical
} from 'lucide-react';

import { getPipeline, updatePipeline, createPipelineStep, updatePipelineStep, reorderPipelineSteps, deletePipelineStep, executePipeline } from '@/api/pipelines';
import { getModels } from '@/api/models';
import { PipelinePreview } from '@/components/pipeline/PipelinePreview';
import { PipelineGitHubSync } from '@/components/pipeline/PipelineGitHubSync';
import { PipelineDefinition, StepType, PipelineExecutionOptions } from '@/types/pipeline';

// Types
interface Pipeline {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  is_active: boolean;
  is_public: boolean;
  version: string;
  tags: string[];
  steps: PipelineStep[];
}

interface PipelineStep {
  id: string;
  pipeline_id: string;
  name: string;
  description: string;
  type: string;
  order: number;
  config: any;
  input_mapping: Record<string, any>;
  output_mapping: Record<string, any>;
  is_enabled: boolean;
  timeout: number | null;
  retry_config: any;
  created_at: string;
  updated_at: string;
}

interface Model {
  id: string;
  name: string;
}

// Step type definitions and icons
const STEP_TYPES = [
  { id: 'prompt', name: 'AI Prompt', description: 'Send a prompt to an AI model', color: 'bg-purple-600', icon: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
      <path d="M7.5 1.5C4.5 1.5 1.5 3.5 1.5 7.5C1.5 11.5 4.5 13.5 7.5 13.5C10.5 13.5 13.5 11.5 13.5 7.5C13.5 3.5 10.5 1.5 7.5 1.5ZM7.5 3C9.5 3 10.5 4 10.5 5C10.5 6 9.5 7 7.5 7C5.5 7 4.5 6 4.5 5C4.5 4 5.5 3 7.5 3ZM4.5 9C4.5 8 5.5 7 7.5 7C9.5 7 10.5 8 10.5 9C10.5 10 9.5 11 7.5 11C5.5 11 4.5 10 4.5 9Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
    </svg>
  )},
  { id: 'code', name: 'Code Execution', description: 'Execute code and process the result', color: 'bg-amber-600', icon: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
      <path d="M9.96424 2.68571C10.0668 2.42931 9.94209 2.13833 9.6857 2.03577C9.4293 1.93322 9.13832 2.05792 9.03576 2.31432L5.03576 12.3143C4.9332 12.5707 5.05791 12.8617 5.3143 12.9642C5.5707 13.0668 5.86168 12.9421 5.96424 12.6857L9.96424 2.68571ZM3.85355 5.14645C4.04882 5.34171 4.04882 5.65829 3.85355 5.85355L2.20711 7.5L3.85355 9.14645C4.04882 9.34171 4.04882 9.65829 3.85355 9.85355C3.65829 10.0488 3.34171 10.0488 3.14645 9.85355L1.14645 7.85355C0.951184 7.65829 0.951184 7.34171 1.14645 7.14645L3.14645 5.14645C3.34171 4.95118 3.65829 4.95118 3.85355 5.14645ZM11.1464 5.14645C11.3417 4.95118 11.6583 4.95118 11.8536 5.14645L13.8536 7.14645C14.0488 7.34171 14.0488 7.65829 13.8536 7.85355L11.8536 9.85355C11.6583 10.0488 11.3417 10.0488 11.1464 9.85355C10.9512 9.65829 10.9512 9.34171 11.1464 9.14645L12.7929 7.5L11.1464 5.85355C10.9512 5.65829 10.9512 5.34171 11.1464 5.14645Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
    </svg>
  )},
  { id: 'file', name: 'File Operation', description: 'Read from or write to a file', color: 'bg-blue-600', icon: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
      <path d="M3.5 2C3.22386 2 3 2.22386 3 2.5V12.5C3 12.7761 3.22386 13 3.5 13H11.5C11.7761 13 12 12.7761 12 12.5V6H8.5C8.22386 6 8 5.77614 8 5.5V2H3.5ZM9 2.70711L11.2929 5H9V2.70711ZM2 2.5C2 1.67157 2.67157 1 3.5 1H8.5C8.63261 1 8.75979 1.05268 8.85355 1.14645L12.8536 5.14645C12.9473 5.24021 13 5.36739 13 5.5V12.5C13 13.3284 12.3284 14 11.5 14H3.5C2.67157 14 2 13.3284 2 12.5V2.5Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
    </svg>
  )},
  { id: 'api', name: 'API Call', description: 'Make an HTTP request to an external service', color: 'bg-green-600', icon: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
      <path d="M7.49991 0.876892C3.84222 0.876892 0.877075 3.84204 0.877075 7.49972C0.877075 11.1574 3.84222 14.1226 7.49991 14.1226C11.1576 14.1226 14.1227 11.1574 14.1227 7.49972C14.1227 3.84204 11.1576 0.876892 7.49991 0.876892ZM1.82707 7.49972C1.82707 4.36671 4.36689 1.82689 7.49991 1.82689C10.6329 1.82689 13.1727 4.36671 13.1727 7.49972C13.1727 10.6327 10.6329 13.1726 7.49991 13.1726C4.36689 13.1726 1.82707 10.6327 1.82707 7.49972ZM7.50003 4C7.77617 4 8.00003 4.22386 8.00003 4.5V7H9.50003C9.77617 7 10 7.22386 10 7.5C10 7.77614 9.77617 8 9.50003 8H7.50003C7.22389 8 7.00003 7.77614 7.00003 7.5V4.5C7.00003 4.22386 7.22389 4 7.50003 4Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
    </svg>
  )},
  { id: 'condition', name: 'Condition', description: 'Evaluate a condition to control pipeline flow', color: 'bg-orange-600', icon: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
      <path d="M7.14645 2.14645C7.34171 1.95118 7.65829 1.95118 7.85355 2.14645L11.8536 6.14645C12.0488 6.34171 12.0488 6.65829 11.8536 6.85355C11.6583 7.04882 11.3417 7.04882 11.1464 6.85355L7.5 3.20711L3.85355 6.85355C3.65829 7.04882 3.34171 7.04882 3.14645 6.85355C2.95118 6.65829 2.95118 6.34171 3.14645 6.14645L7.14645 2.14645ZM7.85355 12.8536C7.65829 13.0488 7.34171 13.0488 7.14645 12.8536L3.14645 8.85355C2.95118 8.65829 2.95118 8.34171 3.14645 8.14645C3.34171 7.95118 3.65829 7.95118 3.85355 8.14645L7.5 11.7929L11.1464 8.14645C11.3417 7.95118 11.6583 7.95118 11.8536 8.14645C12.0488 8.34171 12.0488 8.65829 11.8536 8.85355L7.85355 12.8536Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
    </svg>
  )},
  { id: 'transform', name: 'Transform', description: 'Transform data from one format to another', color: 'bg-pink-600', icon: (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-5 w-5">
      <path d="M5.5 15H4L4 1H5.5L5.5 15ZM11 15H9.5L9.5 1H11L11 15ZM7.5 1H8.95V15H7.5V1ZM1 1H2.5V15H1V1ZM13 1H14.5V15H13V1Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
    </svg>
  )}
];

// Step config forms by type
const StepConfigForms = {
  prompt: ({ step, onChange, models = [] }: { 
    step: PipelineStep, 
    onChange: (config: any) => void,
    models: Model[]
  }) => {
    return (
      <div className="space-y-4">
        <div>
          <Label className="text-slate-300">Model</Label>
          <Select 
            value={step.config?.model_id} 
            onValueChange={(value) => onChange({ ...step.config, model_id: value })}
          >
            <SelectTrigger className="bg-slate-800 border-slate-700 text-slate-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              {models.map(model => (
                <SelectItem key={model.id} value={model.id} className="text-slate-200">
                  {model.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label className="text-slate-300">System Prompt (optional)</Label>
          <Textarea 
            className="bg-slate-800 border-slate-700 text-slate-200 min-h-[80px]" 
           
            value={step.config?.system_prompt || ""}
            onChange={(e) => onChange({ ...step.config, system_prompt: e.target.value })}
          />
        </div>
        
        <div>
          <Label className="text-slate-300">Prompt</Label>
          <Textarea 
            className="bg-slate-800 border-slate-700 text-slate-200 min-h-[120px]" 
           
            value={step.config?.prompt || ""}
            onChange={(e) => onChange({ ...step.config, prompt: e.target.value })}
          />
        </div>
        
        <div>
          <Label className="text-slate-300">Model Parameters</Label>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-slate-400 text-xs">Temperature</Label>
                  <div className="flex">
                    <Input
                      type="number"
                      min="0"
                      max="2"
                      step="0.1"
                      className="bg-slate-900 border-slate-700 text-slate-200 rounded-r-none"
                      value={step.config?.options?.temperature || 0.7}
                      onChange={(e) => onChange({
                        ...step.config,
                        options: { ...(step.config?.options || {}), temperature: parseFloat(e.target.value) }
                      })}
                    />
                    <div className="bg-slate-700 px-2 flex items-center rounded-r-md text-slate-300 text-xs">
                      0-2
                    </div>
                  </div>
                </div>
                
                <div>
                  <Label className="text-slate-400 text-xs">Max Tokens</Label>
                  <div className="flex">
                    <Input
                      type="number"
                      min="1"
                      className="bg-slate-900 border-slate-700 text-slate-200 rounded-r-none"
                      value={step.config?.options?.max_tokens || 1024}
                      onChange={(e) => onChange({
                        ...step.config,
                        options: { ...(step.config?.options || {}), max_tokens: parseInt(e.target.value) }
                      })}
                    />
                    <div className="bg-slate-700 px-2 flex items-center rounded-r-md text-slate-300 text-xs">
                      tokens
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-slate-400 text-xs">Top P</Label>
                  <div className="flex">
                    <Input
                      type="number"
                      min="0"
                      max="1"
                      step="0.05"
                      className="bg-slate-900 border-slate-700 text-slate-200 rounded-r-none"
                      value={step.config?.options?.top_p || 0.95}
                      onChange={(e) => onChange({
                        ...step.config,
                        options: { ...(step.config?.options || {}), top_p: parseFloat(e.target.value) }
                      })}
                    />
                    <div className="bg-slate-700 px-2 flex items-center rounded-r-md text-slate-300 text-xs">
                      0-1
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2 mt-4">
                  <Switch
                    id="stream"
                    checked={step.config?.options?.stream || false}
                    onCheckedChange={(checked) => onChange({
                      ...step.config,
                      options: { ...(step.config?.options || {}), stream: checked }
                    })}
                  />
                  <Label htmlFor="stream" className="text-slate-300 text-xs">Enable Streaming</Label>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  },
  
  code: ({ step, onChange }: { step: PipelineStep, onChange: (config: any) => void }) => {
    return (
      <div className="space-y-4">
        <div>
          <Label className="text-slate-300">Language</Label>
          <Select 
            value={step.config?.language || "python"} 
            onValueChange={(value) => onChange({ ...step.config, language: value })}
          >
            <SelectTrigger className="bg-slate-800 border-slate-700 text-slate-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="python" className="text-slate-200">Python</SelectItem>
              <SelectItem value="javascript" className="text-slate-200">JavaScript</SelectItem>
              <SelectItem value="typescript" className="text-slate-200">TypeScript</SelectItem>
              <SelectItem value="bash" className="text-slate-200">Bash</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label className="text-slate-300">Code</Label>
          <Textarea 
            className="bg-slate-800 border-slate-700 text-slate-200 min-h-[200px] font-mono" 
           
            value={step.config?.code || ""}
            onChange={(e) => onChange({ ...step.config, code: e.target.value })}
          />
        </div>
        
        <div>
          <Label className="text-slate-300 flex items-center">
            <span>Timeout</span>
            <span className="ml-2 text-xs text-slate-400">(in seconds, leave empty for no timeout)</span>
          </Label>
          <Input
            type="number"
            min="1"
            className="bg-slate-800 border-slate-700 text-slate-200"
            value={step.config?.timeout || ""}
            onChange={(e) => onChange({ 
              ...step.config, 
              timeout: e.target.value ? parseInt(e.target.value) : null 
            })}
          />
        </div>
      </div>
    );
  },
  
  file: ({ step, onChange }: { step: PipelineStep, onChange: (config: any) => void }) => {
    return (
      <div className="space-y-4">
        <div>
          <Label className="text-slate-300">Operation</Label>
          <Select 
            value={step.config?.operation || "read"} 
            onValueChange={(value) => onChange({ ...step.config, operation: value })}
          >
            <SelectTrigger className="bg-slate-800 border-slate-700 text-slate-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="read" className="text-slate-200">Read File</SelectItem>
              <SelectItem value="write" className="text-slate-200">Write File</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label className="text-slate-300">File Path</Label>
          <Input 
            className="bg-slate-800 border-slate-700 text-slate-200" 
           
            value={step.config?.file_path || ""}
            onChange={(e) => onChange({ ...step.config, file_path: e.target.value })}
          />
        </div>
        
        {step.config?.operation === 'write' && (
          <div>
            <Label className="text-slate-300">Content</Label>
            <Textarea 
              className="bg-slate-800 border-slate-700 text-slate-200 min-h-[150px]" 
             
              value={step.config?.content || ""}
              onChange={(e) => onChange({ ...step.config, content: e.target.value })}
            />
          </div>
        )}
      </div>
    );
  },
  
  api: ({ step, onChange }: { step: PipelineStep, onChange: (config: any) => void }) => {
    return (
      <div className="space-y-4">
        <div>
          <Label className="text-slate-300">URL</Label>
          <Input 
            className="bg-slate-800 border-slate-700 text-slate-200" 
           
            value={step.config?.url || ""}
            onChange={(e) => onChange({ ...step.config, url: e.target.value })}
          />
        </div>
        
        <div>
          <Label className="text-slate-300">Method</Label>
          <Select 
            value={step.config?.method || "GET"} 
            onValueChange={(value) => onChange({ ...step.config, method: value })}
          >
            <SelectTrigger className="bg-slate-800 border-slate-700 text-slate-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="GET" className="text-slate-200">GET</SelectItem>
              <SelectItem value="POST" className="text-slate-200">POST</SelectItem>
              <SelectItem value="PUT" className="text-slate-200">PUT</SelectItem>
              <SelectItem value="DELETE" className="text-slate-200">DELETE</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label className="text-slate-300">Headers (JSON)</Label>
          <Textarea 
            className="bg-slate-800 border-slate-700 text-slate-200 font-mono" 
            placeholder='{"Content-Type": "application/json"}'
            value={step.config?.headers ? JSON.stringify(step.config.headers, null, 2) : ""}
            onChange={(e) => {
              try {
                // Try to parse as JSON
                const headers = e.target.value ? JSON.parse(e.target.value) : {};
                onChange({ ...step.config, headers });
              } catch (error) {
                // If not valid JSON, just store as string
                onChange({ ...step.config, headers: e.target.value });
              }
            }}
          />
        </div>
        
        <div>
          <Label className="text-slate-300">Request Body (JSON)</Label>
          <Textarea 
            className="bg-slate-800 border-slate-700 text-slate-200 font-mono min-h-[120px]" 
            placeholder='{"key": "value"}'
            value={step.config?.data ? JSON.stringify(step.config.data, null, 2) : ""}
            onChange={(e) => {
              try {
                // Try to parse as JSON
                const data = e.target.value ? JSON.parse(e.target.value) : {};
                onChange({ ...step.config, data });
              } catch (error) {
                // If not valid JSON, just store as string
                onChange({ ...step.config, data: e.target.value });
              }
            }}
          />
        </div>
      </div>
    );
  },
  
  condition: ({ step, onChange }: { step: PipelineStep, onChange: (config: any) => void }) => {
    return (
      <div className="space-y-4">
        <div>
          <Label className="text-slate-300">Condition Expression</Label>
          <Textarea 
            className="bg-slate-800 border-slate-700 text-slate-200 min-h-[120px]" 
           
            value={step.config?.condition || ""}
            onChange={(e) => onChange({ ...step.config, condition: e.target.value })}
          />
        </div>
      </div>
    );
  },
  
  transform: ({ step, onChange }: { step: PipelineStep, onChange: (config: any) => void }) => {
    return (
      <div className="space-y-4">
        <div>
          <Label className="text-slate-300">Transform Type</Label>
          <Select 
            value={step.config?.transform_type || "json_to_text"} 
            onValueChange={(value) => onChange({ ...step.config, transform_type: value })}
          >
            <SelectTrigger className="bg-slate-800 border-slate-700 text-slate-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="json_to_text" className="text-slate-200">JSON to Text</SelectItem>
              <SelectItem value="text_to_json" className="text-slate-200">Text to JSON</SelectItem>
              <SelectItem value="csv_to_json" className="text-slate-200">CSV to JSON</SelectItem>
              <SelectItem value="json_to_csv" className="text-slate-200">JSON to CSV</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label className="text-slate-300">Data Path</Label>
          <Input 
            className="bg-slate-800 border-slate-700 text-slate-200" 
           
            value={step.config?.data_path || ""}
            onChange={(e) => onChange({ ...step.config, data_path: e.target.value })}
          />
        </div>
      </div>
    );
  },
};

// Draggable Step component
const DraggableStep = ({ 
  step, 
  isDragging, 
  isSelected, 
  onClick, 
  onDragStart 
}: { 
  step: PipelineStep, 
  isDragging: boolean, 
  isSelected: boolean, 
  onClick: () => void, 
  onDragStart: (e: React.DragEvent) => void 
}) => {
  const stepType = STEP_TYPES.find(t => t.id === step.type) || STEP_TYPES[0];
  
  return (
    <div 
      draggable
      onDragStart={onDragStart}
      className={`relative p-3 rounded-md mb-2 border-2 cursor-pointer ${
        isDragging ? 'opacity-50' : 'opacity-100'
      } ${
        isSelected 
          ? 'border-cyan-500 bg-slate-800' 
          : 'border-slate-700 bg-slate-800 hover:border-slate-600'
      } transition-all duration-100`}
      onClick={onClick}
    >
      <div className="flex items-center">
        <div className="mr-2 cursor-grab">
          <MoreHorizontal className="h-4 w-4 text-slate-400" />
        </div>
        
        <div className={`p-1 rounded-md ${stepType.color} mr-2`}>
          {stepType.icon}
        </div>
        
        <div className="flex-1 overflow-hidden">
          <div className="text-sm font-medium text-slate-100 truncate">{step.name}</div>
          <div className="text-xs text-slate-400 truncate">{step.description || stepType.description}</div>
        </div>
        
        <div className="ml-2 flex items-center space-x-2">
          {!step.is_enabled && (
            <div className="text-xs bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded">
              Disabled
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Pipeline Builder Page
const PipelineBuilderPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = (window as any).navigate || ((path: string) => { window.location.href = path; });
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedStep, setSelectedStep] = useState<PipelineStep | null>(null);
  const [draggingStep, setDraggingStep] = useState<string | null>(null);
  const [models, setModels] = useState<Model[]>([]);
  const [addStepDialogOpen, setAddStepDialogOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isGitHubConnected, setIsGitHubConnected] = useState(false);
  
  // Input/Output mapping state
  const [newInputMapping, setNewInputMapping] = useState({
    key: '',
    sourceType: 'input',
    stepId: '',
    path: ''
  });
  const [newOutputMapping, setNewOutputMapping] = useState({
    key: '',
    path: ''
  });
  
  const stepsRef = useRef<HTMLDivElement>(null);
  
  // Fetch pipeline data
  useEffect(() => {
    const fetchPipeline = async () => {
      try {
        setLoading(true);
        if (!id) return;
        
        const data = await getPipeline(id);
        setPipeline(data);
        
        // Set the first step as selected by default if available
        if (data.steps && data.steps.length > 0) {
          setSelectedStep(data.steps[0]);
        }
        
        // Fetch models for prompt steps
        try {
          const modelsData = await getModels();
          if (modelsData.success && modelsData.data) {
            setModels(modelsData.data || []);
          }
        } catch (error) {
          console.error('Failed to fetch models:', error);
        }
        
        // Check GitHub connection status
        try {
          const response = await fetch('/api/github/status', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
          if (response.ok) {
            const data = await response.json();
            setIsGitHubConnected(data.connected);
          }
        } catch (error) {
          console.error('Failed to check GitHub status:', error);
        }
      } catch (error) {
        console.error('Failed to fetch pipeline:', error);
        toast({
          title: "Failed to load pipeline",
          description: "There was an error loading the pipeline. Please try again.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchPipeline();
  }, [id]);
  
  // Save pipeline data
  const savePipeline = async () => {
    if (!pipeline) return;
    
    try {
      setSaving(true);
      
      // Update pipeline
      const updatedPipeline = await updatePipeline(pipeline.id, {
        name: pipeline.name,
        description: pipeline.description,
        is_public: pipeline.is_public,
        tags: pipeline.tags
      });
      
      setPipeline(updatedPipeline);
      
      toast({
        title: "Pipeline saved",
        description: "Your pipeline has been saved successfully.",
      });
    } catch (error) {
      console.error('Failed to save pipeline:', error);
      toast({
        title: "Failed to save pipeline",
        description: "There was an error saving your pipeline. Please try again.",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };
  
  // Add a new step
  const addStep = async (type: string) => {
    if (!pipeline) return;
    
    try {
      // Create default config based on step type
      let defaultConfig: any = {};
      
      switch (type) {
        case 'prompt':
          defaultConfig = {
            model_id: models.length > 0 ? models[0].id : '',
            prompt: '',
            options: {
              temperature: 0.7,
              max_tokens: 1024,
              top_p: 0.95,
              stream: false
            }
          };
          break;
        case 'code':
          defaultConfig = {
            language: 'python',
            code: '',
            timeout: 30
          };
          break;
        case 'file':
          defaultConfig = {
            operation: 'read',
            file_path: ''
          };
          break;
        case 'api':
          defaultConfig = {
            url: '',
            method: 'GET',
            headers: {},
            data: {}
          };
          break;
        case 'condition':
          defaultConfig = {
            condition: ''
          };
          break;
        case 'transform':
          defaultConfig = {
            transform_type: 'json_to_text',
            data_path: ''
          };
          break;
      }
      
      // Calculate new step order (after the last step)
      const newOrder = pipeline.steps.length > 0 
        ? Math.max(...pipeline.steps.map(s => s.order)) + 1 
        : 0;
      
      // Create step
      const newStep = await createPipelineStep(pipeline.id, {
        name: `New ${STEP_TYPES.find(t => t.id === type)?.name || 'Step'}`,
        type,
        order: newOrder,
        config: defaultConfig,
        description: '',
        is_enabled: true
      });
      
      // Update local pipeline data
      setPipeline({
        ...pipeline,
        steps: [...pipeline.steps, newStep]
      });
      
      // Select the new step
      setSelectedStep(newStep);
      
      // Close dialog
      setAddStepDialogOpen(false);
      
      toast({
        title: "Step added",
        description: "The new step has been added to your pipeline.",
      });
    } catch (error) {
      console.error('Failed to add step:', error);
      toast({
        title: "Failed to add step",
        description: "There was an error adding the step. Please try again.",
        variant: "destructive"
      });
    }
  };
  
  // Update a step
  const updateStep = async (stepId: string, data: any) => {
    if (!pipeline) return;
    
    try {
      // Update step
      const updatedStep = await updatePipelineStep(pipeline.id, stepId, data);
      
      // Update local pipeline data
      setPipeline({
        ...pipeline,
        steps: pipeline.steps.map(s => s.id === stepId ? updatedStep : s)
      });
      
      // Update selected step if it's the one being edited
      if (selectedStep && selectedStep.id === stepId) {
        setSelectedStep(updatedStep);
      }
      
      toast({
        title: "Step updated",
        description: "The step has been updated successfully.",
      });
    } catch (error) {
      console.error('Failed to update step:', error);
      toast({
        title: "Failed to update step",
        description: "There was an error updating the step. Please try again.",
        variant: "destructive"
      });
    }
  };
  
  // Delete a step
  const deleteStep = async (stepId: string) => {
    if (!pipeline) return;
    
    try {
      // Delete step
      await deletePipelineStep(pipeline.id, stepId);
      
      // Update local pipeline data
      const updatedSteps = pipeline.steps.filter(s => s.id !== stepId);
      setPipeline({
        ...pipeline,
        steps: updatedSteps
      });
      
      // If the deleted step was selected, select the first remaining step or null
      if (selectedStep && selectedStep.id === stepId) {
        setSelectedStep(updatedSteps.length > 0 ? updatedSteps[0] : null);
      }
      
      toast({
        title: "Step deleted",
        description: "The step has been deleted from your pipeline.",
      });
    } catch (error) {
      console.error('Failed to delete step:', error);
      toast({
        title: "Failed to delete step",
        description: "There was an error deleting the step. Please try again.",
        variant: "destructive"
      });
    }
  };
  
  // Handle pipeline execution
  const handlePipelineExecute = async (options: PipelineExecutionOptions) => {
    if (!pipeline) return;
    
    try {
      const result = await executePipeline(pipeline.id, {
        input_parameters: options.initial_variables || {},
        dry_run: options.dry_run || false,
        debug_mode: options.debug_mode || false
      });
      
      // Close preview
      setIsPreviewOpen(false);
      
      if (options.dry_run) {
        toast({
          title: "Dry run complete",
          description: "Pipeline validation successful. Check the execution results.",
        });
      } else {
        toast({
          title: "Pipeline started",
          description: "Your pipeline is now executing.",
        });
        // Navigate to execution page
        navigate(`/pipelines/${pipeline.id}/executions/${result.id}`);
      }
    } catch (error) {
      console.error('Failed to execute pipeline:', error);
      toast({
        title: "Failed to execute pipeline",
        description: "There was an error starting the pipeline execution.",
        variant: "destructive"
      });
    }
  };

  // Convert pipeline format for preview
  const convertPipelineForPreview = (): PipelineDefinition => {
    if (!pipeline) return {} as PipelineDefinition;
    
    return {
      id: pipeline.id,
      name: pipeline.name,
      description: pipeline.description || '',
      steps: pipeline.steps.map(step => ({
        id: step.id,
        name: step.name,
        type: (() => {
          switch(step.type) {
            case 'prompt': return StepType.LLM;
            case 'code': return StepType.CODE;
            case 'api': return StepType.API;
            case 'transform': return StepType.TRANSFORM;
            case 'condition': return StepType.CONDITION;
            default: return StepType.LLM;
          }
        })(),
        config: step.config,
        inputs: [],
        outputs: [],
        depends_on: [],
        retry_count: step.retry_config?.max_retries || 0,
        timeout: step.timeout || 30,
        enabled: step.is_enabled
      })),
      connections: [],
      variables: {},
      settings: {},
      version: pipeline.version
    };
  };

  // Input/Output mapping functions
  const getAvailableSteps = () => {
    if (!selectedStep || !pipeline) return [];
    return pipeline.steps.filter(step => step.order < selectedStep.order);
  };
  
  const addInputMapping = async () => {
    if (!selectedStep || !newInputMapping.key || !newInputMapping.path) return;
    
    try {
      let mappingValue = '';
      
      if (newInputMapping.sourceType === 'input') {
        mappingValue = `{{input.${newInputMapping.path}}}`;
      } else if (newInputMapping.sourceType === 'step' && newInputMapping.stepId) {
        const step = pipeline?.steps.find(s => s.id === newInputMapping.stepId);
        const stepName = step ? (step.name || `step_${step.order}`) : newInputMapping.stepId;
        mappingValue = `{{${stepName}.${newInputMapping.path}}}`;
      } else if (newInputMapping.sourceType === 'static') {
        mappingValue = newInputMapping.path;
      }
      
      const updatedInputMapping = {
        ...selectedStep.input_mapping,
        [newInputMapping.key]: mappingValue
      };
      
      await updateStep(selectedStep.id, {
        input_mapping: updatedInputMapping
      });
      
      // Reset form
      setNewInputMapping({
        key: '',
        sourceType: 'input',
        stepId: '',
        path: ''
      });
      
      toast({
        title: "Input mapping added",
        description: `Added input mapping: ${newInputMapping.key}`,
      });
    } catch (error) {
      console.error('Failed to add input mapping:', error);
      toast({
        title: "Failed to add input mapping",
        description: "There was an error adding the input mapping.",
        variant: "destructive"
      });
    }
  };
  
  const removeInputMapping = async (key: string) => {
    if (!selectedStep) return;
    
    try {
      const updatedInputMapping = { ...selectedStep.input_mapping };
      delete updatedInputMapping[key];
      
      await updateStep(selectedStep.id, {
        input_mapping: updatedInputMapping
      });
      
      toast({
        title: "Input mapping removed",
        description: `Removed input mapping: ${key}`,
      });
    } catch (error) {
      console.error('Failed to remove input mapping:', error);
      toast({
        title: "Failed to remove input mapping",
        description: "There was an error removing the input mapping.",
        variant: "destructive"
      });
    }
  };
  
  const addOutputMapping = async () => {
    if (!selectedStep || !newOutputMapping.key || !newOutputMapping.path) return;
    
    try {
      const updatedOutputMapping = {
        ...selectedStep.output_mapping,
        [newOutputMapping.key]: newOutputMapping.path
      };
      
      await updateStep(selectedStep.id, {
        output_mapping: updatedOutputMapping
      });
      
      // Reset form
      setNewOutputMapping({
        key: '',
        path: ''
      });
      
      toast({
        title: "Output mapping added",
        description: `Added output mapping: ${newOutputMapping.key}`,
      });
    } catch (error) {
      console.error('Failed to add output mapping:', error);
      toast({
        title: "Failed to add output mapping",
        description: "There was an error adding the output mapping.",
        variant: "destructive"
      });
    }
  };
  
  const removeOutputMapping = async (key: string) => {
    if (!selectedStep) return;
    
    try {
      const updatedOutputMapping = { ...selectedStep.output_mapping };
      delete updatedOutputMapping[key];
      
      await updateStep(selectedStep.id, {
        output_mapping: updatedOutputMapping
      });
      
      toast({
        title: "Output mapping removed",
        description: `Removed output mapping: ${key}`,
      });
    } catch (error) {
      console.error('Failed to remove output mapping:', error);
      toast({
        title: "Failed to remove output mapping",
        description: "There was an error removing the output mapping.",
        variant: "destructive"
      });
    }
  };
  
  // Handle step drag and drop
  const handleDragStart = (stepId: string) => (e: React.DragEvent) => {
    setDraggingStep(stepId);
    e.dataTransfer.effectAllowed = 'move';
  };
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    // Find the closest step element
    if (stepsRef.current && draggingStep) {
      const stepsContainer = stepsRef.current;
      const stepElements = Array.from(stepsContainer.querySelectorAll('[data-step-id]'));
      const draggedElement = stepsContainer.querySelector(`[data-step-id="${draggingStep}"]`);
      
      if (!draggedElement) return;
      
      // Find the closest step to the cursor
      const closestElement = stepElements.reduce((closest, current) => {
        if (current === draggedElement) return closest;
        
        const box = current.getBoundingClientRect();
        const offset = e.clientY - (box.top + box.height / 2);
        
        if (!closest) return { element: current, offset: Math.abs(offset) };
        
        if (Math.abs(offset) < closest.offset) {
          return { element: current, offset: Math.abs(offset) };
        }
        
        return closest;
      }, null as { element: Element, offset: number } | null);
      
      // Remove all drop indicators
      stepElements.forEach(el => {
        el.classList.remove('drop-before', 'drop-after');
      });
      
      // Add drop indicator to the closest element
      if (closestElement) {
        const box = closestElement.element.getBoundingClientRect();
        
        if (e.clientY < box.top + box.height / 2) {
          closestElement.element.classList.add('drop-before');
        } else {
          closestElement.element.classList.add('drop-after');
        }
      }
    }
  };
  
  const handleDragEnd = () => {
    setDraggingStep(null);
    
    // Remove all drop indicators
    if (stepsRef.current) {
      const stepElements = Array.from(stepsRef.current.querySelectorAll('[data-step-id]'));
      stepElements.forEach(el => {
        el.classList.remove('drop-before', 'drop-after');
      });
    }
  };
  
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    
    if (!pipeline || !draggingStep) return;
    
    // Find the closest step element
    if (stepsRef.current) {
      const stepsContainer = stepsRef.current;
      const stepElements = Array.from(stepsContainer.querySelectorAll('[data-step-id]'));
      const draggedElement = stepsContainer.querySelector(`[data-step-id="${draggingStep}"]`);
      
      if (!draggedElement) return;
      
      // Find the closest step to the cursor
      const closestElement = stepElements.reduce((closest, current) => {
        if (current === draggedElement) return closest;
        
        const box = current.getBoundingClientRect();
        const offset = e.clientY - (box.top + box.height / 2);
        
        if (!closest) return { element: current, offset: Math.abs(offset), before: offset < 0 };
        
        if (Math.abs(offset) < closest.offset) {
          return { element: current, offset: Math.abs(offset), before: offset < 0 };
        }
        
        return closest;
      }, null as { element: Element, offset: number, before: boolean } | null);
      
      if (closestElement) {
        const targetStepId = closestElement.element.getAttribute('data-step-id');
        if (!targetStepId) return;
        
        // Find the steps in the pipeline
        const draggedStep = pipeline.steps.find(s => s.id === draggingStep);
        const targetStep = pipeline.steps.find(s => s.id === targetStepId);
        
        if (!draggedStep || !targetStep) return;
        
        // Reorder steps
        const reorderedSteps = [...pipeline.steps]
          .filter(s => s.id !== draggingStep) // Remove dragged step
          .sort((a, b) => a.order - b.order); // Sort by order
        
        // Find the index to insert at
        const targetIndex = reorderedSteps.findIndex(s => s.id === targetStepId);
        
        // Insert the dragged step
        const insertIndex = closestElement.before ? targetIndex : targetIndex + 1;
        reorderedSteps.splice(insertIndex, 0, draggedStep);
        
        // Update orders
        const stepsWithNewOrders = reorderedSteps.map((step, idx) => ({
          step_id: step.id,
          order: idx
        }));
        
        try {
          // Update step orders on the server
          await reorderPipelineSteps(pipeline.id, { steps: stepsWithNewOrders });
          
          // Update local pipeline data
          setPipeline({
            ...pipeline,
            steps: reorderedSteps.map((step, idx) => ({
              ...step,
              order: idx
            }))
          });
        } catch (error) {
          console.error('Failed to reorder steps:', error);
          toast({
            title: "Failed to reorder steps",
            description: "There was an error reordering the steps. Please try again.",
            variant: "destructive"
          });
        }
      }
    }
    
    handleDragEnd();
  };
  
  // Render the appropriate step config form based on step type
  const renderStepConfigForm = () => {
    if (!selectedStep) return null;
    
    const StepForm = StepConfigForms[selectedStep.type as keyof typeof StepConfigForms];
    
    if (!StepForm) {
      return (
        <div className="p-6 text-center text-slate-400">
          No configuration available for this step type.
        </div>
      );
    }
    
    return (
      <StepForm 
        step={selectedStep} 
        onChange={(config) => updateStep(selectedStep.id, { config })}
        models={models}
      />
    );
  };
  
  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-screen-2xl">
        <div className="flex items-center mb-8">
          <Button 
            variant="ghost" 
            size="sm" 
            className="mr-4 text-slate-400"
            onClick={() => navigate('/pipelines')}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <div className="flex-1">
            <Skeleton className="h-8 w-1/3 bg-slate-700 mb-1" />
            <Skeleton className="h-4 w-1/2 bg-slate-700" />
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <Skeleton className="h-10 w-full bg-slate-700 mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full bg-slate-700" />
              ))}
            </div>
          </div>
          
          <div className="lg:col-span-2">
            <Skeleton className="h-10 w-full bg-slate-700 mb-4" />
            <Skeleton className="h-64 w-full bg-slate-700" />
          </div>
        </div>
      </div>
    );
  }
  
  if (!pipeline) {
    return (
      <div className="container mx-auto py-8 px-4 text-center">
        <h1 className="text-2xl font-bold text-slate-200 mb-4">Pipeline Not Found</h1>
        <p className="text-slate-400 mb-6">The pipeline you're looking for doesn't exist or you don't have access to it.</p>
        <Button 
          onClick={() => navigate('/pipelines')}
          className="bg-cyan-600 hover:bg-cyan-700 text-white"
        >
          Back to Pipelines
        </Button>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto py-4 px-4 max-w-screen-2xl">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <Button 
            variant="ghost" 
            size="sm" 
            className="mr-4 text-slate-400 hover:text-slate-100 hover:bg-slate-800"
            onClick={() => navigate('/pipelines')}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-50">{pipeline.name}</h1>
            <p className="text-slate-400">{pipeline.description || 'No description'}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <PipelineGitHubSync
            pipelineId={pipeline.id}
            pipelineName={pipeline.name}
            isConnected={isGitHubConnected}
          />
          
          <div className="h-8 w-px bg-slate-700" />
          
          <Button 
            variant="secondary" 
            size="sm" 
            className="bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-200"
            onClick={savePipeline}
            disabled={saving}
          >
            <Save className="h-4 w-4 mr-1" />
            Save
          </Button>
          
          <Button 
            variant="secondary"
            size="sm" 
            className="bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-200"
            onClick={() => setIsPreviewOpen(true)}
          >
            <FlaskConical className="h-4 w-4 mr-1" />
            Preview
          </Button>
          
          <Button 
            size="sm" 
            className="bg-cyan-600 hover:bg-cyan-700 text-white"
            onClick={() => navigate(`/pipelines/${pipeline.id}/run`)}
          >
            <Play className="h-4 w-4 mr-1" />
            Run Pipeline
          </Button>
        </div>
      </div>
      
      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Steps */}
        <div className="lg:col-span-1">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-slate-100">Pipeline Steps</h2>
            <Button 
              variant="outline" 
              size="sm" 
              className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-slate-100"
              onClick={() => setAddStepDialogOpen(true)}
            >
              <Plus className="h-4 w-4 mr-1" />
              Add Step
            </Button>
          </div>
          
          <div 
            ref={stepsRef}
            className="space-y-1 min-h-[200px]"
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
            onDrop={handleDrop}
          >
            {pipeline.steps.length === 0 ? (
              <div className="text-center py-8 px-4 border-2 border-dashed border-slate-700 rounded-md">
                <p className="text-slate-400 mb-4">No steps in this pipeline yet</p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                  onClick={() => setAddStepDialogOpen(true)}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add First Step
                </Button>
              </div>
            ) : (
              pipeline.steps
                .sort((a, b) => a.order - b.order)
                .map(step => (
                  <div key={step.id} data-step-id={step.id} className="drop-indicator">
                    <DraggableStep
                      step={step}
                      isDragging={draggingStep === step.id}
                      isSelected={selectedStep?.id === step.id}
                      onClick={() => setSelectedStep(step)}
                      onDragStart={handleDragStart(step.id)}
                    />
                  </div>
                ))
            )}
          </div>
        </div>
        
        {/* Step Configuration */}
        <div className="lg:col-span-2 mb-8">
          {selectedStep ? (
            <>
              <div className="bg-slate-800 border border-slate-700 rounded-t-lg p-4">
                <div className="flex justify-between items-center mb-4">
                  <div className="flex-1">
                    <Input 
                      value={selectedStep.name}
                      onChange={(e) => updateStep(selectedStep.id, { name: e.target.value })}
                      className="bg-slate-900 border-slate-700 text-slate-100 text-lg font-medium mb-2"
                     
                    />
                    <Textarea 
                      value={selectedStep.description || ''}
                      onChange={(e) => updateStep(selectedStep.id, { description: e.target.value })}
                      className="bg-slate-900 border-slate-700 text-slate-400 resize-none h-16"
                     
                    />
                  </div>
                  
                  <div className="ml-4 flex flex-col space-y-2">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="text-slate-400 hover:text-slate-100"
                            onClick={() => updateStep(selectedStep.id, { is_enabled: !selectedStep.is_enabled })}
                          >
                            <Sliders className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="bg-slate-800 text-slate-200 border-slate-700">
                          {selectedStep.is_enabled ? 'Disable step' : 'Enable step'}
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="text-red-500 hover:text-red-400 hover:bg-slate-700"
                            onClick={() => {
                              if (confirm('Are you sure you want to delete this step?')) {
                                deleteStep(selectedStep.id);
                              }
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="bg-slate-800 text-slate-200 border-slate-700">
                          Delete step
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <div className="mr-2 text-slate-400 text-xs">Step Type:</div>
                      <Badge className={`${STEP_TYPES.find(t => t.id === selectedStep.type)?.color || 'bg-slate-600'}`}>
                        {STEP_TYPES.find(t => t.id === selectedStep.type)?.name || selectedStep.type}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="step-enabled"
                      checked={selectedStep.is_enabled}
                      onCheckedChange={(checked) => updateStep(selectedStep.id, { is_enabled: checked })}
                    />
                    <Label htmlFor="step-enabled" className={`text-sm ${selectedStep.is_enabled ? 'text-slate-300' : 'text-slate-500'}`}>
                      {selectedStep.is_enabled ? 'Enabled' : 'Disabled'}
                    </Label>
                  </div>
                </div>
              </div>
              
              <Tabs defaultValue="config" className="w-full">
                <TabsList className="bg-slate-800 border-x border-slate-700 w-full justify-start rounded-none h-10">
                  <TabsTrigger 
                    value="config" 
                    className="data-[state=active]:bg-slate-900 data-[state=active]:text-white rounded-none h-10 px-4"
                  >
                    Configuration
                  </TabsTrigger>
                  <TabsTrigger 
                    value="io-mapping" 
                    className="data-[state=active]:bg-slate-900 data-[state=active]:text-white rounded-none h-10 px-4"
                  >
                    Input/Output Mapping
                  </TabsTrigger>
                  <TabsTrigger 
                    value="advanced" 
                    className="data-[state=active]:bg-slate-900 data-[state=active]:text-white rounded-none h-10 px-4"
                  >
                    Advanced
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent 
                  value="config" 
                  className="border-x border-b border-slate-700 bg-slate-900 p-4 rounded-b-lg"
                >
                  {renderStepConfigForm()}
                </TabsContent>
                
                <TabsContent 
                  value="io-mapping" 
                  className="border-x border-b border-slate-700 bg-slate-900 p-4 rounded-b-lg"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-slate-200 font-medium mb-2">Input Mapping</h3>
                      <p className="text-slate-400 text-sm mb-4">
                        Map variables from previous steps to inputs for this step.
                      </p>
                      
                      {/* Existing Input Mappings */}
                      <div className="space-y-2 mb-4">
                        {selectedStep && Object.entries(selectedStep.input_mapping || {}).map(([key, value]) => (
                          <div key={key} className="bg-slate-800 border border-slate-700 rounded-lg p-3 flex items-center justify-between">
                            <div className="flex-1">
                              <div className="text-slate-200 font-medium">{key}</div>
                              <div className="text-slate-400 text-sm">{typeof value === 'string' ? value : JSON.stringify(value)}</div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeInputMapping(key)}
                              className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                      
                      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                        <div className="space-y-4">
                          <div>
                            <Label className="text-slate-300 mb-1">Input Variable</Label>
                            <Input 
                              value={newInputMapping.key}
                              onChange={(e) => setNewInputMapping({ ...newInputMapping, key: e.target.value })}
                              className="bg-slate-900 border-slate-700 text-slate-200" 
                              placeholder="e.g., prompt, data, condition"
                            />
                          </div>
                          
                          <div>
                            <Label className="text-slate-300 mb-1">Source</Label>
                            <Select 
                              value={newInputMapping.sourceType} 
                              onValueChange={(value) => setNewInputMapping({ ...newInputMapping, sourceType: value })}
                            >
                              <SelectTrigger className="bg-slate-900 border-slate-700 text-slate-200">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent className="bg-slate-800 border-slate-700">
                                <SelectItem value="input" className="text-slate-200">Pipeline Input</SelectItem>
                                <SelectItem value="step" className="text-slate-200">Previous Step Output</SelectItem>
                                <SelectItem value="static" className="text-slate-200">Static Value</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          
                          {newInputMapping.sourceType === 'step' && (
                            <div>
                              <Label className="text-slate-300 mb-1">Step</Label>
                              <Select 
                                value={newInputMapping.stepId} 
                                onValueChange={(value) => setNewInputMapping({ ...newInputMapping, stepId: value })}
                              >
                                <SelectTrigger className="bg-slate-900 border-slate-700 text-slate-200">
                                  <SelectValue placeholder="Select step" />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-800 border-slate-700">
                                  {getAvailableSteps().map((step) => (
                                    <SelectItem key={step.id} value={step.id} className="text-slate-200">
                                      {step.name || `Step ${step.order + 1}`}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          )}
                          
                          <div>
                            <Label className="text-slate-300 mb-1">
                              {newInputMapping.sourceType === 'static' ? 'Value' : 'Path'}
                            </Label>
                            <Input 
                              value={newInputMapping.path}
                              onChange={(e) => setNewInputMapping({ ...newInputMapping, path: e.target.value })}
                              className="bg-slate-900 border-slate-700 text-slate-200" 
                              placeholder={
                                newInputMapping.sourceType === 'static' 
                                  ? 'Enter static value' 
                                  : newInputMapping.sourceType === 'input'
                                  ? 'e.g., user_input, query'
                                  : 'e.g., result, response.content'
                              }
                            />
                          </div>
                          
                          <Button
                            onClick={addInputMapping}
                            disabled={!newInputMapping.key || !newInputMapping.path}
                            className="bg-slate-700 hover:bg-slate-600 text-slate-200 w-full"
                          >
                            <Plus className="h-4 w-4 mr-1" />
                            Add Mapping
                          </Button>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-slate-200 font-medium mb-2">Output Mapping</h3>
                      <p className="text-slate-400 text-sm mb-4">
                        Define how outputs from this step will be named for use by later steps.
                      </p>
                      
                      {/* Existing Output Mappings */}
                      <div className="space-y-2 mb-4">
                        {selectedStep && Object.entries(selectedStep.output_mapping || {}).map(([key, value]) => (
                          <div key={key} className="bg-slate-800 border border-slate-700 rounded-lg p-3 flex items-center justify-between">
                            <div className="flex-1">
                              <div className="text-slate-200 font-medium">{key}</div>
                              <div className="text-slate-400 text-sm">{typeof value === 'string' ? value : JSON.stringify(value)}</div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeOutputMapping(key)}
                              className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                      
                      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                        <div className="space-y-4">
                          <div>
                            <Label className="text-slate-300 mb-1">Output Variable</Label>
                            <Input 
                              value={newOutputMapping.key}
                              onChange={(e) => setNewOutputMapping({ ...newOutputMapping, key: e.target.value })}
                              className="bg-slate-900 border-slate-700 text-slate-200" 
                              placeholder="e.g., result, response, analysis"
                            />
                          </div>
                          
                          <div>
                            <Label className="text-slate-300 mb-1">Step Output Path</Label>
                            <Input 
                              value={newOutputMapping.path}
                              onChange={(e) => setNewOutputMapping({ ...newOutputMapping, path: e.target.value })}
                              className="bg-slate-900 border-slate-700 text-slate-200" 
                              placeholder="e.g., result, response.content, data.summary"
                             
                            />
                          </div>
                          
                          <Button
                            onClick={addOutputMapping}
                            disabled={!newOutputMapping.key || !newOutputMapping.path}
                            className="bg-slate-700 hover:bg-slate-600 text-slate-200 w-full"
                          >
                            <Plus className="h-4 w-4 mr-1" />
                            Add Mapping
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent 
                  value="advanced" 
                  className="border-x border-b border-slate-700 bg-slate-900 p-4 rounded-b-lg"
                >
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-slate-200 font-medium mb-2">Retry Configuration</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-slate-300 mb-1">Max Retries</Label>
                          <Input 
                            type="number" 
                            min="0"
                            className="bg-slate-800 border-slate-700 text-slate-200" 
                           
                            value={selectedStep.retry_config?.max_retries || 0}
                            onChange={(e) => updateStep(selectedStep.id, { 
                              retry_config: { 
                                ...(selectedStep.retry_config || {}), 
                                max_retries: parseInt(e.target.value) 
                              } 
                            })}
                          />
                        </div>
                        
                        <div>
                          <Label className="text-slate-300 mb-1">Retry Delay (ms)</Label>
                          <Input 
                            type="number" 
                            min="0"
                            className="bg-slate-800 border-slate-700 text-slate-200" 
                           
                            value={selectedStep.retry_config?.delay || 1000}
                            onChange={(e) => updateStep(selectedStep.id, { 
                              retry_config: { 
                                ...(selectedStep.retry_config || {}), 
                                delay: parseInt(e.target.value) 
                              } 
                            })}
                          />
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-slate-200 font-medium mb-2">Timeout</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label className="text-slate-300 mb-1">Timeout (seconds)</Label>
                          <Input 
                            type="number" 
                            min="0"
                            className="bg-slate-800 border-slate-700 text-slate-200" 
                           
                            value={selectedStep.timeout || ""}
                            onChange={(e) => updateStep(selectedStep.id, { 
                              timeout: e.target.value ? parseInt(e.target.value) : null 
                            })}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </>
          ) : (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
              <h3 className="text-slate-300 text-lg mb-2">No Step Selected</h3>
              <p className="text-slate-400 mb-6">Select a step from the left to configure it or add a new step to your pipeline.</p>
              <Button 
                variant="outline" 
                className="border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white"
                onClick={() => setAddStepDialogOpen(true)}
              >
                <Plus className="h-4 w-4 mr-1" />
                Add New Step
              </Button>
            </div>
          )}
        </div>
      </div>
      
      {/* Add Step Dialog */}
      <Dialog open={addStepDialogOpen} onOpenChange={setAddStepDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>Add Pipeline Step</DialogTitle>
            <DialogDescription className="text-slate-400">
              Choose a step type to add to your pipeline.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 py-4">
            {STEP_TYPES.map(stepType => (
              <Card 
                key={stepType.id}
                className="bg-slate-800 border-slate-700 hover:border-cyan-600 cursor-pointer transition-all"
                onClick={() => addStep(stepType.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start">
                    <div className={`p-2 rounded-md ${stepType.color} mr-3`}>
                      {stepType.icon}
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-100">{stepType.name}</h3>
                      <p className="text-sm text-slate-400">{stepType.description}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          
          <DialogFooter>
            <Button
              variant="outline"
              className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
              onClick={() => setAddStepDialogOpen(false)}
            >
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Pipeline Preview */}
      {pipeline && (
        <PipelinePreview
          pipeline={convertPipelineForPreview()}
          isOpen={isPreviewOpen}
          onClose={() => setIsPreviewOpen(false)}
          onExecute={handlePipelineExecute}
        />
      )}

      {/* Add CSS for drag and drop indicators */}
      <style dangerouslySetInnerHTML={{__html: `
        .drop-indicator {
          position: relative;
        }
        
        .drop-indicator.drop-before::before {
          content: "";
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 2px;
          background-color: #0EA5E9;
          z-index: 10;
        }
        
        .drop-indicator.drop-after::after {
          content: "";
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          height: 2px;
          background-color: #0EA5E9;
          z-index: 10;
        }
      `}} />
    </div>
  );
};

export default PipelineBuilderPage;