"""
GitHub Integration for Pipeline Version Control

This module provides functionality to sync pipelines with GitHub repositories,
enabling version control, collaboration, and backup of pipeline definitions.
"""

import json
import base64
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GitHubConfig(BaseModel):
    """Configuration for GitHub integration."""
    token: str = Field(..., description="GitHub personal access token")
    owner: str = Field(..., description="Repository owner (username or organization)")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(default="main", description="Default branch")
    pipelines_path: str = Field(default="pipelines", description="Path in repo for pipelines")


class GitHubFile(BaseModel):
    """Represents a file in GitHub."""
    path: str
    content: str
    sha: Optional[str] = None
    message: str
    branch: Optional[str] = None


class GitHubCommit(BaseModel):
    """Represents a GitHub commit."""
    sha: str
    message: str
    author: Dict[str, Any]
    date: str
    files: List[str]


class GitHubIntegration:
    """Handles GitHub integration for pipeline version control."""
    
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {config.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    async def test_connection(self) -> bool:
        """Test GitHub connection and authentication."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/user",
                    headers=self.headers
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False
    
    async def get_repository(self) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{self.config.owner}/{self.config.repo}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.error(f"Failed to get repository: {e}")
            return None
    
    async def create_or_update_file(
        self, 
        path: str, 
        content: str, 
        message: str,
        branch: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create or update a file in the repository."""
        try:
            # Get current file info if it exists
            current_file = await self.get_file(path, branch)
            sha = current_file.get("sha") if current_file else None
            
            # Encode content to base64
            encoded_content = base64.b64encode(content.encode()).decode()
            
            # Prepare request data
            data = {
                "message": message,
                "content": encoded_content,
                "branch": branch or self.config.branch
            }
            
            if sha:
                data["sha"] = sha
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/repos/{self.config.owner}/{self.config.repo}/contents/{path}",
                    headers=self.headers,
                    json=data
                )
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    logger.error(f"Failed to create/update file: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to create/update file: {e}")
            return None
    
    async def get_file(
        self, 
        path: str, 
        branch: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a file from the repository."""
        try:
            params = {}
            if branch:
                params["ref"] = branch
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{self.config.owner}/{self.config.repo}/contents/{path}",
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            return None
    
    async def get_file_content(
        self, 
        path: str, 
        branch: Optional[str] = None
    ) -> Optional[str]:
        """Get decoded content of a file."""
        file_info = await self.get_file(path, branch)
        if file_info and "content" in file_info:
            try:
                # Decode base64 content
                content = base64.b64decode(file_info["content"]).decode()
                return content
            except Exception as e:
                logger.error(f"Failed to decode file content: {e}")
        return None
    
    async def list_files(
        self, 
        path: str = "", 
        branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List files in a directory."""
        try:
            params = {}
            if branch:
                params["ref"] = branch
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{self.config.owner}/{self.config.repo}/contents/{path}",
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                return []
                
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    async def get_commits(
        self, 
        path: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 30
    ) -> List[GitHubCommit]:
        """Get commit history for a path."""
        try:
            params = {
                "per_page": limit
            }
            
            if path:
                params["path"] = path
            if since:
                params["since"] = since.isoformat()
            if until:
                params["until"] = until.isoformat()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{self.config.owner}/{self.config.repo}/commits",
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code == 200:
                    commits = []
                    for commit_data in response.json():
                        commits.append(GitHubCommit(
                            sha=commit_data["sha"],
                            message=commit_data["commit"]["message"],
                            author={
                                "name": commit_data["commit"]["author"]["name"],
                                "email": commit_data["commit"]["author"]["email"]
                            },
                            date=commit_data["commit"]["author"]["date"],
                            files=[f["filename"] for f in commit_data.get("files", [])]
                        ))
                    return commits
                return []
                
        except Exception as e:
            logger.error(f"Failed to get commits: {e}")
            return []
    
    async def create_branch(
        self, 
        branch_name: str, 
        from_branch: Optional[str] = None
    ) -> bool:
        """Create a new branch."""
        try:
            # Get the SHA of the branch to branch from
            from_branch = from_branch or self.config.branch
            
            async with httpx.AsyncClient() as client:
                # Get reference of source branch
                ref_response = await client.get(
                    f"{self.base_url}/repos/{self.config.owner}/{self.config.repo}/git/ref/heads/{from_branch}",
                    headers=self.headers
                )
                
                if ref_response.status_code != 200:
                    return False
                
                sha = ref_response.json()["object"]["sha"]
                
                # Create new branch
                create_response = await client.post(
                    f"{self.base_url}/repos/{self.config.owner}/{self.config.repo}/git/refs",
                    headers=self.headers,
                    json={
                        "ref": f"refs/heads/{branch_name}",
                        "sha": sha
                    }
                )
                
                return create_response.status_code == 201
                
        except Exception as e:
            logger.error(f"Failed to create branch: {e}")
            return False
    
    async def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a pull request."""
        try:
            base_branch = base_branch or self.config.branch
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/repos/{self.config.owner}/{self.config.repo}/pulls",
                    headers=self.headers,
                    json={
                        "title": title,
                        "body": body,
                        "head": head_branch,
                        "base": base_branch
                    }
                )
                
                if response.status_code == 201:
                    return response.json()
                else:
                    logger.error(f"Failed to create pull request: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            return None
    
    # Pipeline-specific methods
    
    async def save_pipeline(
        self, 
        pipeline_id: str, 
        pipeline_data: Dict[str, Any],
        message: Optional[str] = None
    ) -> bool:
        """Save a pipeline to GitHub."""
        try:
            # Prepare pipeline file path
            filename = f"{pipeline_id}.json"
            filepath = f"{self.config.pipelines_path}/{filename}"
            
            # Prepare commit message
            if not message:
                message = f"Update pipeline: {pipeline_data.get('name', pipeline_id)}"
            
            # Convert pipeline data to JSON
            content = json.dumps(pipeline_data, indent=2)
            
            # Save to GitHub
            result = await self.create_or_update_file(
                path=filepath,
                content=content,
                message=message
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to save pipeline to GitHub: {e}")
            return False
    
    async def load_pipeline(
        self, 
        pipeline_id: str,
        branch: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Load a pipeline from GitHub."""
        try:
            filename = f"{pipeline_id}.json"
            filepath = f"{self.config.pipelines_path}/{filename}"
            
            content = await self.get_file_content(filepath, branch)
            if content:
                return json.loads(content)
            return None
            
        except Exception as e:
            logger.error(f"Failed to load pipeline from GitHub: {e}")
            return None
    
    async def list_pipelines(
        self, 
        branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all pipelines in the repository."""
        try:
            files = await self.list_files(self.config.pipelines_path, branch)
            pipelines = []
            
            for file in files:
                if file["name"].endswith(".json"):
                    pipeline_id = file["name"][:-5]  # Remove .json extension
                    pipelines.append({
                        "id": pipeline_id,
                        "name": file["name"],
                        "path": file["path"],
                        "sha": file["sha"],
                        "size": file["size"]
                    })
            
            return pipelines
            
        except Exception as e:
            logger.error(f"Failed to list pipelines from GitHub: {e}")
            return []
    
    async def get_pipeline_history(
        self, 
        pipeline_id: str,
        limit: int = 10
    ) -> List[GitHubCommit]:
        """Get commit history for a specific pipeline."""
        filename = f"{pipeline_id}.json"
        filepath = f"{self.config.pipelines_path}/{filename}"
        
        return await self.get_commits(path=filepath, limit=limit)