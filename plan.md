# Document Q&A Assistant - Complete Migration Plan

## Overview
This document outlines the comprehensive migration strategy for transforming the current Streamlit prototype into a production-ready enterprise web application with Next.js frontend and FastAPI backend.

## Current Architecture Assessment

### Existing System (Streamlit)
- **Frontend**: Streamlit with custom CSS styling
- **Backend**: Python scripts with subprocess calls
- **Database**: Neon PostgreSQL with pgvector
- **Authentication**: Custom session-based auth with role management
- **Document Processing**: Python scripts (extraction, chunking, embedding)
- **LLM Integration**: OpenAI and Mistral APIs

### Target Architecture (Next.js + FastAPI)
- **Frontend**: Next.js 15 with React 19, TypeScript, Tailwind CSS
- **Backend**: FastAPI with existing Python logic
- **Database**: Neon PostgreSQL (unchanged)
- **Authentication**: NextAuth.js with JWT tokens
- **Document Processing**: REST API endpoints
- **LLM Integration**: Maintain existing providers

## Migration Strategy

### Phase 1: Backend API Layer (Weeks 1-4)

#### 1.1 FastAPI Setup
```python
# app/main.py
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Document Q&A API")

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded documents
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")
```

#### 1.2 API Endpoints
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `POST /api/documents/upload` - Document upload and processing
- `GET /api/documents` - List user documents
- `POST /api/chat` - Chat with documents
- `GET /api/admin/users` - Admin user management
- `POST /api/admin/api-config` - API configuration

#### 1.3 Database Integration
- Reuse existing database schema
- Add FastAPI database session management
- Maintain pgvector for embeddings

### Phase 2: Frontend Foundation (Weeks 5-8)

#### 2.1 Next.js Application Structure
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── login/
│   ├── dashboard/
│   ├── chat/
│   ├── documents/
│   └── admin/
├── components/
│   ├── ui/
│   ├── auth/
│   ├── chat/
│   └── documents/
├── lib/
│   ├── auth.ts
│   ├── api.ts
│   └── utils.ts
└── types/
```

#### 2.2 Core Components
- **Authentication**: NextAuth.js with custom provider
- **Layout**: Responsive dashboard layout
- **Navigation**: Role-based navigation menu
- **Theme**: Dark/light mode with Tailwind CSS

#### 2.3 API Integration
```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL;

export const api = {
  auth: {
    login: (credentials: LoginCredentials) => 
      fetch(`${API_BASE}/api/auth/login`, { method: 'POST', body: JSON.stringify(credentials) }),
    register: (userData: RegisterData) => 
      fetch(`${API_BASE}/api/auth/register`, { method: 'POST', body: JSON.stringify(userData) }),
  },
  documents: {
    upload: (formData: FormData) => 
      fetch(`${API_BASE}/api/documents/upload`, { method: 'POST', body: formData }),
    list: () => fetch(`${API_BASE}/api/documents`),
  },
  chat: {
    send: (message: string, context?: string) => 
      fetch(`${API_BASE}/api/chat`, { method: 'POST', body: JSON.stringify({ message, context }) }),
  }
};
```

### Phase 3: Feature Migration (Weeks 9-14)

#### 3.1 Authentication System
- Migrate from Streamlit session state to NextAuth.js
- Maintain role-based access control
- Add JWT token management

#### 3.2 Document Processing Interface
```typescript
// components/documents/UploadZone.tsx
'use client';
import { useDropzone } from 'react-dropzone';
import { useState } from 'react';

