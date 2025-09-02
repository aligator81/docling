import streamlit as st
import json
import numpy as np
import subprocess
import os
import re
import sys
from openai import OpenAI
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
load_dotenv()

<<<<<<< HEAD
# Add diagnostic logging for debugging
print(f"DEBUG: Current working directory: {os.getcwd()}")
print(f"DEBUG: .env file exists: {os.path.exists('.env')}")
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        env_content = f.read()
    print(f"DEBUG: .env file content length: {len(env_content)}")
    print(f"DEBUG: .env contains OPENAI_API_KEY: {'OPENAI_API_KEY' in env_content}")

# Initialize OpenAI client with explicit API key handling
api_key = os.getenv("OPENAI_API_KEY")
print(f"DEBUG: API key loaded: {api_key is not None}")
print(f"DEBUG: API key length: {len(api_key) if api_key else 0}")
print(f"DEBUG: API key starts with sk-: {api_key.startswith('sk-') if api_key else False}")

if not api_key:
    st.error("❌ OPENAI_API_KEY environment variable is not set. Please configure it in your .env file or environment variables.")
    st.stop()

client = OpenAI(api_key=api_key)
print(f"DEBUG: OpenAI client created successfully")
=======
# Initialize OpenAI client
client = OpenAI()
>>>>>>> 99fe1f9d064d750dec8c5a0cf8de004641d1b0dc


