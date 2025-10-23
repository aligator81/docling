from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

# Authentication schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    role: str  # user, admin, super_admin
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Document schemas
class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    mime_type: str

class DocumentCreate(DocumentBase):
    user_id: int
    file_path: str

class Document(DocumentBase):
    id: int
    user_id: int
    file_path: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    document: Document
    message: str

# Chat schemas
class ChatMessage(BaseModel):
    message: str
    document_ids: Optional[List[int]] = None
    context_docs: Optional[List[int]] = None

class ReferenceDetail(BaseModel):
    document_id: int
    filename: str
    page_numbers: Optional[str] = None
    section_title: Optional[str] = None
    similarity: float

class ChatResponse(BaseModel):
    response: str
    context_docs: List[int]
    model_used: str
    references: Optional[List[ReferenceDetail]] = None

# Admin schemas
class UserManagement(BaseModel):
    user_id: int
    action: str  # activate, deactivate, promote, demote

class PasswordReset(BaseModel):
    new_password: str

class APIConfigBase(BaseModel):
    provider: str  # openai, mistral
    api_key: str
    is_active: bool = True

class APIConfigCreate(APIConfigBase):
    pass

class APIConfig(APIConfigBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# System schemas
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database_connected: bool

class SystemStats(BaseModel):
    total_users: int
    total_documents: int
    total_chunks: int
    total_embeddings: int
    active_sessions: int

# Processing schemas
class ProcessingStatus(BaseModel):
    document_id: int
    status: str
    content_length: int
    chunks_count: int
    embeddings_count: int
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProcessingResult(BaseModel):
    success: bool
    message: str
    processing_time: float
    metadata: Optional[Dict] = None

class DocumentProcessingRequest(BaseModel):
    prefer_cloud: bool = False
    use_cache: bool = True

class ChunkingRequest(BaseModel):
    chunk_size: Optional[int] = 2048
    overlap: Optional[int] = 256

class EmbeddingRequest(BaseModel):
    provider: Optional[str] = "openai"
    resume: bool = False

# Company Branding schemas
class CompanyBrandingBase(BaseModel):
    company_name: str
    logo_url: Optional[str] = None

class CompanyBrandingCreate(CompanyBrandingBase):
    pass

class CompanyBranding(CompanyBrandingBase):
    id: int

    class Config:
        from_attributes = True