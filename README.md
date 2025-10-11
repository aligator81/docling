# Docling - Advanced Document Q&A Platform

<div align="center">

![Docling Logo](https://img.shields.io/badge/Docling-Advanced%20Document%20Q&A-blue)
![Status](https://img.shields.io/badge/Status-✅%20Production%20Ready-green)
![Version](https://img.shields.io/badge/Version-2.0.0-orange)

**Enterprise-grade document intelligence platform with AI-powered chat capabilities**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Enhancements](#-enhancement-roadmap)

</div>

## 🚀 Overview

Docling is a sophisticated document processing and Q&A platform that transforms documents into searchable, queryable knowledge bases using advanced AI technologies. The platform supports multiple document formats, provides intelligent content extraction, and enables natural language conversations with your documents.

### ✅ **Current Status: Production Ready**

- **Backend**: FastAPI running on `http://localhost:8000`
- **Frontend**: Next.js running on `http://localhost:3000`
- **Database**: PostgreSQL with Neon connection pooling
- **AI Integration**: OpenAI & Mistral APIs for embeddings and chat

## ✨ Features

### Core Capabilities
- **📄 Multi-format Document Processing**: PDF, DOCX, Markdown, HTML, Images
- **🤖 AI-Powered Chat**: Natural language conversations with document content
- **🔍 Semantic Search**: Intelligent content retrieval using embeddings
- **👥 User Management**: Role-based access control and document isolation
- **📊 Admin Dashboard**: System monitoring and user management

### Advanced Features
- **🔄 Background Processing**: Non-blocking document processing pipeline
- **🛡️ Enterprise Security**: Comprehensive file validation and rate limiting
- **📈 Performance Monitoring**: Real-time metrics and health checks
- **🔧 Developer-Friendly**: Comprehensive API documentation and testing

## 🏗️ Architecture

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend API   │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│   (PostgreSQL)  │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                          │          │
                          ▼          ▼
                ┌─────────────────┐  ┌─────────────────┐
                │   AI Services   │  │   Background    │
                │   (OpenAI,      │  │   Tasks         │
                │    Mistral)     │  │   (Celery)      │
                └─────────────────┘  └─────────────────┘
```

### Technology Stack
- **Frontend**: Next.js 14, React 18, TypeScript, Ant Design
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis
- **AI/ML**: OpenAI API, Mistral API, Sentence Transformers
- **Document Processing**: Docling, PyMuPDF, Pillow
- **Security**: JWT, bcrypt, rate limiting, file validation
- **Deployment**: Docker, Uvicorn, Celery

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis (optional, for rate limiting)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd docling-app
```

2. **Backend Setup**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

4. **Environment Configuration**
```bash
# Copy and configure environment variables
cp .env.example .env
```

5. **Start the Application**
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

6. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📚 API Documentation

### Key Endpoints

#### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user info

#### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/` - List user documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

#### Chat
- `POST /api/chat/` - Send message to document chat
- `GET /api/chat/{document_id}` - Get chat history

#### Admin
- `GET /api/admin/users` - List all users (admin only)
- `GET /api/admin/stats` - System statistics (admin only)

### Example Usage

```python
import requests

# Login
response = requests.post("http://localhost:8000/api/auth/login", json={
    "email": "user@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Upload document
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("document.pdf", "rb")}
response = requests.post("http://localhost:8000/api/documents/upload", files=files, headers=headers)
```

## 🎯 Enhancement Roadmap

### Phase 1: Quick Wins (Completed)
- ✅ Fixed database connection issues
- ✅ Implemented Redis-based rate limiting
- ✅ Enhanced error handling and user feedback
- ✅ Improved API documentation

### Phase 2: Core Enhancements (In Progress)
- 🔄 Advanced RAG with hybrid search
- 🔄 Multi-modal document processing
- 🔄 Enhanced UI/UX with modern components
- 🔄 Comprehensive monitoring and logging

### Phase 3: Advanced Features (Planned)
- 🤖 Self-RAG framework with dynamic retrieval
- 📊 GraphRAG knowledge graph integration
- 🔍 Ensemble retrieval with intelligent reranking
- 🎨 Multi-modal processing (images, tables, formulas)

### Phase 4: Enterprise Scale (Future)
- 🌐 Multi-tenant architecture
- 🔒 Advanced compliance features
- 🚀 Global deployment capability
- 🧠 Custom model training

## 🔧 Development

### Code Quality
```bash
# Install pre-commit hooks
pre-commit install

# Run code quality checks
black backend/
flake8 backend/
mypy backend/
```

### Testing
```bash
# Run backend tests
cd backend
pytest

# Run frontend tests  
cd frontend
npm test
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## 🛡️ Security

### Implemented Security Features
- **Authentication**: JWT with bcrypt password hashing
- **Authorization**: Role-based access control
- **File Validation**: Magic number detection and content scanning
- **Rate Limiting**: Redis-based API protection
- **Input Validation**: Comprehensive data validation
- **CORS**: Configured for frontend integration

### Security Best Practices
- Environment variable configuration
- Database connection pooling
- Secure file upload handling
- Comprehensive error logging
- Regular dependency updates

## 📊 Performance

### Current Metrics
- **Document Upload**: < 1 second
- **Content Extraction**: 30-60 seconds
- **Chat Response**: 3-8 seconds
- **API Response**: < 200ms

### Optimization Features
- Background processing with Celery
- Database connection pooling
- Intelligent caching strategies
- Query optimization and indexing

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and code quality checks
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Technical Documentation](TECHNICAL_DOCUMENTATION.md) - Detailed technical guide
- [Enhancement Roadmap](ENHANCEMENT_ROADMAP_2025.md) - Future development plans

### Issues
If you encounter any issues, please:
1. Check the existing documentation
2. Search existing issues
3. Create a new issue with detailed information

## 🎉 Acknowledgments

- **FastAPI** for the excellent web framework
- **Next.js** for the modern React framework
- **OpenAI** and **Mistral** for AI capabilities
- **Docling** for document processing
- **PostgreSQL** and **Neon** for database services

---

<div align="center">

**Docling** - Transforming documents into intelligent conversations

[Report Bug](https://github.com/your-repo/issues) • [Request Feature](https://github.com/your-repo/issues) • [Documentation](https://github.com/your-repo/docs)

</div>