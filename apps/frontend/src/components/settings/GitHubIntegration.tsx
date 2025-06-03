import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from '@/components/ui/use-toast';
import { 
  Github, 
  Link, 
  Unlink, 
  Settings, 
  Check, 
  AlertCircle,
  Loader2,
  GitBranch,
  FolderGit2
} from 'lucide-react';

interface GitHubConfig {
  token: string;
  owner: string;
  repo: string;
  branch: string;
  pipelines_path: string;
}

interface GitHubStatus {
  connected: boolean;
  repository?: {
    name: string;
    full_name: string;
    description: string;
    url: string;
  };
  config?: {
    owner: string;
    repo: string;
    branch: string;
    pipelines_path: string;
  };
}

export function GitHubIntegration() {
  const [status, setStatus] = useState<GitHubStatus>({ connected: false });
  const [config, setConfig] = useState<GitHubConfig>({
    token: '',
    owner: '',
    repo: '',
    branch: 'main',
    pipelines_path: 'pipelines'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingStatus, setIsCheckingStatus] = useState(true);
  const [showSetup, setShowSetup] = useState(false);

  useEffect(() => {
    checkGitHubStatus();
  }, []);

  const checkGitHubStatus = async () => {
    setIsCheckingStatus(true);
    try {
      const response = await fetch('/api/github/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
        if (data.config) {
          setConfig(prev => ({
            ...prev,
            owner: data.config.owner,
            repo: data.config.repo,
            branch: data.config.branch,
            pipelines_path: data.config.pipelines_path
          }));
        }
      }
    } catch (error) {
      console.error('Failed to check GitHub status:', error);
    } finally {
      setIsCheckingStatus(false);
    }
  };

  const handleSetup = async () => {
    if (!config.token || !config.owner || !config.repo) {
      toast({
        title: "Missing information",
        description: "Please fill in all required fields",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/github/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        const data = await response.json();
        toast({
          title: "GitHub connected",
          description: `Successfully connected to ${data.repository.full_name}`
        });
        setShowSetup(false);
        await checkGitHubStatus();
      } else {
        const error = await response.json();
        toast({
          title: "Connection failed",
          description: error.detail || "Failed to connect to GitHub",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Connection failed",
        description: "An error occurred while connecting to GitHub",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect GitHub integration?')) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/github/disconnect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        toast({
          title: "GitHub disconnected",
          description: "GitHub integration has been removed"
        });
        setStatus({ connected: false });
        setConfig({
          token: '',
          owner: '',
          repo: '',
          branch: 'main',
          pipelines_path: 'pipelines'
        });
      }
    } catch (error) {
      toast({
        title: "Disconnection failed",
        description: "Failed to disconnect GitHub integration",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isCheckingStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Github className="h-5 w-5" />
            GitHub Integration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Github className="h-5 w-5" />
          GitHub Integration
        </CardTitle>
        <CardDescription>
          Connect your GitHub repository to sync and version control your pipelines
        </CardDescription>
      </CardHeader>
      <CardContent>
        {status.connected ? (
          <div className="space-y-4">
            <Alert>
              <Check className="h-4 w-4" />
              <AlertDescription>
                Connected to GitHub repository
              </AlertDescription>
            </Alert>

            {status.repository && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{status.repository.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      {status.repository.description || 'No description'}
                    </p>
                  </div>
                  <a
                    href={status.repository.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    <Link className="h-4 w-4" />
                  </a>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <FolderGit2 className="h-3 w-3" />
                      <span>Repository</span>
                    </div>
                    <p className="font-mono">{status.config?.owner}/{status.config?.repo}</p>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <GitBranch className="h-3 w-3" />
                      <span>Branch</span>
                    </div>
                    <p className="font-mono">{status.config?.branch}</p>
                  </div>
                </div>

                <Separator />

                <div className="flex justify-between items-center">
                  <Badge variant="outline">
                    Pipelines path: {status.config?.pipelines_path}
                  </Badge>
                  
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleDisconnect}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Unlink className="h-4 w-4 mr-2" />
                    )}
                    Disconnect
                  </Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                GitHub integration is not configured. Connect your repository to enable version control for pipelines.
              </AlertDescription>
            </Alert>

            {!showSetup ? (
              <Button onClick={() => setShowSetup(true)} className="w-full">
                <Github className="h-4 w-4 mr-2" />
                Connect GitHub Repository
              </Button>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="token">Personal Access Token</Label>
                  <Input
                    id="token"
                    type="password"
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                    value={config.token}
                    onChange={(e) => setConfig({ ...config, token: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground">
                    Create a token with repo scope at{' '}
                    <a
                      href="https://github.com/settings/tokens/new"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      GitHub Settings
                    </a>
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="owner">Repository Owner</Label>
                    <Input
                      id="owner"
                      placeholder="username or org"
                      value={config.owner}
                      onChange={(e) => setConfig({ ...config, owner: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="repo">Repository Name</Label>
                    <Input
                      id="repo"
                      placeholder="my-pipelines"
                      value={config.repo}
                      onChange={(e) => setConfig({ ...config, repo: e.target.value })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="branch">Default Branch</Label>
                    <Input
                      id="branch"
                      placeholder="main"
                      value={config.branch}
                      onChange={(e) => setConfig({ ...config, branch: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="path">Pipelines Path</Label>
                    <Input
                      id="path"
                      placeholder="pipelines"
                      value={config.pipelines_path}
                      onChange={(e) => setConfig({ ...config, pipelines_path: e.target.value })}
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowSetup(false)}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSetup}
                    disabled={isLoading}
                    className="flex-1"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Connecting...
                      </>
                    ) : (
                      <>
                        <Link className="h-4 w-4 mr-2" />
                        Connect Repository
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}