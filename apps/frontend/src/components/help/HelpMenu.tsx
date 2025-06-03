import React, { useState } from 'react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { HelpCircle, Book, Zap, MessageSquare, Workflow, Settings, AlertCircle } from 'lucide-react';
import { HelpContent } from './HelpContent';

export function HelpMenu() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" title="Help">
          <HelpCircle className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>Web+ Help</SheetTitle>
          <SheetDescription>
            Learn how to use Web+ features effectively
          </SheetDescription>
        </SheetHeader>
        <ScrollArea className="h-[calc(100vh-120px)] mt-6">
          <Tabs defaultValue="quick-start" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="quick-start">Start</TabsTrigger>
              <TabsTrigger value="features">Features</TabsTrigger>
              <TabsTrigger value="tasks">Tasks</TabsTrigger>
              <TabsTrigger value="troubleshoot">Help</TabsTrigger>
            </TabsList>
            
            <TabsContent value="quick-start" className="mt-4">
              <div className="space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Quick Start Guide
                </h3>
                <ol className="list-decimal list-inside space-y-2 text-sm">
                  <li>Login with your credentials at <code>/login</code></li>
                  <li>Navigate to Models page to view available AI models</li>
                  <li>Start a chat by clicking "Chat" in the navigation</li>
                  <li>Select a model and type your message</li>
                  <li>View the response in real-time as it streams</li>
                </ol>
              </div>
            </TabsContent>
            
            <TabsContent value="features" className="mt-4">
              <Accordion type="single" collapsible className="w-full">
                <HelpContent />
              </Accordion>
            </TabsContent>
            
            <TabsContent value="tasks" className="mt-4">
              <div className="space-y-4">
                <h3 className="font-semibold">Common Tasks</h3>
                
                <div className="space-y-3">
                  <div className="border rounded-lg p-3">
                    <h4 className="font-medium mb-1">Start a Conversation</h4>
                    <ol className="list-decimal list-inside text-sm space-y-1 text-muted-foreground">
                      <li>Navigate to Chat page</li>
                      <li>Select an AI model from the dropdown</li>
                      <li>Type your message in the input field</li>
                      <li>Press Enter or click Send</li>
                      <li>View streaming response in real-time</li>
                    </ol>
                  </div>
                  
                  <div className="border rounded-lg p-3">
                    <h4 className="font-medium mb-1">Upload and Analyze Files</h4>
                    <ol className="list-decimal list-inside text-sm space-y-1 text-muted-foreground">
                      <li>Click the attachment icon in chat</li>
                      <li>Select files (max 10MB each)</li>
                      <li>Supported: .txt, .md, .pdf, .doc, .py, .js, etc.</li>
                      <li>Files are analyzed automatically</li>
                      <li>Reference files in your chat messages</li>
                    </ol>
                  </div>
                  
                  <div className="border rounded-lg p-3">
                    <h4 className="font-medium mb-1">Build a Pipeline</h4>
                    <ol className="list-decimal list-inside text-sm space-y-1 text-muted-foreground">
                      <li>Go to Pipelines → Builder</li>
                      <li>Drag steps from the sidebar</li>
                      <li>Connect steps by dragging between nodes</li>
                      <li>Configure each step's parameters</li>
                      <li>Save and execute your pipeline</li>
                    </ol>
                  </div>
                  
                  <div className="border rounded-lg p-3">
                    <h4 className="font-medium mb-1">Export Conversations</h4>
                    <ol className="list-decimal list-inside text-sm space-y-1 text-muted-foreground">
                      <li>Open a conversation</li>
                      <li>Click the Export button</li>
                      <li>Choose format: Markdown, JSON, or Text</li>
                      <li>Select messages to include</li>
                      <li>Download the exported file</li>
                    </ol>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="troubleshoot" className="mt-4">
              <div className="space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Troubleshooting
                </h3>
                
                <Accordion type="single" collapsible className="w-full">
                  <AccordionItem value="item-1">
                    <AccordionTrigger>Model not responding</AccordionTrigger>
                    <AccordionContent>
                      <ul className="text-sm space-y-1">
                        <li>• Check if the model is running (green status)</li>
                        <li>• For Ollama models, ensure Ollama service is active</li>
                        <li>• Try refreshing the models list</li>
                        <li>• Check network connectivity</li>
                      </ul>
                    </AccordionContent>
                  </AccordionItem>
                  
                  <AccordionItem value="item-2">
                    <AccordionTrigger>File upload fails</AccordionTrigger>
                    <AccordionContent>
                      <ul className="text-sm space-y-1">
                        <li>• Maximum file size is 10MB</li>
                        <li>• Check supported file types in settings</li>
                        <li>• Ensure you have upload permissions</li>
                        <li>• Try a smaller file or different format</li>
                      </ul>
                    </AccordionContent>
                  </AccordionItem>
                  
                  <AccordionItem value="item-3">
                    <AccordionTrigger>Pipeline execution errors</AccordionTrigger>
                    <AccordionContent>
                      <ul className="text-sm space-y-1">
                        <li>• Validate pipeline connections</li>
                        <li>• Check step configurations</li>
                        <li>• Ensure all required inputs are provided</li>
                        <li>• Review execution logs for details</li>
                      </ul>
                    </AccordionContent>
                  </AccordionItem>
                  
                  <AccordionItem value="item-4">
                    <AccordionTrigger>Authentication issues</AccordionTrigger>
                    <AccordionContent>
                      <ul className="text-sm space-y-1">
                        <li>• JWT tokens expire after 30 minutes</li>
                        <li>• Use refresh token to get new access token</li>
                        <li>• Check if your account is active</li>
                        <li>• Contact admin if locked out</li>
                      </ul>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
                
                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2">Common Error Messages</h4>
                  <dl className="text-sm space-y-2">
                    <dt className="font-mono text-red-600">"Model not found"</dt>
                    <dd className="text-muted-foreground ml-4">The selected model is not available. Refresh the models list.</dd>
                    
                    <dt className="font-mono text-red-600">"Invalid API Key"</dt>
                    <dd className="text-muted-foreground ml-4">Your API key is incorrect or expired. Generate a new one in settings.</dd>
                    
                    <dt className="font-mono text-red-600">"Rate limit exceeded"</dt>
                    <dd className="text-muted-foreground ml-4">Too many requests. Default limit is 10/minute. Wait before retrying.</dd>
                    
                    <dt className="font-mono text-red-600">"Insufficient permissions"</dt>
                    <dd className="text-muted-foreground ml-4">Your role doesn't have access to this feature. Contact your admin.</dd>
                  </dl>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}