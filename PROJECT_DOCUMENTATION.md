# Docling Document Processing & Q&A System - Comprehensive Documentation

## 📋 Overview

This project is a comprehensive document processing and question-answering system built on top of [Docling](https://github.com/DS4SD/docling), an open-source document processing library. It provides a complete pipeline for extracting, chunking, embedding, and querying documents with a user-friendly Streamlit interface.

## 🎯 Key Features

- **Universal Document Support**: Process PDF, DOCX, XLSX, PPTX, Markdown, HTML, and more
- **Smart Chunking**: AI-powered document structure understanding with hierarchical and hybrid chunking
- **Semantic Search**: Vector embeddings with OpenAI for accurate document retrieval
- **Interactive Q&A**: Streamlit-based chat interface for document queries
- **Docker Deployment**: Containerized deployment with multi-stage builds
- **Cloud Ready**: Support for multiple cloud platforms (Render, Railway, Fly.io, Heroku)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Document      │    │   Smart         │    │   Vector        │
│   Extraction    │───▶│   Chunking      │───▶│   Embedding     │
│   (1-extraction)│    │   (2-chunking)  │    │   (3-embedding) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   Semantic      │───▶│   Q&A Response  │
│   Interface     │    │   Search        │    │   Generation    │
│   (5-chat)      │◀───│   (4-search)    │◀───│   (OpenAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
docling/
├── 1-extraction.py          # Document extraction using Docling
├── 2-chunking.py            # Smart document chunking
├── 3-embedding-alternative.py # Vector embedding generation
├── 4-search-alternative.py  # Semantic search functionality
├── 5-chat.py               # Streamlit Q&A interface
├── simple_search.py        # Alternative search implementation
├── requirements.txt        # Python dependencies (including scikit-learn)
├── Dockerfile             # Multi-stage Docker build
├── docker-compose.yml     # Docker Compose configuration
├── deploy.sh              # Deployment automation script
├── .env.example           # Environment variables template
├── .dockerignore          # Docker ignore patterns
├── README.md              # Main documentation
├── README-DOCKER.md       # Docker-specific documentation
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── sitemap.py         # Sitemap URL extraction
│   └── tokenizer.py       # OpenAI tokenizer wrapper
├── data/                  # Processed data storage
├── output/                # Extracted content output
└── PROJECT_DOCUMENTATION.md # This comprehensive guide
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Docker (for containerized deployment)

### Local Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd docling
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

4. **Process a document**:
```bash
# Update source in 1-extraction.py first, then:
python 1-extraction.py    # Extract content
python 2-chunking.py      # Create chunks
python 3-embedding-alternative.py  # Generate embeddings
```

5. **Start the interface**:
```bash
streamlit run 5-chat.py
```

## 🔧 Processing Pipeline

### 1. Document Extraction ([`1-extraction.py`](1-extraction.py:1))

**Purpose**: Extract content from various document formats into structured Markdown.

**Key Components**:
- [`DocumentConverter`](1-extraction.py:1) from Docling library
- Supports local files and URLs
- Outputs to [`output/`](1-extraction.py:10) directory

**Usage**:
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
doc = converter.convert("document.pdf").document
markdown_content = doc.export_to_markdown()
```

### 2. Smart Chunking ([`2-chunking.py`](2-chunking.py:1))

**Purpose**: Break documents into meaningful chunks while preserving structure.

**Key Components**:
- [`HybridChunker`](2-chunking.py:1) with token awareness
- [`OpenAITokenizerWrapper`](2-chunking.py:5) for OpenAI compatibility
- Max tokens: 8191 (text-embedding-3-large limit)

**Features**:
- Hierarchical structure preservation
- Token-aware splitting and merging
- Context preservation for RAG applications

### 3. Vector Embedding ([`3-embedding-alternative.py`](3-embedding-alternative.py:1))

**Purpose**: Generate embeddings for document chunks using OpenAI.

**Key Components**:
- OpenAI [`text-embedding-3-large`](3-embedding-alternative.py:70) model
- Cosine similarity for retrieval
- JSON storage in [`data/embeddings.json`](3-embedding-alternative.py:111)

**Metadata Preserved**:
- Source filename
- Page numbers
- Section titles
- Original document structure

### 4. Semantic Search ([`4-search-alternative.py`](4-search-alternative.py:1))

**Purpose**: Search through embedded documents using semantic similarity.

**Key Components**:
- [`cosine_similarity`](4-search-alternative.py:5) from scikit-learn
- Top-k results retrieval
- Relevance scoring

### 5. Q&A Interface ([`5-chat.py`](5-chat.py:1))

**Purpose**: Interactive document querying with Streamlit.

**Features**:
- File upload and URL input
- Real-time processing status
- Streaming responses
- Source attribution
- Beautiful UI with custom styling

## 🛠️ Utility Modules

### [`utils/tokenizer.py`](utils/tokenizer.py:1) - OpenAITokenizerWrapper

**Purpose**: Bridge between OpenAI's tokenizer and Docling's HybridChunker.

**Key Methods**:
- [`tokenize()`](utils/tokenizer.py:24): Convert text to tokens
- [`_convert_token_to_id()`](utils/tokenizer.py:31): Token to ID mapping
- [`_convert_id_to_token()`](utils/tokenizer.py:34): ID to token mapping

**Usage**:
```python
from utils.tokenizer import OpenAITokenizerWrapper

tokenizer = OpenAITokenizerWrapper()
tokens = tokenizer.tokenize("Your text here")
```

### [`utils/sitemap.py`](utils/sitemap.py:1) - Sitemap URL Extraction

**Purpose**: Extract URLs from website sitemaps for bulk processing.

**Key Methods**:
- [`get_sitemap_urls()`](utils/sitemap.py:8): Fetch and parse sitemap XML
- Namespace-aware XML parsing
- Graceful fallback to base URL

**Usage**:
```python
from utils.sitemap import get_sitemap_urls

urls = get_sitemap_urls("https://example.com")
```

## 🐳 Docker Deployment

### Multi-stage Build ([`Dockerfile`](Dockerfile:1))

**Builder Stage**:
- Installs build dependencies
- Creates virtual environment
- Installs Python packages

**Runtime Stage**:
- Minimal base image
- Only runtime dependencies
- Optimized for size (~500MB)

### Docker Compose ([`docker-compose.yml`](docker-compose.yml:1))

**Features**:
- Volume mounts for data persistence
- Health checks
- Environment variable management
- Easy scaling options

### Deployment Script ([`deploy.sh`](deploy.sh:1))

**Commands**:
```bash
./deploy.sh          # Local deployment
./deploy.sh render   # Render.com instructions
./deploy.sh railway  # Railway instructions
./deploy.sh stop     # Stop application
./deploy.sh logs     # View logs
```

## ⚙️ Configuration

### Environment Variables ([`.env.example`](.env.example:1))

**Required**:
```bash
OPENAI_API_KEY=your_actual_api_key_here
```

**Optional**:
```bash
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_CHAT_MODEL=gpt-4o-mini
MAX_DOCUMENT_SIZE_MB=50
PROCESSING_TIMEOUT_SECONDS=300
```

### Supported Document Formats

| Format | Support | Notes |
|--------|---------|-------|
| PDF | ✅ Full | Layout preservation |
| DOCX | ✅ Full | Microsoft Word |
| XLSX | ✅ Full | Excel spreadsheets |
| PPTX | ✅ Full | PowerPoint |
| Markdown | ✅ Full | Native support |
| HTML | ✅ Full | Web documents |
| Images | ✅ Partial | OCR via EasyOCR |
| XML Formats | ✅ Partial | USPTO, PMC |

## 🚀 Deployment Options

### Local Development
```bash
# Using Python directly
pip install -r requirements.txt
streamlit run 5-chat.py

# Using Docker
docker-compose up -d
```

### Cloud Platforms

**Render.com**:
```bash
./deploy.sh render
```

**Railway**:
```bash
./deploy.sh railway
```

**Fly.io**:
```bash
./deploy.sh flyio
```

**Heroku**:
```bash
./deploy.sh heroku
```

## 🔍 Usage Examples

### Example 1: Process a Local PDF
```bash
# Update source in 1-extraction.py to "document.pdf"
python 1-extraction.py
python 2-chunking.py
python 3-embedding-alternative.py
streamlit run 5-chat.py
```

### Example 2: Process from URL
```bash
# Update source in 1-extraction.py to "https://example.com/doc.pdf"
python 1-extraction.py
# ... rest of pipeline
```

### Example 3: Direct API Usage
```python
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from utils.tokenizer import OpenAITokenizerWrapper

# Extract
converter = DocumentConverter()
doc = converter.convert("document.pdf").document

# Chunk
tokenizer = OpenAITokenizerWrapper()
chunker = HybridChunker(tokenizer=tokenizer, max_tokens=8191)
chunks = list(chunker.chunk(doc))

# Process chunks...
```

## 🐛 Troubleshooting

### Common Issues

**1. OpenAI API Errors**
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API connection
python -c "from openai import OpenAI; client = OpenAI(); print(client.models.list())"
```

**2. Docling Model Loading**
```bash
# Update transformers if needed
pip install --upgrade transformers
```

**3. Memory Issues**
```bash
# Reduce chunk size in 2-chunking.py
MAX_TOKENS = 4096  # Instead of 8191
```

**4. Docker Build Failures**
```bash
# Clear cache and rebuild
docker-compose build --no-cache
```

### Performance Optimization

**For Large Documents**:
- Increase timeout in [`5-chat.py`](5-chat.py:50)
- Use smaller chunk sizes
- Process in batches

**For Production**:
- Add Redis caching
- Implement request queuing
- Use GPU acceleration

## 📊 Monitoring & Logging

### Health Checks
```bash
# Docker health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Application health
curl http://localhost:8501/_stcore/health
```

### Logs
```bash
# Docker logs
docker-compose logs -f

# Streamlit logs
streamlit run 5-chat.py --logger.level=DEBUG
```

## 🔒 Security Considerations

1. **API Keys**: Never commit `.env` files
2. **File Uploads**: Validate file types and sizes
3. **Docker Security**: Use non-root users in production
4. **Network**: Use reverse proxy with SSL
5. **Data**: Encrypt sensitive documents

## 📈 Scaling Strategies

### Horizontal Scaling
- Multiple Streamlit instances behind load balancer
- Shared Redis cache for sessions
- Database for embedding storage

### Vertical Scaling
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '4'
```

### Performance Tips
- Pre-process documents during off-peak hours
- Cache frequently accessed embeddings
- Use CDN for static assets

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Install development dependencies
4. Write tests
5. Submit pull request

### Code Style
- Follow PEP 8 for Python
- Use type hints
- Add docstrings
- Write comprehensive tests

## 📝 License

This project is built on top of Docling, which is licensed under the Apache 2.0 License. Refer to the main [Docling repository](https://github.com/DS4SD/docling) for detailed licensing information.

## 🆘 Support

### Documentation
- [Docling Official Docs](https://ds4sd.github.io/docling/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)

### Issues
- Check existing issues in GitHub
- Provide detailed error messages
- Include environment information

### Community
- Docling GitHub Discussions
- OpenAI Developer Forum
- Streamlit Community

---

*Last Updated: 2025-09-01*  
*Documentation Version: 1.0.0*