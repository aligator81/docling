# Development Guide

This guide covers the development workflow, code structure, and best practices for Docling v2.

## Project Structure

```
docling_v2/
├── backend/                 # FastAPI backend
│   ├── app/                # Main application code
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic services
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── main.py         # Application entry point
│   ├── alembic/            # Database migrations
│   ├── data/               # Uploaded files and output
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app router pages
│   │   ├── components/    # React components
│   │   └── types/         # TypeScript type definitions
│   └── package.json       # Node.js dependencies
├── utils/                  # Shared utilities
└── docs/                  # Documentation
```

## Backend Development

### Architecture Overview

The backend follows a clean architecture pattern:

- **Models**: SQLAlchemy ORM models
- **Schemas**: Pydantic validation schemas
- **Services**: Business logic layer
- **Routers**: API endpoint handlers
- **Database**: PostgreSQL with SQLAlchemy

### Key Components

#### Document Processing Pipeline
1. **Upload**: File validation and storage
2. **Extraction**: Content extraction using Docling
3. **Chunking**: Text segmentation for embeddings
4. **Embedding**: Vector generation for semantic search
5. **Storage**: Database persistence

#### Authentication System
- JWT-based authentication
- Role-based access control (RBAC)
- Secure password hashing with bcrypt

### Development Setup

1. **Set up Python environment**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure database**
   ```bash
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your database configuration
   ```

3. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start development server**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### API Development

#### Adding New Endpoints

1. **Create schema** (`app/schemas/`)
   ```python
   from pydantic import BaseModel

   class NewFeatureRequest(BaseModel):
       name: str
       description: str
   ```

2. **Create service** (`app/services/`)
   ```python
   class NewFeatureService:
       def create_feature(self, request: NewFeatureRequest):
           # Business logic here
           pass
   ```

3. **Create router** (`app/routers/`)
   ```python
   from fastapi import APIRouter, Depends
   from app.schemas import NewFeatureRequest
   from app.services import NewFeatureService

   router = APIRouter(prefix="/api/features", tags=["features"])

   @router.post("/")
   async def create_feature(
       request: NewFeatureRequest,
       service: NewFeatureService = Depends()
   ):
       return await service.create_feature(request)
   ```

4. **Register router** (`app/main.py`)
   ```python
   from app.routers import features

   app.include_router(features.router)
   ```

### Database Operations

#### Creating Models
```python
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class NewFeature(Base):
    __tablename__ = "new_features"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### Creating Migrations
```bash
alembic revision --autogenerate -m "Add new features table"
alembic upgrade head
```

## Frontend Development

### Architecture Overview

The frontend uses Next.js 14 with:

- **App Router**: File-based routing
- **TypeScript**: Type safety
- **Ant Design**: UI components
- **React Query**: Data fetching and caching
- **Axios**: HTTP client

### Key Components

#### Pages Structure
- `/` - Dashboard
- `/documents` - Document management
- `/chat` - Document Q&A
- `/login` - Authentication
- `/admin` - Admin panel

#### State Management
- **Local State**: React hooks (useState, useEffect)
- **Server State**: React Query for API data
- **Form State**: React Hook Form

### Development Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   # Set NEXT_PUBLIC_API_URL in .env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

### Component Development

#### Creating New Components

1. **Create component** (`src/components/`)
   ```typescript
   import { FC } from 'react';

   interface NewComponentProps {
     title: string;
     onAction: () => void;
   }

   export const NewComponent: FC<NewComponentProps> = ({ 
     title, 
     onAction 
   }) => {
     return (
       <div>
         <h1>{title}</h1>
         <button onClick={onAction}>Click me</button>
       </div>
     );
   };
   ```

2. **Create page** (`src/app/new-page/page.tsx`)
   ```typescript
   'use client';

   import { NewComponent } from '@/components/NewComponent';

   export default function NewPage() {
     const handleAction = () => {
       console.log('Action triggered');
     };

     return (
       <div>
         <NewComponent 
           title="New Feature" 
           onAction={handleAction} 
         />
       </div>
     );
   }
   ```

### API Integration

#### Using React Query
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

// Query example
const { data, isLoading } = useQuery({
  queryKey: ['features'],
  queryFn: () => apiClient.get('/api/features')
});

// Mutation example
const mutation = useMutation({
  mutationFn: (data) => apiClient.post('/api/features', data),
  onSuccess: () => {
    // Handle success
  }
});
```

