import React, { useState, useEffect } from 'react';
import { File as FileType, filesApi } from '@/api/files';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Cpu, FileText, RefreshCw } from "lucide-react";
import { Badge } from '@/components/ui/badge';
import { formatFileSize } from '@/api/files';
import MarkdownRenderer from './MarkdownRenderer';

interface FileAnalysisDisplayProps {
  file: FileType;
  onRefreshAnalysis?: (fileId: string) => void;
  className?: string;
}

export const FileAnalysisDisplay: React.FC<FileAnalysisDisplayProps> = ({
  file,
  onRefreshAnalysis,
  className
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<FileType | null>(null);

  useEffect(() => {
    if (file.analyzed) {
      setAnalysisData(file);
    } else {
      loadAnalysis();
    }
  }, [file]);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const { data, error } = await filesApi.getFileAnalysis(file.id);
      
      if (error) {
        setError(typeof error === 'string' ? error : 'Failed to load file analysis');
      } else if (data) {
        setAnalysisData(data);
      }
    } catch (err) {
      setError('An unexpected error occurred');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const { data, error } = await filesApi.analyzeFile(file.id);
      
      if (error) {
        setError(typeof error === 'string' ? error : 'Failed to analyze file');
      } else if (data) {
        setAnalysisData(data);
        if (onRefreshAnalysis) {
          onRefreshAnalysis(file.id);
        }
      }
    } catch (err) {
      setError('An unexpected error occurred');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Render different content based on analysis state
  const renderContent = () => {
    if (loading) {
      return (
        <div className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-destructive p-4 bg-destructive/10 rounded-md">
          <p className="font-medium">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      );
    }

    if (!analysisData?.analyzed) {
      return (
        <div className="flex flex-col items-center justify-center py-8">
          <Cpu className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-center mb-4">
            This file hasn't been analyzed yet. Analyze it to extract text and insights.
          </p>
          <Button onClick={handleRequestAnalysis} className="gap-2">
            <Cpu className="h-4 w-4" />
            Analyze File
          </Button>
        </div>
      );
    }

    // Show tabs with extracted content and analysis
    return (
      <Tabs defaultValue="extracted" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="extracted">Extracted Text</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>
        
        <TabsContent value="extracted" className="min-h-[200px] max-h-[400px] overflow-y-auto">
          {analysisData.extracted_text ? (
            <div className="p-4 text-sm whitespace-pre-wrap">
              {analysisData.extracted_text}
            </div>
          ) : (
            <div className="p-4 text-center text-muted-foreground">
              No text content could be extracted from this file.
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="analysis" className="min-h-[200px] max-h-[400px] overflow-y-auto">
          {analysisData.analysis_result ? (
            <div className="p-4">
              {typeof analysisData.analysis_result === 'string' ? (
                <MarkdownRenderer content={analysisData.analysis_result as string} />
              ) : (
                <div className="space-y-4">
                  {Object.entries(analysisData.analysis_result).map(([key, value]) => (
                    <div key={key} className="border-b pb-2">
                      <h4 className="font-medium capitalize">{key.replace(/_/g, ' ')}</h4>
                      <div className="text-sm mt-1">
                        {typeof value === 'string' ? (
                          <p>{value}</p>
                        ) : (
                          <pre className="text-xs bg-muted p-2 rounded-md overflow-x-auto">
                            {JSON.stringify(value, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 text-center text-muted-foreground">
              No analysis results available for this file.
            </div>
          )}
        </TabsContent>
      </Tabs>
    );
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-base">{file.original_filename}</CardTitle>
            <CardDescription>
              {formatFileSize(file.size)} • {file.content_type}
            </CardDescription>
          </div>
          {analysisData?.analyzed && (
            <Badge variant="outline" className="flex items-center gap-1">
              <Cpu className="h-3 w-3" />
              <span>Analyzed</span>
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        {renderContent()}
      </CardContent>
      
      {analysisData?.analyzed && (
        <CardFooter className="pt-0 flex justify-end">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleRequestAnalysis}
            disabled={loading}
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Refresh Analysis
          </Button>
        </CardFooter>
      )}
    </Card>
  );
};

export default FileAnalysisDisplay;