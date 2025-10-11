
# Technical Documentation - Document Q&A Application

## 📚 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Service Components](#service-components)
5. [Enhanced Features](#enhanced-features)
   - [Background Processing](#background-processing)
   - [Security & Validation](#security--validation)
   - [Monitoring & Logging](#monitoring--logging)
   - [Rate Limiting](#rate-limiting)
   - [Advanced Search](#advanced-search)
   - [Document Versioning](#document-versioning)
   - [Collaboration Features](#collaboration-features)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)
9. [Development Guidelines](#development-guidelines)

## 🎉 **ENHANCED VERSION 2.0**

**✅ COMPLETED ENHANCEMENTS**
- **Critical Database Fixes** - SQLAlchemy query optimization
- **Background Processing** - Celery-based task processing
- **Enterprise Security** - File validation and rate limiting
- **Advanced Features** - Versioning, collaboration, enhanced search
- **Production Monitoring** - Structured logging and performance tracking

## 🏗️ Architecture Overview

### System Components

#### Backend Architecture
```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Application configuration
├── database.py          # Database connection and session management
├── models.py            # SQLAlchemy data models
├── schemas.py           # Pydantic schemas for API validation
├── auth.py              # Authentication and authorization
├── routers/             # API route handlers
│   ├── auth.py          # Authentication endpoints
│   ├── documents.py     # Document management endpoints
│   ├── chat.py          # Chat and Q&A endpoints
│   ├── admin.py         # Administrative endpoints
│   └── processing.py    # Document processing endpoints
└── services/            # Business logic services
    ├── document_processor.py    # Document extraction service
    ├── document_chunker.py      # Document chunking service
    └── embedding_service.py     # Embedding generation service
```

#### Frontend Architecture
```
src/
├── app/                 # Next.js app directory
│   ├── page.tsx         # Home page
│   ├── layout.tsx       # Root layout
│   ├── globals.css      # Global styles
│   └── [pages]/         # Route pages
│       ├── login/
│       ├── documents/
│       ├── chat/
│       └── admin/
├── components/          # Reusable React components
│   ├── ui/              # UI components
│   ├── auth/            # Authentication components
│   ├── documents/       # Document management components
│   └── chat/            # Chat interface components
├── lib/                 # Utility libraries
│   ├── auth.ts          # Authentication utilities
│   └── api.ts           # API client
└── types/               # TypeScript type definitions
```

## 🗄️ Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    role VARCHAR(20) DEFAULT 'user' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX idx_users_role ON users(role);
```

#### Documents Table
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(20) DEFAULT 'not processed' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    processed_at TIMESTAMP,
    content TEXT,  -- Extracted content
    metadata_ TEXT  -- JSON metadata
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
```

#### Document Chunks Table
```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    page_numbers INTEGER[],  -- Array of page numbers
    section_title VARCHAR(255),
    chunk_type VARCHAR(50),
    token_count INTEGER
);

CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_text ON document_chunks USING gin(chunk_text gin_trgm_ops);
```

#### Embeddings Table
```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER REFERENCES document_chunks(id) ON DELETE CASCADE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    page_numbers INTEGER[],
    title VARCHAR(255),
    embedding_vector TEXT NOT NULL,  -- JSON array as text
    embedding_provider VARCHAR(100) NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_provider ON embeddings(embedding_provider);
CREATE INDEX idx_embeddings_model ON embeddings(embedding_model);
```

## 🌐 API Endpoints

### Authentication Endpoints

#### POST /api/auth/register
```python
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    Request: {username, email, password}
    Response: User object
    """
```

#### POST /api/auth/login
```python
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login user and return JWT token
    Request: username, password (form data)
    Response: {access_token, token_type, user}
    """
```

### Document Management Endpoints

#### POST /api/documents/upload
```python
@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document
    Request: Multipart form with file
    Response: Document object with upload status
    """
```

#### GET /api/documents/
```python
@router.get("/", response_model=List[DocumentSchema])
async def list_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List documents (user's documents for regular users, all for admins)
    Response: List of Document objects
    """
```

#### POST /api/documents/{document_id}/extract
```python
@router.post("/{document_id}/extract")
async def extract_document_content(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Extract content from uploaded document
    Response: Extraction status and content length
    """
```

### Chat Endpoints

#### POST /api/chat/
```python
@router.post("/", response_model=ChatResponse)
async def chat_with_documents(
    message: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Chat with documents using embeddings and LLM
    Request: {message: str, document_ids: List[int] (optional)}
    Response: {response: str, context_docs: List[int], model_used: str}
    """
```

## 🔧 Service Components

### Document Processor Service

#### Key Features
- **Multi-format Support**: PDF, DOCX, PPTX, XLSX, HTML, MD, Images
- **Fallback Logic**: Docling → Mistral OCR → Simple text reading
- **Performance Optimization**: Caching, timeout handling, progress tracking

#### Core Methods
```python
class DocumentProcessor:
    async def extract_document(self, file_path: str, prefer_cloud: bool = False) -> ProcessingResult:
        """
        Extract document with intelligent fallback logic
        """
    
    async def extract_with_docling(self, file_path: str, enable_ocr: bool = False) -> ProcessingResult:
        """
        Extract document using Docling (local processing)
        """
    
    async def extract_with_mistral_ocr(self, file_path: str) -> ProcessingResult:
        """
        Extract document using Mistral OCR (cloud processing)
        """
```

### Document Chunker Service

#### Chunking Strategy
- **Hybrid Approach**: Combines semantic and token-based chunking
- **Metadata Extraction**: Page numbers, section titles, token counts
- **Language Support**: Enhanced French document handling

#### Core Methods
```python
class DocumentChunker:
    async def chunk_document_content(self, content: str, filename: str) -> List[Dict]:
        """
        Chunk document content with enhanced metadata extraction
        """
    
    def extract_page_numbers_from_text(self, text: str) -> str:
        """
        Extract page numbers from chunk text content
        """
    
    def extract_section_title_from_text(self, text: str) -> str:
        """
        Extract section title from chunk text content
        """
```

### Embedding Service

#### Features
- **Multi-provider Support**: OpenAI and Mistral embeddings
- **Robust Error Handling**: Retry mechanisms, timeout management
- **Progress Tracking**: Checkpoint system for large files

#### Core Methods
```python
class EmbeddingService:
    async def get_embedding(self, text: str, emergency_mode: bool = False) -> List[float]:
        """
        Get embedding for text using configured provider
        """
    
    def validate_and_split_chunk(self, text: str, max_tokens: int = None) -> Tuple[List[str], List[int]]:
        """
        Validate chunk size and split if necessary
        """
    
    async def process_embeddings_from_db(self, db, resume: bool = False) -> EmbeddingResult:
        """
        Process all chunks that need embeddings from database
        """
```

## 🚀 Enhanced Features

### Background Processing

#### Celery Task System
```python
# Background document processing with Celery
@celery_app.task
def process_document_task(document_id: int):
    """Complete document processing pipeline in background"""
    # Extract → Chunk → Embed → Update status

@celery_app.task
def extract_document_task(document_id: int):
    """Background document extraction only"""

@celery_app.task
def chunk_document_task(document_id: int):
    """Background document chunking only"""

@celery_app.task
def embed_document_task(document_id: int):
    """Background embedding generation only"""
```

#### API Endpoints
```python
# Background processing endpoints
POST /api/documents/{document_id}/process-background
POST /api/documents/{document_id}/extract-background
POST /api/documents/{document_id}/chunk-background
POST /api/documents/{document_id}/embed-background
```

### Security & Validation

#### File Security Service
```python
class FileSecurity:
    def validate_file_content(self, file_path: str) -> bool:
        """Comprehensive file validation"""
        # MIME type detection
        # Magic number validation
        # Malware pattern detection
        # Compression bomb protection

    def scan_for_malware_signatures(self, file_path: str) -> bool:
        """Scan for malicious patterns"""

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash for integrity verification"""
```

#### Enhanced Upload Validation
```python
# Secure upload with comprehensive validation
@router.post("/upload")
async def secure_upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    security: FileSecurity = Depends()
):
    """Upload with security validation"""
```

### Monitoring & Logging

#### Structured Logging
```python
class StructuredLogger:
    def log_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Log API requests with structured format"""

    def log_document_event(self, event_type: str, document_id: int, **kwargs):
        """Log document-related events"""

    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
```

#### System Monitoring
```python
class SystemMonitor:
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get CPU, memory, and disk usage metrics"""

    def get_database_connections(self) -> Dict[str, Any]:
        """Monitor database connection pool"""
```

#### Health Check Endpoints
```python
GET /health              # Basic health check
GET /api/metrics         # Detailed metrics (authenticated)
```

### Rate Limiting

#### Redis-Based Rate Limiting
```python
class RateLimiter:
    def __init__(self):
        self.limits = {
            'upload': {'requests': 10, 'window': 3600},     # 10 uploads/hour
            'chat': {'requests': 60, 'window': 60},        # 60 chats/minute
            'api': {'requests': 1000, 'window': 3600},     # 1000 API calls/hour
            'admin': {'requests': 100, 'window': 3600},    # 100 admin actions/hour
        }

    async def check_rate_limit(self, request: Request) -> bool:
        """Check if request exceeds rate limit"""
```

#### User-Specific Limits
```python
class UserRateLimiter:
    def check_user_limit(self, user_id: int, user_role: str, endpoint_type: str) -> bool:
        """Check user-specific rate limits based on role"""
```

### Advanced Search

#### Search Service
```python
class AdvancedSearch:
    def search_documents(self, query: str = None, filters: Dict = None) -> Dict:
        """Advanced search with filters and pagination"""

    def search_similar_documents(self, document_id: int, limit: int = 10) -> Dict:
        """Find similar documents using embeddings"""

    def get_search_suggestions(self, query: str, user_id: int) -> List[str]:
        """Get search suggestions from existing content"""
```

#### Search API Endpoints
```python
GET /api/search/documents
    ?query=search_term
    &status=processed
    &file_type=pdf
    &date_from=2024-01-01
    &date_to=2024-12-31
    &sort_by=created_at
    &sort_order=desc
    &page=1
    &per_page=20
```

### Document Versioning

#### Version Management Service
```python
class DocumentVersionService:
    def create_version(self, document_id: int, user_id: int, changes: str) -> Dict:
        """Create a new document version"""

    def get_versions(self, document_id: int) -> Dict:
        """Get all versions of a document"""

    def restore_version(self, document_id: int, version_number: int, user_id: int) -> Dict:
        """Restore document to specific version"""
```

#### Version API Endpoints
```python
POST   /api/documents/{document_id}/versions              # Create version
GET    /api/documents/{document_id}/versions              # List versions
POST   /api/documents/{document_id}/versions/{version_id}/restore  # Restore version
```

### Collaboration Features

#### Collaboration Service
```python
class DocumentCollaborationService:
    def add_collaborator(self, document_id: int, user_email: str, permission: str, added_by: int) -> Dict:
        """Add user as collaborator"""

    def check_collaborator_permission(self, document_id: int, user_id: int, required_permission: str) -> bool:
        """Check if user has required permission level"""
```

#### Comment System
```python
class DocumentCommentService:
    def add_comment(self, document_id: int, user_id: int, content: str, comment_type: str) -> Dict:
        """Add comment to document"""

    def get_comments(self, document_id: int) -> Dict:
        """Get all comments for document"""
```

#### Activity Tracking
```python
class DocumentActivityService:
    def log_activity(self, document_id: int, user_id: int, activity_type: str, description: str) -> None:
        """Log document activity"""

    def get_activities(self, document_id: int, limit: int = 50) -> Dict:
        """Get recent activities for document"""
```

#### Collaboration API Endpoints
```python
POST   /api/documents/{document_id}/collaborators          # Add collaborator
DELETE /api/documents/{document_id}/collaborators/{user_id} # Remove collaborator
GET    /api/documents/{document_id}/collaborators          # List collaborators
POST   /api/documents/{document_id}/comments              # Add comment
GET    /api/documents/{document_id}/comments              # List comments
GET    /api/documents/{document_id}/activities            # Get activities
```

## ⚙️ Configuration

### Environment Variables
```bash
# Database
NEON_CONNECTION_STRING=postgresql://user:pass@host/db

# API Keys
OPENAI_API_KEY=sk-...
MISTRAL_API_KEY=...

# Security
SECRET_KEY=your-secret-key-change-in-production

# Application
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes
```

### Application Settings
```python
class Settings(BaseSettings):
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = ""
    
    # API Keys
    openai_api_key: str = ""
    mistral_api_key: str = ""
    
    # File upload settings
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = [".pdf", ".docx", ".md", ".html", ".png", ".jpg"]
```

## 🚀 Deployment

### Docker Configuration

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY frontend/ .

# Build application
RUN npm run build

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/docling
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
    depends_on:
      - db

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=docling
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Document Processing Timeouts
**Problem**: Document extraction times out for large files
**Solution**: 
```python
# Increase timeout in document_processor.py
timeout_seconds = max(60, min(int(file_size_mb * 2), 1800))  # Max 30 minutes
```

#### 2. Database Connection Issues
**Problem**: Database connection failures or slow queries
**Solution**:
```python
# Add connection pooling in database.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

#### 3. Memory Issues with Large Files
**Problem**: High memory usage during document processing
**Solution**:
```python
# Implement streaming processing
def process_large_file(file_path: str):
    with open(file_path, 'rb') as f:
        for chunk in read_in_chunks(f):
            process_chunk(chunk)

def read_in_chunks(file_object, chunk_size=1024*1024):  # 1MB chunks
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data
```

#### 4. API Rate Limiting
**Problem**: OpenAI/Mistral API rate limits exceeded
**Solution**:
```python
# Implement rate limiting in embedding_service.py
import asyncio

async def process_with_rate_limit():
    # Process chunk
    await asyncio.sleep(1)  # 1 second delay between API calls
```

### Performance Optimization

#### Database Optimization
```sql
-- Add performance indexes
CREATE INDEX CONCURRENTLY idx_documents_created_at ON documents(created_at);
CREATE INDEX CONCURRENTLY idx_chunks_created_at ON document_chunks(created_at);
CREATE INDEX CONCURRENTLY idx_embeddings_created_at ON embeddings(created_at);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM documents WHERE user_id = 1 AND status = 'embedding';
```

#### Application Optimization
```python
# Use connection pooling
from sqlalchemy.pool import StaticPool

# For development with SQLite
engine = create_engine(
    "sqlite:///./test.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
```

## 💻 Development Guidelines

### Code Standards

#### Python Development
```python
# Use type hints
def process_document(file_path: str, user_id: int) -> ProcessingResult:
    """Process document with comprehensive error handling."""
    try:
        # Implementation
        return ProcessingResult(success=True, content=content)
    except Exception as e:
        logger.error(f"Failed to process document {file_path}: {e}")
        return ProcessingResult(success=False, content="")

# Use async/await for I/O operations
async def extract_document_async(file_path: str) -> ProcessingResult:
    result = await asyncio.get_event_loop().run_in_executor(
        None, extract_document_sync, file_path
    )
    return result
```

#### Frontend Development
```typescript
// Use TypeScript interfaces
interface Document {
  id: number;
  filename: string;
  original_filename: string;
  status: DocumentStatus;
  created_at: string;
}

// Use React hooks properly
const useDocuments = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const data = await api.getDocuments();
      setDocuments(data);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };

  return { documents, loading, refetch: loadDocuments };
};
```

### Testing Strategy

#### Backend Testing
```python
# tests/test_documents.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_upload_document(client, mock_user):
    with open("test.pdf", "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers={"Authorization": f"Bearer {mock_user.token}"}
        )
    assert response.status_code == 200
    assert response.json()["message"] == "Document uploaded successfully"
```

#### Frontend Testing
```typescript
// tests/documents.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import DocumentsPage from '@/app/documents/page';

describe('DocumentsPage', () => {
  it('renders document list', async () => {
    render(<DocumentsPage />);
    
    expect(await screen.findByText('Document Management')).toBeInTheDocument();
    expect(screen.getByText('Upload New Document')).toBeInTheDocument();
  });

  it('handles file upload', async () => {
    render(<DocumentsPage />);
    
    const fileInput = screen.getByTestId('file-upload');
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