## Testing

### Backend Testing

1. **Unit Tests**
   ```python
   import pytest
   from app.services.new_feature import NewFeatureService

   def test_create_feature():
       service = NewFeatureService()
       result = service.create_feature({"name": "test"})
       assert result.name == "test"
   ```

2. **Integration Tests**
   ```python
   @pytest.mark.asyncio
   async def test_feature_endpoint(client):
       response = await client.post("/api/features", json={"name": "test"})
       assert response.status_code == 200
   ```

3. **Run tests**
   ```bash
   cd backend
   pytest
   ```

### Frontend Testing

1. **Component Tests**
   ```typescript
   import { render, screen } from '@testing-library/react';
   import { NewComponent } from './NewComponent';

   test('renders component', () => {
     render(<NewComponent title="Test" onAction={() => {}} />);
     expect(screen.getByText('Test')).toBeInTheDocument();
   });
   ```

2. **Run tests**
   ```bash
   cd frontend
   npm test
   ```

## Code Quality

### Backend Code Quality

1. **Formatting**
   ```bash
   black backend/
   ```

2. **Linting**
   ```bash
   flake8 backend/
   ```

3. **Type Checking**
   ```bash
   mypy backend/
   ```

### Frontend Code Quality

1. **Formatting**
   ```bash
   npx prettier --write .
   ```

2. **Linting**
   ```bash
   npx eslint .
   ```

3. **Type Checking**
   ```bash
   npx tsc --noEmit
   ```

## Debugging

### Backend Debugging

1. **Enable debug logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Use FastAPI debug mode**
   ```bash
   uvicorn app.main:app --reload --log-level debug
   ```

### Frontend Debugging

1. **React Developer Tools**
   - Install browser extension
   - Inspect component hierarchy

2. **Network Debugging**
   - Use browser dev tools
   - Check API responses

## Performance Optimization

### Backend Optimization

1. **Database Indexing**
   ```sql
   CREATE INDEX idx_documents_user_id ON documents(user_id);
   ```

2. **Query Optimization**
   - Use eager loading for relationships
   - Implement pagination

3. **Caching**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=128)
   def get_cached_data(key):
       return expensive_operation()
   ```

### Frontend Optimization

1. **Code Splitting**
   ```typescript
   const LazyComponent = lazy(() => import('./LazyComponent'));
   ```

2. **Image Optimization**
   ```typescript
   import Image from 'next/image';
   <Image src="/image.jpg" alt="Description" width={500} height={300} />
   ```

3. **Bundle Analysis**
   ```bash
   npm run build -- --analyze
   ```

## Security Best Practices

### Backend Security

1. **Input Validation**
   ```python
   from pydantic import BaseModel, validator

   class UserCreate(BaseModel):
       email: str
       
       @validator('email')
       def validate_email(cls, v):
           if not re.match(r'[^@]+@[^@]+\.[^@]+', v):
               raise ValueError('Invalid email format')
           return v
   ```

2. **Authentication**
   - Use secure JWT tokens
   - Implement proper session management

### Frontend Security

1. **XSS Protection**
   - Sanitize user input
   - Use Content Security Policy

2. **CSRF Protection**
   - Use anti-CSRF tokens
   - Implement proper CORS policies

## Deployment Preparation

### Backend Checklist
- [ ] All tests passing
- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] Logging configured
- [ ] Security settings reviewed

### Frontend Checklist
- [ ] Build successful
- [ ] Environment variables set
- [ ] API endpoints configured
- [ ] Performance optimized

## Troubleshooting

### Common Issues

1. **Database Connection**
   ```bash
   # Check connection
   psql $DATABASE_URL -c "SELECT 1;"
   ```

2. **API CORS Issues**
   ```python
   # Check CORS configuration
   from fastapi.middleware.cors import CORSMiddleware
   ```

3. **Build Failures**
   ```bash
   # Clear cache and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

### Getting Help

- Check existing documentation
- Search GitHub issues
- Create detailed bug reports
- Ask in community channels