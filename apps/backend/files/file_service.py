import os
import uuid
import shutil
import tempfile
import aiofiles
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from db import crud

# Define settings as a simple object since we don't have a config.py file
class Settings:
    api_base_url = "http://localhost:8000"
    
settings = Settings()

# File storage directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# File size limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Allowed file types
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
ALLOWED_DOCUMENT_TYPES = ["application/pdf", "text/plain", "text/markdown", "application/msword", 
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
ALL_ALLOWED_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_DOCUMENT_TYPES

# File validation functions
def is_valid_file_type(content_type: str) -> bool:
    """Check if the file content type is allowed."""
    return content_type in ALL_ALLOWED_TYPES

def is_valid_file_size(file_size: int) -> bool:
    """Check if the file size is within limits."""
    return file_size <= MAX_FILE_SIZE

def get_file_extension(filename: str, content_type: str) -> str:
    """Get the file extension based on content type or filename."""
    # Try to get from filename first
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    
    # Map content types to extensions
    content_type_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "application/pdf": "pdf",
        "text/plain": "txt",
        "text/markdown": "md",
        "application/msword": "doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx"
    }
    
    return content_type_map.get(content_type, "bin")

def generate_secure_filename(original_filename: str, content_type: str) -> str:
    """Generate a secure, unique filename with the correct extension."""
    ext = get_file_extension(original_filename, content_type)
    return f"{uuid.uuid4().hex}.{ext}"

# File storage service
async def save_uploaded_file(file: UploadFile, user_id: str) -> Dict[str, Any]:
    """Save an uploaded file to disk and return file metadata."""
    # Validate file
    content_type = file.content_type or "application/octet-stream"
    if not is_valid_file_type(content_type):
        raise ValueError(f"File type {content_type} not allowed")
    
    # Check file size - first try with file.size if available
    file_size = getattr(file, "size", None)
    if file_size is None:
        # If size not available, read a chunk to estimate
        pos = file.file.tell()
        chunk = await file.read(1024 * 1024)  # Read 1MB to check
        file_size = len(chunk)
        await file.seek(0)  # Reset position
    
    if not is_valid_file_size(file_size):
        raise ValueError(f"File size exceeds maximum allowed ({MAX_FILE_SIZE // (1024 * 1024)}MB)")
    
    # Generate secure filename
    original_filename = file.filename or "unnamed_file"
    secure_filename = generate_secure_filename(original_filename, content_type)
    
    # Create user directory if it doesn't exist
    user_dir = os.path.join(UPLOAD_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    # Save file to disk
    file_path = os.path.join(user_dir, secure_filename)
    
    async with aiofiles.open(file_path, "wb") as out_file:
        # Read and write file in chunks
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            await out_file.write(chunk)
    
    # Get final file size
    final_size = os.path.getsize(file_path)
    
    return {
        "original_filename": original_filename,
        "filename": secure_filename,
        "content_type": content_type,
        "size": final_size,
        "path": file_path
    }

async def upload_file(
    db: AsyncSession,
    file: UploadFile,
    user_id: str,
    conversation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    is_public: bool = False
) -> Dict[str, Any]:
    """Upload a file and create database record."""
    # Save file to disk
    file_data = await save_uploaded_file(file, user_id)
    
    # Create file record in database
    db_file = await crud.create_file(
        db=db,
        filename=file_data["filename"],
        original_filename=file_data["original_filename"],
        content_type=file_data["content_type"],
        size=file_data["size"],
        path=file_data["path"],
        user_id=user_id,
        conversation_id=conversation_id,
        metadata=metadata,
        is_public=is_public
    )
    
    return {
        "id": db_file.id,
        "filename": db_file.filename,
        "original_filename": db_file.original_filename,
        "content_type": db_file.content_type,
        "size": db_file.size,
        "user_id": db_file.user_id,
        "conversation_id": db_file.conversation_id,
        "created_at": db_file.created_at.isoformat(),
        "is_public": db_file.is_public
    }

async def upload_multiple_files(
    db: AsyncSession,
    files: List[UploadFile],
    user_id: str,
    conversation_id: Optional[str] = None,
    message_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    is_public: bool = False
) -> List[Dict[str, Any]]:
    """Upload multiple files and create database records."""
    results = []
    
    for file in files:
        # Upload each file
        file_result = await upload_file(
            db=db,
            file=file,
            user_id=user_id,
            conversation_id=conversation_id,
            metadata=metadata,
            is_public=is_public
        )
        
        # Associate with message if provided
        if message_id:
            await crud.associate_file_with_message(
                db=db,
                file_id=file_result["id"],
                message_id=message_id
            )
        
        results.append(file_result)
    
    return results

async def get_file_contents(file_id: str, db: AsyncSession) -> Optional[bytes]:
    """Get the contents of a file by ID."""
    # Get file record from database
    file = await crud.get_file(db=db, file_id=file_id)
    if not file:
        return None
    
    # Check if file exists on disk
    if not os.path.exists(file.path):
        return None
    
    # Read file contents
    async with aiofiles.open(file.path, "rb") as f:
        return await f.read()

async def delete_file_and_record(file_id: str, db: AsyncSession) -> bool:
    """Delete a file from disk and database."""
    return await crud.delete_file(db=db, file_id=file_id, delete_from_storage=True)

def get_file_url(file_id: str, is_public: bool = False) -> str:
    """Generate a URL for accessing the file."""
    base_url = settings.api_base_url
    prefix = "public" if is_public else "files"
    return f"{base_url}/{prefix}/{file_id}"