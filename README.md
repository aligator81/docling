# 📚 Document Q&A Assistant

A Streamlit-based application for document processing, embedding, and intelligent Q&A using LLMs.

## 🚀 Coolify Deployment Guide

### Prerequisites
- A VPS/Server (Ubuntu 20.04+ or Debian 11+)
- Minimum 2GB RAM, 2 vCPUs, 20GB SSD
- Git repository (GitHub, GitLab, or Bitbucket)

### Quick Deployment Steps

#### 1. Prepare Your Repository
```bash
# Add all files to git
git add .
git commit -m "Add Coolify deployment configuration"
git push origin main
```

#### 2. Set Up Coolify Server
1. **Provision a server** (DigitalOcean, Vultr, AWS, etc.)
2. **Install Coolify**:
   ```bash
   curl -fsSL https://get.coolify.io | bash
   ```
3. **Access Coolify dashboard** at `http://your-server-ip:3000`

#### 3. Configure Deployment in Coolify

1. **Add Project** → Select your Git provider
2. **Configure Application**:
   - **Build Method**: Dockerfile
   - **Build Path**: `/` (root)
   - **Port**: 8501
   - **Branch**: main

3. **Set Environment Variables**:
   ```
   OPENAI_API_KEY=your_openai_key_here
   MISTRAL_API_KEY=your_mistral_key_here
   EMBEDDING_PROVIDER=openai
   NEON_CONNECTION_STRING=your_neon_connection_string
   ```

4. **Deploy** → Monitor build logs

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for chat/embeddings | Yes |
| `MISTRAL_API_KEY` | Mistral API key for chat/embeddings | Yes |
| `EMBEDDING_PROVIDER` | Default embedding provider (`openai`/`mistral`) | No |
| `NEON_CONNECTION_STRING` | Neon database connection string | Yes |

### Application Features

- **Document Upload**: PDF, DOCX, XLSX, PPTX, images, HTML
- **Text Extraction**: Local (Docling) or Cloud (Mistral OCR)
- **Chunking**: Intelligent text segmentation
- **Embedding**: OpenAI or Mistral embeddings
- **Semantic Search**: Vector similarity search
- **Q&A Chat**: Context-aware responses

### File Structure
```
.
├── 5-chat.py              # Main Streamlit application
├── 1-extraction.py        # Document extraction
├── 2-chunking-neon.py     # Text chunking
├── 3-embedding-neon.py    # Embedding generation
├── Dockerfile             # Container configuration
├── coolify.yml            # Coolify deployment config
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Health Check
The application includes health checks at `/_stcore/health` for monitoring.

### Troubleshooting

#### Common Issues
1. **Build Fails**: Check Dockerfile syntax and requirements.txt
2. **Application Crashes**: Verify environment variables and database connection
3. **Memory Issues**: Increase memory allocation in Coolify (1GB minimum)

#### Logs
- Check Coolify deployment logs for build issues
- Application logs available in Coolify dashboard
- Database connection logs in Neon dashboard

### Support
For deployment issues, check:
- Coolify documentation: https://coolify.io/docs
- Streamlit deployment guide
- Neon database connection troubleshooting

---
**Ready to deploy?** Follow the steps above and your Document Q&A Assistant will be live! 🎉