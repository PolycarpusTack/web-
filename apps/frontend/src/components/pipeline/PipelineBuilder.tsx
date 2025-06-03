import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  NodeTypes,
  EdgeTypes,
  Connection,
  ConnectionMode,
  OnConnect,
  OnNodeDrag,
  OnSelectionChange,
  MarkerType,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';

import { 
  PipelineDefinition, 
  PipelineStep, 
  StepType, 
  PipelineConnection,
  ValidationResult 
} from '@/types/pipeline';

import { 
  Bot, 
  Code, 
  Settings, 
  Database, 
  GitBranch, 
  Merge, 
  Play, 
  Save, 
  Download, 
  Upload,
  Plus,
  Trash2,
  Copy,
  Undo,
  Redo,
  ZoomIn,
  ZoomOut,
  Maximize,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

// Custom Node Components
const LLMNode = ({ data, selected }: { data: any; selected: boolean }) => (
  <div className={`px-4 py-3 shadow-lg rounded-lg bg-white border-2 min-w-[200px] ${
    selected ? 'border-blue-500' : 'border-gray-200'
  }`}>
    <div className="flex items-center gap-2 mb-2">
      <Bot className="h-4 w-4 text-blue-600" />
      <div className="font-medium text-sm">{data.label}</div>
    </div>
    <div className="text-xs text-gray-500 mb-2">{data.model || 'No model selected'}</div>
    {data.status && (
      <Badge 
        variant={data.status === 'completed' ? 'default' : data.status === 'running' ? 'secondary' : 'outline'}
        className="text-xs"
      >
        {data.status}
      </Badge>
    )}
    {/* Input/Output Handles */}
    <div className="absolute -left-2 top-1/2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white" 
         style={{ transform: 'translateY(-50%)' }} />
    <div className="absolute -right-2 top-1/2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white" 
         style={{ transform: 'translateY(-50%)' }} />
  </div>
);

const CodeNode = ({ data, selected }: { data: any; selected: boolean }) => (
  <div className={`px-4 py-3 shadow-lg rounded-lg bg-white border-2 min-w-[200px] ${
    selected ? 'border-green-500' : 'border-gray-200'
  }`}>
    <div className="flex items-center gap-2 mb-2">
      <Code className="h-4 w-4 text-green-600" />
      <div className="font-medium text-sm">{data.label}</div>
    </div>
    <div className="text-xs text-gray-500 mb-2">{data.language || 'python'}</div>
    {data.status && (
      <Badge 
        variant={data.status === 'completed' ? 'default' : data.status === 'running' ? 'secondary' : 'outline'}
        className="text-xs"
      >
        {data.status}
      </Badge>
    )}
    <div className="absolute -left-2 top-1/2 w-4 h-4 bg-green-500 rounded-full border-2 border-white" 
         style={{ transform: 'translateY(-50%)' }} />
    <div className="absolute -right-2 top-1/2 w-4 h-4 bg-green-500 rounded-full border-2 border-white" 
         style={{ transform: 'translateY(-50%)' }} />
  </div>
);

const TransformNode = ({ data, selected }: { data: any; selected: boolean }) => (
  <div className={`px-4 py-3 shadow-lg rounded-lg bg-white border-2 min-w-[200px] ${
    selected ? 'border-purple-500' : 'border-gray-200'
  }`}>
    <div className="flex items-center gap-2 mb-2">
      <Settings className="h-4 w-4 text-purple-600" />
      <div className="font-medium text-sm">{data.label}</div>
    </div>
    <div className="text-xs text-gray-500 mb-2">{data.transform_type || 'extract'}</div>
    {data.status && (
      <Badge 
        variant={data.status === 'completed' ? 'default' : data.status === 'running' ? 'secondary' : 'outline'}
        className="text-xs"
      >
        {data.status}
      </Badge>
    )}
    <div className="absolute -left-2 top-1/2 w-4 h-4 bg-purple-500 rounded-full border-2 border-white" 
         style={{ transform: 'translateY(-50%)' }} />
    <div className="absolute -right-2 top-1/2 w-4 h-4 bg-purple-500 rounded-full border-2 border-white" 
         style={{ transform: 'translateY(-50%)' }} />
  </div>
);

const APINode = ({ data, selected }: { data: any; selected: boolean }) => (
  <div className={`px-4 py-3 shadow-lg rounded-lg bg-white border-2 min-w-[200px] ${
    selected ? 'border-orange-500' : 'border-gray-200'
  }`}>
    <div className="flex items-center gap-2 mb-2">
      <Database className="h-4 w-4 text-orange-600" />
      <div className="font-medium text-sm">{data.label}</div>
    </div>
    <div className="text-xs text-gray-500 mb-2">{data.method || 'GET'} {data.url || 'No URL'}</div>
    {data.status && (
      <Badge 
        variant={data.status === 'completed' ? 'default' : data.status === 'running' ? 'secondary' : 'outline'}
        className="text-xs"
      >
        {data.status}
      </Badge>
    )}
    <div className="absolute -left-2 top-1/2 w-4 h-4 bg-orange-500 rounded-full border-2 border-white" 
         style={{ transform: 'translateY(-50%)' }} />
    <div className="absolute -right-2 top-1/2 w-4 h-4 bg-orange-500 rounded-full border-2 border-white" 
         style={{ transform: 'translateY(-50%)' }} />
  </div>
);

const ConditionNode = ({ data, selected }: { data: any; selected: boolean }) => (
  <div className={`px-4 py-3 shadow-lg rounded-lg bg-white border-2 min-w-[200px] ${
    selected ? 'border-yellow-500' : 'border-gray-200'
  }`}>
    <div className="flex items-center gap-2 mb-2">
      <GitBranch className="h-4 w-4 text-yellow-600" />
      <div className="font-medium text-sm">{data.label}</div>
    </div>
    <div className="text-xs text-gray-500 mb-2">If/Else Logic</div>
    {data.status && (
      <Badge 
        variant={data.status === 'completed' ? 'default' : data.status === 'running' ? 'secondary' : 'outline'}
        className="text-xs"
      >
        {data.status}
      </Badge>
    )}
    <div className="absolute -left-2 top-1/2 w-4 h-4 bg-yellow-500 rounded-full border-2 border-white" 
         style={{ transform: 'translateY(-50%)' }} />
    <div className="absolute -right-2 top-1/3 w-4 h-4 bg-green-500 rounded-full border-2 border-white" />
    <div className="absolute -right-2 bottom-1/3 w-4 h-4 bg-red-500 rounded-full border-2 border-white" />
  </div>
);

// Step Palette Items
const stepTypes = [
  {
    type: StepType.LLM,
    name: 'LLM Chat',
    description: 'Language model processing',
    icon: Bot,
    color: 'blue'
  },
  {
    type: StepType.CODE,
    name: 'Code Execution',
    description: 'Python/JavaScript code',
    icon: Code,
    color: 'green'
  },
  {
    type: StepType.TRANSFORM,
    name: 'Data Transform',
    description: 'Data manipulation',
    icon: Settings,
    color: 'purple'
  },
  {
    type: StepType.API,
    name: 'API Call',
    description: 'HTTP requests',
    icon: Database,
    color: 'orange'
  },
  {
    type: StepType.CONDITION,
    name: 'Conditional',
    description: 'Branching logic',
    icon: GitBranch,
    color: 'yellow'
  }
];

const nodeTypes: NodeTypes = {
  llm: LLMNode,
  code: CodeNode,
  transform: TransformNode,
  api: APINode,
  condition: ConditionNode,
};

interface PipelineBuilderProps {
  pipeline?: PipelineDefinition;
  onChange?: (pipeline: PipelineDefinition) => void;
  onExecute?: (pipeline: PipelineDefinition) => void;
  onSave?: (pipeline: PipelineDefinition) => void;
  isExecuting?: boolean;
  validationResult?: ValidationResult;
}

export const PipelineBuilder: React.FC<PipelineBuilderProps> = ({
  pipeline,
  onChange,
  onExecute,
  onSave,
  isExecuting = false,
  validationResult
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [selectedEdges, setSelectedEdges] = useState<string[]>([]);
  const [stepCounter, setStepCounter] = useState(1);
  const reactFlowInstance = useRef<any>(null);

  // Load pipeline data
  useEffect(() => {
    if (pipeline) {
      const flowNodes = pipeline.steps.map(step => ({
        id: step.id,
        type: step.type,
        position: step.position || { x: 100 * nodes.length, y: 100 },
        data: {
          label: step.name,
          ...step.config,
          status: step.enabled ? 'ready' : 'disabled'
        }
      }));

      const flowEdges = pipeline.connections.map(conn => ({
        id: conn.id,
        source: conn.source_step_id,
        target: conn.target_step_id,
        type: 'smoothstep',
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
        label: conn.label,
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    }
  }, [pipeline]);

  // Convert flow data to pipeline definition
  const toPipelineDefinition = useCallback((): PipelineDefinition => {
    const steps: PipelineStep[] = nodes.map(node => ({
      id: node.id,
      name: node.data.label,
      type: node.type as StepType,
      config: {
        ...node.data,
        label: undefined,
        status: undefined
      },
      inputs: [],
      outputs: [],
      depends_on: edges.filter(e => e.target === node.id).map(e => e.source),
      retry_count: 0,
      timeout: 300,
      enabled: node.data.status !== 'disabled',
      position: node.position
    }));

    const connections: PipelineConnection[] = edges.map(edge => ({
      id: edge.id,
      source_step_id: edge.source,
      target_step_id: edge.target,
      source_output: 'output',
      target_input: 'input',
      label: edge.label as string
    }));

    return {
      id: pipeline?.id || `pipeline_${Date.now()}`,
      name: pipeline?.name || 'Untitled Pipeline',
      description: pipeline?.description,
      steps,
      connections,
      variables: pipeline?.variables || {},
      settings: pipeline?.settings || {},
      version: '1.0'
    };
  }, [nodes, edges, pipeline]);

  // Handle changes
  useEffect(() => {
    const newPipeline = toPipelineDefinition();
    onChange?.(newPipeline);
  }, [nodes, edges, toPipelineDefinition, onChange]);

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      const edge = {
        ...connection,
        id: `edge_${Date.now()}`,
        type: 'smoothstep',
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
      };
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges]
  );

  const addNode = useCallback((stepType: StepType) => {
    const id = `${stepType}_${stepCounter}`;
    const stepInfo = stepTypes.find(s => s.type === stepType);
    
    const newNode = {
      id,
      type: stepType,
      position: { x: 250 + (stepCounter * 50), y: 100 + (stepCounter * 50) },
      data: {
        label: `${stepInfo?.name} ${stepCounter}`,
        status: 'ready'
      },
    };

    setNodes((nds) => [...nds, newNode]);
    setStepCounter(prev => prev + 1);
  }, [stepCounter, setNodes]);

  const deleteSelected = useCallback(() => {
    setNodes((nds) => nds.filter(node => !selectedNodes.includes(node.id)));
    setEdges((eds) => eds.filter(edge => 
      !selectedEdges.includes(edge.id) && 
      !selectedNodes.includes(edge.source) && 
      !selectedNodes.includes(edge.target)
    ));
    setSelectedNodes([]);
    setSelectedEdges([]);
  }, [selectedNodes, selectedEdges, setNodes, setEdges]);

  const onSelectionChange: OnSelectionChange = useCallback(({ nodes, edges }) => {
    setSelectedNodes(nodes.map(node => node.id));
    setSelectedEdges(edges.map(edge => edge.id));
  }, []);

  const fitView = useCallback(() => {
    reactFlowInstance.current?.fitView();
  }, []);

  const zoomIn = useCallback(() => {
    reactFlowInstance.current?.zoomIn();
  }, []);

  const zoomOut = useCallback(() => {
    reactFlowInstance.current?.zoomOut();
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = (event.target as Element).getBoundingClientRect();
      const stepType = event.dataTransfer.getData('application/reactflow');

      if (typeof stepType === 'undefined' || !stepType) {
        return;
      }

      const position = reactFlowInstance.current?.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const id = `${stepType}_${stepCounter}`;
      const stepInfo = stepTypes.find(s => s.type === stepType);
      
      const newNode = {
        id,
        type: stepType,
        position,
        data: {
          label: `${stepInfo?.name} ${stepCounter}`,
          status: 'ready'
        },
      };

      setNodes((nds) => [...nds, newNode]);
      setStepCounter(prev => prev + 1);
    },
    [stepCounter, setNodes]
  );

  const onDragStart = (event: React.DragEvent, stepType: StepType) => {
    event.dataTransfer.setData('application/reactflow', stepType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="flex h-full">
      {/* Step Palette */}
      <div className="w-80 border-r border-gray-200 bg-gray-50">
        <div className="p-4">
          <h3 className="font-semibold mb-4">Pipeline Steps</h3>
          
          <ScrollArea className="h-[calc(100vh-12rem)]">
            <div className="space-y-2">
              {stepTypes.map((stepType) => {
                const Icon = stepType.icon;
                return (
                  <Card 
                    key={stepType.type}
                    className="cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
                    draggable
                    onDragStart={(event) => onDragStart(event, stepType.type)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-center gap-3">
                        <Icon className={`h-8 w-8 text-${stepType.color}-600`} />
                        <div>
                          <div className="font-medium text-sm">{stepType.name}</div>
                          <div className="text-xs text-gray-500">{stepType.description}</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </ScrollArea>

          <Separator className="my-4" />

          {/* Quick Actions */}
          <div className="space-y-2">
            <Button 
              onClick={() => onExecute?.(toPipelineDefinition())} 
              disabled={isExecuting || nodes.length === 0}
              className="w-full"
              size="sm"
            >
              <Play className="h-4 w-4 mr-2" />
              {isExecuting ? 'Executing...' : 'Execute Pipeline'}
            </Button>
            
            <Button 
              variant="outline" 
              onClick={() => onSave?.(toPipelineDefinition())}
              disabled={nodes.length === 0}
              className="w-full"
              size="sm"
            >
              <Save className="h-4 w-4 mr-2" />
              Save Pipeline
            </Button>
          </div>

          {/* Validation Status */}
          {validationResult && (
            <div className="mt-4">
              <Alert className={validationResult.valid ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
                {validationResult.valid ? 
                  <CheckCircle className="h-4 w-4 text-green-600" /> : 
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                }
                <AlertDescription>
                  {validationResult.valid ? 
                    'Pipeline is valid' : 
                    `${validationResult.errors.length} validation errors`
                  }
                </AlertDescription>
              </Alert>
            </div>
          )}
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 relative">
        {/* Toolbar */}
        <div className="absolute top-4 left-4 z-10 flex gap-2">
          <Button variant="outline" size="sm" onClick={deleteSelected} disabled={selectedNodes.length === 0 && selectedEdges.length === 0}>
            <Trash2 className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={zoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={zoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={fitView}>
            <Maximize className="h-4 w-4" />
          </Button>
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onSelectionChange={onSelectionChange}
          onInit={(instance) => { reactFlowInstance.current = instance; }}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          connectionMode={ConnectionMode.Loose}
          fitView
          snapToGrid
          snapGrid={[20, 20]}
          defaultEdgeOptions={{
            type: 'smoothstep',
            markerEnd: { type: MarkerType.ArrowClosed },
          }}
        >
          <Controls />
          <MiniMap 
            nodeStrokeColor={(n) => {
              switch (n.type) {
                case 'llm': return '#3b82f6';
                case 'code': return '#10b981';
                case 'transform': return '#8b5cf6';
                case 'api': return '#f59e0b';
                case 'condition': return '#eab308';
                default: return '#6b7280';
              }
            }}
            nodeColor={(n) => {
              switch (n.type) {
                case 'llm': return '#dbeafe';
                case 'code': return '#d1fae5';
                case 'transform': return '#ede9fe';
                case 'api': return '#fef3c7';
                case 'condition': return '#fefce8';
                default: return '#f3f4f6';
              }
            }}
            nodeBorderRadius={8}
          />
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        </ReactFlow>
      </div>
    </div>
  );
};

export default PipelineBuilder;