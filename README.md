# Building Knowledge Extraction Pipeline with Docling

[Docling](https://github.com/DS4SD/docling) is a powerful, flexible open source document processing library that converts various document formats into a unified format. It has advanced document understanding capabilities powered by state-of-the-art AI models for layout analysis and table structure recognition.

The whole system runs locally on standard computers and is designed to be extensible - developers can add new models or modify the pipeline for specific needs. It's particularly useful for tasks like enterprise document search, passage retrieval, and knowledge extraction. With its advanced chunking and processing capabilities, it's the perfect tool for providing GenAI applications with knowledge through RAG (Retrieval Augmented Generation) pipelines.

## Key Features

- **Universal Format Support**: Process PDF, DOCX, XLSX, PPTX, Markdown, HTML, images, and more
- **Advanced Understanding**: AI-powered layout analysis and table structure recognition
- **Flexible Output**: Export to HTML, Markdown, JSON, or plain text
- **High Performance**: Efficient processing on local hardware

## Things They're Working on

- Metadata extraction, including title, authors, references & language
- Inclusion of Visual Language Models (SmolDocling)
- Chart understanding (Barchart, Piechart, LinePlot, etc)
- Complex chemistry understanding (Molecular structures)

## Getting Started with the Example

### System Requirements

**Minimum Requirements:**
- **Operating System**: Ubuntu 20.04+ or Debian 11+ (recommended for OVH)
- **CPU**: 4+ cores (8+ recommended for AI model processing)
- **RAM**: 8GB+ (16GB+ recommended for large document processing)
- **Storage**: 20GB+ free space (for models and document storage)
- **Python**: 3.8+ (3.9+ recommended)
- **GPU**: Optional but recommended for faster AI model inference (NVIDIA GPU with CUDA support)

**OVH Server Recommendations:**
- **Instance Type**: B2-15 (4 vCPU, 15GB RAM) or higher
- **Storage**: 50GB+ SSD storage
- **Network**: Public IP with SSH access enabled

### Prerequisites

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables by creating a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
```

### OVH Server Installation

#### Step 1: Provision OVH Server
1. Log in to your OVH Cloud account
2. Create a new public cloud project
3. Deploy an Ubuntu 22.04 instance with:
   - Minimum: 4 vCPU, 8GB RAM, 50GB SSD
   - Recommended: 8 vCPU, 16GB RAM, 100GB SSD
4. Configure SSH key access for secure login
5. Note the public IP address of your instance

#### Step 2: Initial Server Setup
```bash
# Connect to your OVH server
ssh ubuntu@your-server-ip

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential dependencies
sudo apt install -y python3-pip python3-venv git curl wget

# Install system libraries required by Docling
sudo apt install -y libgl1 libglib2.0-0 libsm6 libxrender1 libxext6
```

#### Step 3: Install Application
```bash
# Clone the repository
git clone https://github.com/your-username/docling-knowledge-pipeline.git
cd docling-knowledge-pipeline

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install additional system dependencies for AI models
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### Step 4: Configure Environment
```bash
# Set up environment variables
cp .env.example .env
# Edit .env file with your OpenAI API key and other settings
nano .env

# Create necessary directories
mkdir -p data output
```

#### Step 5: Test Installation
```bash
# Test document extraction
python 1-extraction.py

# Verify all components work
python -c "import docling; print('Docling installed successfully')"
```

#### Step 6: Optional - Set up as Service (Production)
```bash
# Create systemd service for the Streamlit app
sudo nano /etc/systemd/system/docling-streamlit.service

# Add the following content:
[Unit]
Description=Docling Streamlit Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/docling-knowledge-pipeline
Environment=PATH=/home/ubuntu/docling-knowledge-pipeline/venv/bin
ExecStart=/home/ubuntu/docling-knowledge-pipeline/venv/bin/streamlit run 5-chat.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable docling-streamlit.service
sudo systemctl start docling-streamlit.service
```

#### Step 7: Configure Firewall
```bash
# Allow SSH and web traffic
sudo ufw allow 22
sudo ufw allow 8501
sudo ufw enable
```

### Running the Example

Execute the files in order to build and query the document database:

1. Extract document content: `python 1-extraction.py`
2. Create document chunks: `python 2-chunking.py`
3. Create embeddings and store in LanceDB: `python 3-embedding.py`
4. Test basic search functionality: `python 4-search.py`
5. Launch the Streamlit chat interface: `streamlit run 5-chat.py`

Then open your browser and navigate to `http://localhost:8501` to interact with the document Q&A interface.

## Document Processing

### Supported Input Formats

| Format | Description |
|--------|-------------|
| PDF | Native PDF documents with layout preservation |
| DOCX, XLSX, PPTX | Microsoft Office formats (2007+) |
| Markdown | Plain text with markup |
| HTML/XHTML | Web documents |
| Images | PNG, JPEG, TIFF, BMP |
| USPTO XML | Patent documents |
| PMC XML | PubMed Central articles |

Check out this [page](https://ds4sd.github.io/docling/supported_formats/) for an up to date list.

### Processing Pipeline

The standard pipeline includes:

1. Document parsing with format-specific backend
2. Layout analysis using AI models
3. Table structure recognition
4. Metadata extraction
5. Content organization and structuring
6. Export formatting

## Models

Docling leverages two primary specialized AI models for document understanding. At its core, the layout analysis model is built on the `RT-DETR (Real-Time Detection Transformer)` architecture, which excels at detecting and classifying page elements. This model processes pages at 72 dpi resolution and can analyze a single page in under a second on a standard CPU, having been trained on the comprehensive `DocLayNet` dataset.

The second key model is `TableFormer`, a table structure recognition system that can handle complex table layouts including partial borders, empty cells, spanning cells, and hierarchical headers. TableFormer typically processes tables in 2-6 seconds on CPU, making it efficient for practical use. 

For documents requiring text extraction from images, Docling integrates `EasyOCR` as an optional component, which operates at 216 dpi for optimal quality but requires about 30 seconds per page. Both the layout analysis and TableFormer models were developed by IBM Research and are publicly available as pre-trained weights on Hugging Face under "ds4sd/docling-models".

For more detailed information about these models and their implementation, you can refer to the [technical documentation](https://arxiv.org/pdf/2408.09869).

## Chunking

When you're building a RAG (Retrieval Augmented Generation) application, you need to break down documents into smaller, meaningful pieces that can be easily searched and retrieved. But this isn't as simple as just splitting text every X words or characters.

What makes [Docling's chunking](https://ds4sd.github.io/docling/concepts/chunking/) unique is that it understands the actual structure of your document. It has two main approaches:

1. The [Hierarchical Chunker](https://ds4sd.github.io/docling/concepts/chunking/#hierarchical-chunker) is like a smart document analyzer - it knows where the natural "joints" of your document are. Instead of blindly cutting text into fixed-size pieces, it recognizes and preserves important elements like sections, paragraphs, tables, and lists. It maintains the relationship between headers and their content, and keeps related items together (like items in a list).

2. The [Hybrid Chunker](https://ds4sd.github.io/docling/concepts/chunking/#hybrid-chunker) takes this a step further. It starts with the hierarchical chunks but then:
   - It can split chunks that are too large for your embedding model
   - It can stitch together chunks that are too small
   - It works with your specific tokenizer, so the chunks will fit perfectly with your chosen language model

### Why is this great for RAG applications?

Imagine you're building a system to answer questions about technical documents. With basic chunking (like splitting every 500 words), you might cut right through the middle of a table, or separate a header from its content. But Docling's smart chunking:

- Keeps related information together
- Preserves document structure
- Maintains context (like headers and captions)
- Creates chunks that are optimized for your specific embedding model
- Ensures each chunk is meaningful and self-contained

This means when your RAG system retrieves chunks, they'll have the proper context and structure, leading to more accurate and coherent responses from your language model.

## Documentation

For full documentation, visit [documentation site](https://ds4sd.github.io/docling/).

For example notebooks and more detailed guides, check out [GitHub repository](https://github.com/DS4SD/docling).