def update_extraction_source(source):
    """Update the source (URL or file path) in 1-extraction.py"""
    try:
        with open("1-extraction.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update the source line (line 5)
        new_content = re.sub(
            r'^source = ".*"',
            f'source = "{source}"',
            content,
            flags=re.MULTILINE
        )
        
        with open("1-extraction.py", "w", encoding="utf-8") as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        st.error(f"Error updating extraction source: {e}")
        return False


def run_extraction():
    """Run the extraction process"""
    try:
        result = subprocess.run(
            [sys.executable, "1-extraction.py"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            # Check for specific docling/huggingface errors
            error_output = result.stderr
            if "init_empty_weights" in error_output:
                error_output += "\n\n⚠️  This appears to be a Hugging Face transformers compatibility issue. Try updating transformers: pip install --upgrade transformers"
            elif "huggingface" in error_output.lower():
                error_output += "\n\n⚠️  Hugging Face model loading issue detected. This may require package updates."
            return False, error_output
    except subprocess.TimeoutExpired:
        return False, "Extraction timed out after 5 minutes. The document may be too large or the server is slow."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def run_chunking():
    """Run the chunking process"""
    try:
        result = subprocess.run(
            [sys.executable, "2-chunking.py"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Chunking timed out after 5 minutes."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def run_embedding():
    """Run the embedding process"""
    try:
        result = subprocess.run(
            [sys.executable, "3-embedding-alternative.py"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Embedding timed out after 5 minutes."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def get_embedding(text):
    """Get embedding for text using OpenAI API"""
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return response.data[0].embedding


def get_context(query: str, num_results: int = 5) -> str:
    """Search the database for relevant context.

    Args:
        query: User's question
        table: LanceDB table object
        num_results: Number of results to return

    Returns:
        str: Concatenated context from relevant chunks with source information
    """
    # Load embeddings from JSON file (alternative approach)
    try:
        with open("data/embeddings.json", "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except FileNotFoundError:
        st.error("Embeddings file not found. Please run the alternative embedding script first.")
        return ""
    
    # Get embedding for query
    query_embedding = get_embedding(query)
    query_embedding = np.array(query_embedding).reshape(1, -1)
    
    # Calculate similarities
    similarities = []
    for chunk in chunks:
        chunk_embedding = np.array(chunk["embedding"]).reshape(1, -1)
        similarity = cosine_similarity(query_embedding, chunk_embedding)[0][0]
        similarities.append((similarity, chunk))
    
    # Sort by similarity and get top results
    similarities.sort(key=lambda x: x[0], reverse=True)
    top_results = similarities[:num_results]
    contexts = []

    for score, result in top_results:
        # Extract metadata
        filename = result.get("filename")
        page_numbers = result.get("page_numbers")
        title = result.get("title")

        # Build source citation
        source_parts = []
        if filename:
            source_parts.append(filename)
        if page_numbers:
            source_parts.append(f"p. {', '.join(str(p) for p in page_numbers)}")

        source = f"\nSource: {' - '.join(source_parts)}"
        if title:
            source += f"\nTitle: {title}"

        contexts.append(f"{result['text']}{source}")

    return "\n\n".join(contexts)


def get_chat_response(messages, context: str) -> str:
    """Get streaming response from OpenAI API.

    Args:
        messages: Chat history
        context: Retrieved context from database

    Returns:
        str: Model's response
    """
    system_prompt = f"""You are a helpful assistant that answers questions based on the provided context.
    Use only the information from the context to answer questions. If you're unsure or the context
<<<<<<< HEAD
    doesn't contain the relevant information, say so. 
=======
    doesn't contain the relevant information, say so. answer only what is asked from the docum and do not provide additional information.    
>>>>>>> 99fe1f9d064d750dec8c5a0cf8de004641d1b0dc
    Context:
    {context}
    """

    messages_with_context = [{"role": "system", "content": system_prompt}, *messages]

    # Create the streaming response
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages_with_context,
        temperature=0.7,
        stream=True,
    )

    # Use Streamlit's built-in streaming capability
    response = st.write_stream(stream)
    return response


# Initialize Streamlit app with custom styling
st.set_page_config(
    page_title="📚 Document Q&A Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
    }
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3498db;
    }
    .upload-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px dashed #dee2e6;
        margin-bottom: 1.5rem;
    }
    .button-primary {
        background: linear-gradient(45deg, #667eea, #764ba2) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }
    .button-secondary {
        background: linear-gradient(45deg, #6c757d, #495057) !important;
        border: none !important;
        color: white !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
    }
    .status-success {
        background: #d4edda !important;
        border-color: #c3e6cb !important;
        color: #155724 !important;
    }
    .status-error {
        background: #f8d7da !important;
        border-color: #f5c6cb !important;
        color: #721c24 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for document processing
with st.sidebar:
    st.markdown('<div class="sidebar-header">📄 Document Processing</div>', unsafe_allow_html=True)
    
    # Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
<<<<<<< HEAD
    st.subheader("📁 Upload Document or Image")
    uploaded_file = st.file_uploader(
        "Drag & drop or click to upload",
        type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "docx", "xlsx"],
        help="Upload PDF, DOCX, XLSX, PNG, JPEG, TIFF, or BMP files for processing",
=======
    st.subheader("📁 Upload PDF")
    uploaded_file = st.file_uploader(
        "Drag & drop or click to upload",
        type=["pdf"],
        help="Upload a PDF document for processing",
>>>>>>> 99fe1f9d064d750dec8c5a0cf8de004641d1b0dc
        label_visibility="collapsed"
    )
    
    st.subheader("🔗 Or enter URL")
    url = st.text_input(
<<<<<<< HEAD
        "Document/Image URL",
        placeholder="https://example.com/document.pdf or https://example.com/image.png",
        help="Enter URL to PDF, DOCX, XLSX, PNG, JPEG, TIFF, or BMP file",
=======
        "Document URL",
        placeholder="https://example.com/document.pdf",
        help="Enter URL to PDF or webpage",
>>>>>>> 99fe1f9d064d750dec8c5a0cf8de004641d1b0dc
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
<<<<<<< HEAD
    # Image processing information
    with st.expander("ℹ️ About Image Processing"):
        st.markdown("""
        **Supported Image Formats:**
        - 📄 **Scanned Documents** - OCR converts to searchable text
        - 📱 **Screenshots** - Extract text content from images
        - 📊 **Charts & Graphs** - Text extraction from labels and annotations
        - 🧪 **Technical Diagrams** - Extract any text elements
        - ✍️ **Handwritten Notes** - OCR can process clear handwriting
        
        **Supported Formats:**
        - 📄 **Documents:** PDF, DOCX (Word), XLSX (Excel)
        - 🖼️ **Images:** PNG, JPEG, TIFF, BMP
        
        **Processing Time:** ~30 seconds per page/image
        
        **Features:**
        - 📄 Scanned Documents → Searchable text via OCR
        - 📱 Screenshots → Text extraction
        - 📊 Charts & Graphs → Label and annotation extraction
        - 🧪 Technical Diagrams → Text element extraction
        - ✍️ Handwritten Notes → Clear handwriting OCR
        - 📝 Word Documents → Full text extraction
        - 📊 Excel Spreadsheets → Data and text extraction
        """)
    
=======
>>>>>>> 99fe1f9d064d750dec8c5a0cf8de004641d1b0dc
    # Processing buttons
    col1, col2 = st.columns(2)
    
    with col1:
        extract_btn = st.button("🚀 Extract", use_container_width=True, type="primary")
    
    with col2:
        chunk_btn = st.button("🔪 Chunk", use_container_width=True, type="secondary")
    
    embed_btn = st.button("🧬 Embed", use_container_width=True, type="secondary")
    
    # Process extraction
    if extract_btn:
        if uploaded_file and url:
            st.warning("⚠️ Please use either file upload OR URL, not both.")
        elif uploaded_file or url:
            # Check file size before starting extraction
            if uploaded_file and uploaded_file.size > 50 * 1024 * 1024:
                st.error("❌ File size too large. Maximum size is 50MB.")
            else:
                with st.status("🔄 Processing extraction...", expanded=True) as status:
                    # Handle file upload
                    if uploaded_file:
                        # Save uploaded file temporarily
                        temp_file_path = f"temp_{uploaded_file.name}"
                        with open(temp_file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        source_to_use = temp_file_path
                    else:
                        source_to_use = url
                    
                    # Update the extraction source
                    st.write("📝 Updating extraction script...")
                    if update_extraction_source(source_to_use):
                        st.write("✅ Extraction script updated")
                        
                        # Run the extraction process
                        st.write("🔍 Extracting document content...")
                        success, output = run_extraction()
                        
                        # Clean up temporary file if uploaded
                        if uploaded_file and os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                        
                        if success:
                            st.write("✅ Extraction completed successfully!")
                            st.code(output, language="text")
                            status.update(label="✅ Extraction Complete!", state="complete")
                            st.balloons()
                            st.success("Document ready for questions! 🎉")
                        else:
                            st.error("❌ Extraction failed")
                            st.code(output, language="text")
                            status.update(label="❌ Extraction Failed", state="error")
                    else:
                        st.error("Failed to update extraction script")
                        status.update(label="❌ Update Failed", state="error")
        else:
<<<<<<< HEAD
            st.warning("📝 Please upload a document/image file or enter a URL first")
=======
            st.warning("📝 Please upload a PDF file or enter a URL first")
>>>>>>> 99fe1f9d064d750dec8c5a0cf8de004641d1b0dc
    
    # Process chunking
    if chunk_btn:
        with st.status("🔄 Processing chunking...", expanded=True) as status:
            st.write("🔪 Chunking document content...")
            success, output = run_chunking()
            
            if success:
                st.write("✅ Chunking completed successfully!")
                st.code(output, language="text")
                status.update(label="✅ Chunking Complete!", state="complete")
                st.success("Document chunked successfully! 🎯")
            else:
                st.error("❌ Chunking failed")
                st.code(output, language="text")
                status.update(label="❌ Chunking Failed", state="error")
    
    # Process embedding
    if embed_btn:
        with st.status("🔄 Processing embedding...", expanded=True) as status:
            st.write("🧬 Creating embeddings...")
            success, output = run_embedding()
            
            if success:
                st.write("✅ Embedding completed successfully!")
                st.code(output, language="text")
                status.update(label="✅ Embedding Complete!", state="complete")
                st.success("Embeddings created successfully! 🎯")
            else:
                st.error("❌ Embedding failed")
                st.code(output, language="text")
                status.update(label="❌ Embedding Failed", state="error")

# Main content area for chat
<<<<<<< HEAD
st.markdown('<div class="main-header">📚 Document & Image Q&A Assistant</div>', unsafe_allow_html=True)
=======
st.markdown('<div class="main-header">📚 Document Q&A Assistant</div>', unsafe_allow_html=True)
>>>>>>> 99fe1f9d064d750dec8c5a0cf8de004641d1b0dc

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages in centered container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
<<<<<<< HEAD
if prompt := st.chat_input("💬 Ask a question about the document or image..."):
=======
if prompt := st.chat_input("💬 Ask a question about the document..."):
>>>>>>> 99fe1f9d064d750dec8c5a0cf8de004641d1b0dc
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get relevant context
    with st.status("🔍 Searching document...", expanded=False) as status:
        context = get_context(prompt)
        st.markdown(
            """
            <style>
            .search-result {
                margin: 10px 0;
                padding: 15px;
                border-radius: 8px;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-left: 4px solid #3498db;
            }
            .search-result summary {
                cursor: pointer;
                color: #2c3e50;
                font-weight: 600;
                font-size: 1.1em;
            }
            .search-result summary:hover {
                color: #1a73e8;
            }
            .metadata {
                font-size: 0.9em;
                color: #6c757d;
                font-style: italic;
                margin-bottom: 8px;
            }
            </style>
        """,
            unsafe_allow_html=True,
        )

        st.write("📋 Found relevant sections:")
        for chunk in context.split("\n\n"):
            # Split into text and metadata parts
            parts = chunk.split("\n")
            text = parts[0]
            metadata = {
                line.split(": ")[0]: line.split(": ")[1]
                for line in parts[1:]
                if ": " in line
            }

            source = metadata.get("Source", "Unknown source")
            title = metadata.get("Title", "Untitled section")

            st.markdown(
                f"""
                <div class="search-result">
                    <details>
                        <summary>{source}</summary>
                        <div class="metadata">📖 Section: {title}</div>
                        <div style="margin-top: 12px; line-height: 1.6;">{text}</div>
                    </details>
                </div>
            """,
                unsafe_allow_html=True,
            )

    # Display assistant response first
    with st.chat_message("assistant"):
        # Get model response with streaming
        response = get_chat_response(st.session_state.messages, context)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown('</div>', unsafe_allow_html=True)
