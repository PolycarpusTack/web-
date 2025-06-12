import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from '@/components/ui/use-toast';
import { 
  Github, 
  GitCommit, 
  GitPullRequest,
  Upload,
  Download,
  History,
  Loader2,
  CheckCircle,
  Info
} from 'lucide-react';

interface PipelineGitHubSyncProps {
  pipelineId: string;
  pipelineName: string;
  isConnected: boolean;
}

export function PipelineGitHubSync({ 
  pipelineId, 
  pipelineName, 
  isConnected 
}: PipelineGitHubSyncProps) {
  const [isSyncDialogOpen, setIsSyncDialogOpen] = useState(false);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [isHistoryDialogOpen, setIsHistoryDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Sync form state
  const [commitMessage, setCommitMessage] = useState('');
  const [createPR, setCreatePR] = useState(false);
  const [prTitle, setPrTitle] = useState('');
  const [prBody, setPrBody] = useState('');
  
  // Import form state
  const [importBranch, setImportBranch] = useState('');
  const [overwrite, setOverwrite] = useState(false);
  
  // History state
  const [history, setHistory] = useState<any[]>([]);

  const handleSync = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/github/sync/pipeline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          pipeline_id: pipelineId,
          commit_message: commitMessage || `Update pipeline: ${pipelineName}`,
          create_pr: createPR,
          pr_title: prTitle,
          pr_body: prBody
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.pull_request) {
          toast({
            title: "Pull request created",
            description: `PR #${data.pull_request.number} created successfully`,
          });
        } else {
          toast({
            title: "Pipeline synced",
            description: "Pipeline has been synced to GitHub successfully"
          });
        }
        setIsSyncDialogOpen(false);
        resetSyncForm();
      } else {
        const error = await response.json();
        toast({
          title: "Sync failed",
          description: error.detail || "Failed to sync pipeline to GitHub",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Sync failed",
        description: "An error occurred while syncing to GitHub",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleImport = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/github/import/pipeline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          pipeline_id: pipelineId,
          branch: importBranch || undefined,
          overwrite
        })
      });

      if (response.ok) {
        toast({
          title: "Pipeline imported",
          description: "Pipeline has been imported from GitHub successfully"
        });
        setIsImportDialogOpen(false);
        resetImportForm();
        // Reload the page to show updated pipeline
        window.location.reload();
      } else {
        const error = await response.json();
        toast({
          title: "Import failed",
          description: error.detail || "Failed to import pipeline from GitHub",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Import failed",
        description: "An error occurred while importing from GitHub",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadHistory = async () => {
    setIsHistoryDialogOpen(true);
    setIsLoading(true);
    try {
      const response = await fetch(`/api/github/pipelines/${pipelineId}/history`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setHistory(data.history);
      }
    } catch (error) {
      toast({
        title: "Failed to load history",
        description: "Could not load commit history from GitHub",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const resetSyncForm = () => {
    setCommitMessage('');
    setCreatePR(false);
    setPrTitle('');
    setPrBody('');
  };

  const resetImportForm = () => {
    setImportBranch('');
    setOverwrite(false);
  };

  if (!isConnected) {
    return (
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Connect your GitHub repository in settings to enable version control
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsSyncDialogOpen(true)}
      >
        <Upload className="h-4 w-4 mr-2" />
        Sync to GitHub
      </Button>
      
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsImportDialogOpen(true)}
      >
        <Download className="h-4 w-4 mr-2" />
        Import
      </Button>
      
      <Button
        variant="outline"
        size="sm"
        onClick={loadHistory}
      >
        <History className="h-4 w-4 mr-2" />
        History
      </Button>

      {/* Sync Dialog */}
      <Dialog open={isSyncDialogOpen} onOpenChange={setIsSyncDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sync Pipeline to GitHub</DialogTitle>
            <DialogDescription>
              Save this pipeline to your GitHub repository
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="commit-message">Commit Message</Label>
              <Textarea
                id="commit-message"
                placeholder={`Update pipeline: ${pipelineName}`}
                value={commitMessage}
                onChange={(e) => setCommitMessage(e.target.value)}
                rows={3}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="create-pr"
                checked={createPR}
                onCheckedChange={setCreatePR}
              />
              <Label htmlFor="create-pr">Create Pull Request</Label>
            </div>

            {createPR && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="pr-title">Pull Request Title</Label>
                  <Input
                    id="pr-title"
                    placeholder={`Update pipeline: ${pipelineName}`}
                    value={prTitle}
                    onChange={(e) => setPrTitle(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pr-body">Pull Request Description</Label>
                  <Textarea
                    id="pr-body"
                    placeholder="Describe the changes made to this pipeline..."
                    value={prBody}
                    onChange={(e) => setPrBody(e.target.value)}
                    rows={4}
                  />
                </div>
              </>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsSyncDialogOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button onClick={handleSync} disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Syncing...
                </>
              ) : (
                <>
                  <GitCommit className="h-4 w-4 mr-2" />
                  {createPR ? 'Create PR' : 'Commit'}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={isImportDialogOpen} onOpenChange={setIsImportDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Import Pipeline from GitHub</DialogTitle>
            <DialogDescription>
              Import this pipeline from your GitHub repository
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="import-branch">Branch (optional)</Label>
              <Input
                id="import-branch"
                placeholder="Leave empty for default branch"
                value={importBranch}
                onChange={(e) => setImportBranch(e.target.value)}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="overwrite"
                checked={overwrite}
                onCheckedChange={setOverwrite}
              />
              <Label htmlFor="overwrite">Overwrite local changes</Label>
            </div>

            {overwrite && (
              <Alert>
                <AlertDescription>
                  Warning: This will replace all local changes with the version from GitHub
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsImportDialogOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleImport} 
              disabled={isLoading}
              variant={overwrite ? "destructive" : "default"}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Import
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* History Dialog */}
      <Dialog open={isHistoryDialogOpen} onOpenChange={setIsHistoryDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Pipeline History</DialogTitle>
            <DialogDescription>
              Commit history for this pipeline
            </DialogDescription>
          </DialogHeader>
          
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : history.length > 0 ? (
              <div className="space-y-3">
                {history.map((commit) => (
                  <div key={commit.sha} className="border rounded-lg p-3">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <p className="font-medium">{commit.message}</p>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>{commit.author.name}</span>
                          <span>{new Date(commit.date).toLocaleString()}</span>
                        </div>
                      </div>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {commit.sha.substring(0, 7)}
                      </code>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center py-8 text-muted-foreground">
                No commit history found
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsHistoryDialogOpen(false)}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}