export function UploadZone() {
  const [uploading, setUploading] = useState(false);
  
  const { getRootProps, getInputProps } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/markdown': ['.md'],
      'text/html': ['.html'],
    },
    onDrop: async (acceptedFiles) => {
      setUploading(true);
      const formData = new FormData();
      acceptedFiles.forEach(file => formData.append('files', file));
      
      try {
        await api.documents.upload(formData);
        // Refresh document list
      } catch (error) {
        // Handle error
      } finally {
        setUploading(false);
      }
    },
  });

  return (
    <div {...getRootProps()} className="border-2 border-dashed rounded-lg p-8 text-center">
      <input {...getInputProps()} />
      {uploading ? (
        <div>Uploading...</div>
      ) : (
        <div>
          <p>Drag & drop files here, or click to select</p>
          <p className="text-sm text-gray-500">PDF, DOCX, MD, HTML files supported</p>
        </div>
      )}
    </div>
  );
}
```

#### 3.3 Chat Interface
- Real-time chat with WebSocket support
- Message history with proper citations
- File context integration
- Streaming responses for better UX

#### 3.4 Admin Dashboard
- User management interface
- API configuration panel
- System monitoring
- Database management tools

### Phase 4: Advanced Features & Optimization (Weeks 15-18)

#### 4.1 Real-time Features
- WebSocket connections for live updates
- Server-sent events for processing status
- Real-time chat with typing indicators

#### 4.2 Performance Optimization
- Image optimization with Next.js Image component
- Code splitting and lazy loading
- CDN integration for static assets
- Database query optimization

#### 4.3 Monitoring & Analytics
- Application performance monitoring
- User behavior analytics
- Error tracking and logging
- Usage metrics dashboard

## Technology Stack

### Frontend (Next.js)
```json
{
  "dependencies": {
    "next": "15.0.0",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "next-auth": "^5.0.0",
    "@tanstack/react-query": "^5.0.0",
    "react-hook-form": "^7.0.0",
    "recharts": "^2.0.0",
    "socket.io-client": "^4.0.0"
  }
}
```

### Backend (FastAPI)
```txt
fastapi==0.104.0
uvicorn==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
# Plus all existing dependencies from requirements.txt
```

## Database Schema (Extended)

### Users Table (Existing)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### API Sessions Table (New)
```sql
CREATE TABLE api_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Deployment Architecture

### Production Environment
```
Frontend (Next.js) → Vercel
    ↓
Backend (FastAPI) → Railway/Render
    ↓
Database → Neon PostgreSQL
    ↓
File Storage → Backblaze B2/AWS S3
```

### Development Environment
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Migration Timeline

### Phase 1: Backend API (Weeks 1-4)
- [ ] Setup FastAPI application
- [ ] Create authentication endpoints
- [ ] Implement document upload API
- [ ] Build chat API endpoints
- [ ] Add admin API endpoints
- [ ] Database session management
- [ ] API documentation with Swagger

### Phase 2: Frontend Foundation (Weeks 5-8)
- [ ] Initialize Next.js application
- [ ] Implement NextAuth.js authentication
- [ ] Create responsive layout components
- [ ] Build API integration layer
- [ ] Add error handling and loading states
- [ ] Implement theme system

### Phase 3: Core Features (Weeks 9-14)
- [ ] Document upload interface
- [ ] Chat interface with real-time updates
- [ ] Document management dashboard
- [ ] Admin user management
- [ ] API configuration panel
- [ ] Database management tools

### Phase 4: Advanced Features (Weeks 15-18)
- [ ] Real-time WebSocket integration
- [ ] Performance optimization
- [ ] Monitoring and analytics
- [ ] Progressive Web App features
- [ ] Offline functionality
- [ ] Comprehensive testing

### Phase 5: Deployment & Migration (Weeks 19-20)
- [ ] Production deployment setup
- [ ] Data migration scripts
- [ ] Load testing
- [ ] Security audit
- [ ] User acceptance testing
- [ ] Go-live and monitoring

## Risk Mitigation

### Technical Risks
1. **Database Migration**: Maintain backward compatibility during transition
2. **API Integration**: Use feature flags for gradual rollout
3. **Performance**: Conduct load testing before production
4. **Security**: Implement comprehensive security testing

### Business Risks
1. **Downtime**: Plan for zero-downtime migration
2. **User Training**: Provide documentation and training materials
3. **Rollback Plan**: Maintain Streamlit version as fallback

## Success Metrics

### Performance
- Page load time < 2 seconds
- API response time < 500ms
- 99.9% uptime
- Concurrent users: 1000+

### User Experience
- Mobile-responsive design
- Real-time updates < 1 second
- Intuitive navigation
- Accessibility compliance

### Business
- Reduced operational costs
- Improved user satisfaction
- Increased user engagement
- Better scalability

## Next Steps

### Immediate Actions (Week 1)
1. Setup development environment
2. Create FastAPI proof of concept
3. Initialize Next.js application
4. Define API contract between frontend and backend

### Short-term Goals (Month 1)
1. Complete backend API implementation
2. Build basic frontend authentication
3. Implement document upload functionality
4. Create basic chat interface

This migration plan provides a comprehensive roadmap for transforming the Document Q&A Assistant into a production-ready enterprise application while maintaining all existing functionality and improving performance, scalability, and user experience.