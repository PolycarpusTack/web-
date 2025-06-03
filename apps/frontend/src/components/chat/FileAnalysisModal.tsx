import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Message } from '@/api/conversations';
import { File as FileType, filesApi } from '@/api/files';
import FileAnalysisDisplay from './FileAnalysisDisplay';
import { Button } from '@/components/ui/button';
import { ChevronRight, FileSearch } from "lucide-react";
import { Loader2 } from 'lucide-react';

interface FileAnalysisModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  messageId?: string;
  files?: FileType[];
}

export const FileAnalysisModal: React.FC<FileAnalysisModalProps> = ({
  open,
  onOpenChange,
  messageId,
  files: initialFiles = [],
}) => {
  const [files, setFiles] = useState<FileType[]>(initialFiles);
  const [loading, setLoading] = useState(initialFiles.length === 0 && !!messageId);
  const [error, setError] = useState<string | null>(null);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);

  // Load files if messageId is provided and no initial files
  useEffect(() => {
    if (open && messageId && initialFiles.length === 0) {
      loadMessageFiles();
    } else if (initialFiles.length > 0) {
      setActiveFileId(initialFiles[0].id);
    }
  }, [open, messageId, initialFiles]);

  const loadMessageFiles = async () => {
    if (!messageId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await filesApi.getMessageFiles(messageId);
      
      if (response.success && response.data?.files && response.data.files.length > 0) {
        setFiles(response.data.files);
        setActiveFileId(response.data.files[0].id);
      } else {
        setError('No files found for this message');
      }
    } catch (err) {
      console.error('Error loading message files:', err);
      setError('Failed to load message files');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshAnalysis = async (fileId: string) => {
    const updatedFiles = [...files];
    const fileIndex = updatedFiles.findIndex(f => f.id === fileId);
    
    if (fileIndex >= 0) {
      try {
        const { data, error } = await filesApi.getFileAnalysis(fileId);
        
        if (error) {
          console.error('Error refreshing file analysis:', error);
        } else if (data) {
          updatedFiles[fileIndex] = data;
          setFiles(updatedFiles);
        }
      } catch (err) {
        console.error('Unexpected error refreshing analysis:', err);
      }
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
          <p className="text-muted-foreground mt-4">Loading files...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-6 text-center">
          <div className="bg-destructive/10 p-4 rounded-md text-destructive mb-4">
            <p>{error}</p>
          </div>
          <Button onClick={loadMessageFiles} variant="outline">
            Retry
          </Button>
        </div>
      );
    }

    if (files.length === 0) {
      return (
        <div className="p-6 text-center">
          <p className="text-muted-foreground">No files to analyze.</p>
        </div>
      );
    }

    // Show file analysis tabs if we have files
    return (
      <>
        <Tabs 
          value={activeFileId || files[0].id} 
          onValueChange={setActiveFileId} 
          className="w-full"
        >
          <TabsList className="w-full max-w-screen-lg mx-auto mb-4 overflow-x-auto flex-wrap">
            {files.map(file => (
              <TabsTrigger key={file.id} value={file.id} className="flex items-center gap-2">
                <span className="truncate max-w-[150px]">{file.original_filename || file.filename}</span>
                {file.analyzed && (
                  <FileSearch className="h-3 w-3 text-green-500" />
                )}
              </TabsTrigger>
            ))}
          </TabsList>
          
          {files.map(file => (
            <TabsContent key={file.id} value={file.id}>
              <FileAnalysisDisplay 
                file={file} 
                onRefreshAnalysis={handleRefreshAnalysis}
              />
            </TabsContent>
          ))}
        </Tabs>
      </>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[900px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>File Analysis</DialogTitle>
          <DialogDescription>
            View and analyze files to extract text and insights
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          {renderContent()}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default FileAnalysisModal;