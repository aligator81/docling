
import streamlit as st
import json
import numpy as np
import subprocess
import os
import re
import sys
from openai import OpenAI
from mistralai import Mistral
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
load_dotenv()

# Initialize session state for API keys and settings
if "api_keys_configured" not in st.session_state:
    st.session_state.api_keys_configured = False
if "openai_client" not in st.session_state:
    st.session_state.openai_client = None
if "mistral_client" not in st.session_state:
    st.session_state.mistral_client = None
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = "openai"
if "embedding_provider" not in st.session_state:
    st.session_state.embedding_provider = "openai"

def configure_api_keys():
    """Display API key configuration interface"""
    st.markdown("### 🔑 API Configuration")
    st.markdown("Please configure your API keys to get started:")
    
    # LLM Provider selection
    provider_choice = st.selectbox(
        "Choose your LLM Provider:",
        options=["openai", "mistral"],
        index=0 if st.session_state.llm_provider == "openai" else 1,
        help="Select which LLM provider you want to use for chat responses"
    )
    
    # API Key inputs
    col1, col2 = st.columns(2)
    
    # Embedding provider selection
    st.markdown("#### Embedding Provider")
    embedding_provider = st.selectbox(
        "Choose Embedding Provider:",
        options=["openai", "mistral"],
        index=0,
        help="Select which provider to use for text embeddings"
    )
    
    with col1:
        st.markdown("#### OpenAI Configuration")
        openai_key = st.text_input(
            "OpenAI API Key:",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help=f"Required for chat (if using OpenAI) and embeddings (if using OpenAI for embeddings)",
            placeholder="sk-...",
            disabled=(provider_choice == "mistral" and embedding_provider == "mistral")
        )
        openai_model = st.selectbox(
            "OpenAI Chat Model:",
            options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=0,
            help="Choose your preferred OpenAI model",
            disabled=(provider_choice == "mistral")
        )
    
    with col2:
        st.markdown("#### Mistral Configuration")
        mistral_key = st.text_input(
            "Mistral API Key:",
            type="password",
            value=os.getenv("MISTRAL_API_KEY", ""),
            help="Required for chat (if using Mistral) and embeddings (if using Mistral for embeddings)",
            placeholder="your-mistral-key",
            disabled=(provider_choice == "openai" and embedding_provider == "openai")
        )
        mistral_model = st.selectbox(
            "Mistral Chat Model:",
            options=["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"],
            index=0,
            help="Choose your preferred Mistral model (small recommended for rate limits)",
            disabled=(provider_choice == "openai")
        )
    
    # Configuration notes
    if provider_choice == "mistral":
        st.info("ℹ️ **Note**: Mistral provides both chat and embedding models. You can use Mistral for everything, or optionally keep OpenAI for embeddings.")
    
    # Test and save configuration
    if st.button("🔧 Test & Save Configuration", type="primary"):
        try:
            success = True
            error_messages = []
            
            # Validate OpenAI configuration if needed
            if provider_choice == "openai" or embedding_provider == "openai":
                if not openai_key:
                    error_messages.append("OpenAI API key is required for selected configuration")
                    success = False
                else:
                    try:
                        test_openai_client = OpenAI(api_key=openai_key)
                        # Test with a minimal request
                        test_openai_client.models.list()
                        st.session_state.openai_client = test_openai_client
                        st.session_state.openai_model = openai_model
                    except Exception as e:
                        error_messages.append(f"OpenAI API key validation failed: {str(e)}")
                        success = False
            
            # Validate Mistral configuration if needed
            if provider_choice == "mistral" or embedding_provider == "mistral":
                if not mistral_key:
                    error_messages.append("Mistral API key is required for selected configuration")
                    success = False
                else:
                    try:
                        test_mistral_client = Mistral(api_key=mistral_key)
                        # Test with a minimal request
                        test_mistral_client.models.list()
                        st.session_state.mistral_client = test_mistral_client
                        st.session_state.mistral_model = mistral_model
                    except Exception as e:
                        error_messages.append(f"Mistral API key validation failed: {str(e)}")
                        success = False
            
            if success:
                st.session_state.llm_provider = provider_choice
                st.session_state.embedding_provider = embedding_provider
                st.session_state.api_keys_configured = True
                st.success("✅ Configuration successful! You can now use the application.")
                st.rerun()
            else:
                for msg in error_messages:
                    st.error(f"❌ {msg}")
                    
        except Exception as e:
            st.error(f"❌ Configuration failed: {str(e)}")

if not st.session_state.api_keys_configured:
    st.set_page_config(
        page_title="🔑 API Configuration",
        page_icon="🔑",
        layout="wide"
    )
    
    st.title("🔑 LLM API Configuration")
    st.markdown("Welcome! Please configure your API keys to get started with the Document Q&A Assistant.")
    
    configure_api_keys()
    st.stop()

# Get the configured clients and settings
openai_client = st.session_state.openai_client
mistral_client = st.session_state.mistral_client
llm_provider = st.session_state.llm_provider
embedding_provider = st.session_state.get("embedding_provider", "openai")


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
        # Build command with API keys from session state
        cmd = [sys.executable, "3-embedding-alternative.py"]
        
        # Add embedding provider argument
        embedding_provider = st.session_state.get("embedding_provider", "openai")
        cmd.extend(["--embedding-provider", embedding_provider])
        
        # Add API key arguments based on provider
        if embedding_provider == "openai":
            if st.session_state.openai_client:
                # Extract API key from the client
                api_key = st.session_state.openai_client.api_key
                cmd.extend(["--openai-api-key", api_key])
        elif embedding_provider == "mistral":
            if st.session_state.mistral_client:
                # Extract API key from the client (Mistral stores it in sdk_configuration.security.api_key)
                api_key = st.session_state.mistral_client.sdk_configuration.security.api_key
                cmd.extend(["--mistral-api-key", api_key])
        
        result = subprocess.run(
            cmd,
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
    """Get embedding for text using the configured embedding provider"""
    embedding_provider = st.session_state.get("embedding_provider", "openai")
    
    if embedding_provider == "openai":
        response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    elif embedding_provider == "mistral":
        response = mistral_client.embeddings.create(
            model="mistral-embed",
            inputs=[text]
        )
        return response.data[0].embedding
    else:
        raise ValueError(f"Unsupported embedding provider: {embedding_provider}")


def get_context(query: str, num_results: int = 5) -> str:
    """Search the database for relevant context.

    Args:
        query: User's question
        table: LanceDB table object
        num_results: Number of results to return

    Returns:
        str: Concatenated context from relevant chunks with source information
    """
    # Load embeddings from provider-specific JSON file
    current_embedding_provider = st.session_state.get("embedding_provider", "openai")
    embedding_filename = f"data/{current_embedding_provider}_embeddings.json"
    
    try:
        with open(embedding_filename, "r", encoding="utf-8") as f:
            embeddings_data = json.load(f)
        
        # Check if it's the new format with metadata
        original_provider = None
        if isinstance(embeddings_data, dict) and "chunks" in embeddings_data:
            stored_embedding_provider = embeddings_data.get("embedding_provider")
            chunks = embeddings_data["chunks"]
            
            # Check for provider mismatch (shouldn't happen with provider-specific files, but good to check)
            if stored_embedding_provider and stored_embedding_provider != current_embedding_provider:
                st.error(f"❌ Embedding provider mismatch! File contains {stored_embedding_provider.upper()} embeddings, but current setting is {current_embedding_provider.upper()}.")
                st.error(f"Please switch to {stored_embedding_provider.upper()} provider or regenerate embeddings with {current_embedding_provider.upper()}.")
                st.info("Click the '🧬 Embed' button to regenerate embeddings with the current provider.")
                return ""
        else:
            # Old format without metadata - use as chunks directly
            chunks = embeddings_data
            
    except FileNotFoundError:
        st.error(f"Embeddings file not found for {current_embedding_provider.upper()} provider.")
        st.error(f"Please run the embedding process with {current_embedding_provider.upper()} provider first.")
        st.info("Click the '🧬 Embed' button to create embeddings with the current provider.")
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
    """Get streaming response from the selected LLM API.

    Args:
        messages: Chat history
        context: Retrieved context from database

    Returns:
        str: Model's response
    """
    system_prompt = f"""You are a helpful assistant that answers questions based on the provided context.
    Use only the information from the context to answer questions. If you're unsure or the context
    doesn't contain the relevant information, say so.
    Context:
    {context}
    """

    messages_with_context = [{"role": "system", "content": system_prompt}, *messages]

    if llm_provider == "openai":
        # Create the streaming response with OpenAI
        stream = openai_client.chat.completions.create(
            model=st.session_state.get("openai_model", "gpt-4o-mini"),
            messages=messages_with_context,
            temperature=0.7,
            stream=True,
        )
        response = st.write_stream(stream)
        return response
    
    elif llm_provider == "mistral":
        # Create the streaming response with Mistral
        stream = mistral_client.chat.stream(
            model=st.session_state.get("mistral_model", "mistral-large-latest"),
            messages=messages_with_context,
            temperature=0.7,
        )
        
        # Create a generator that extracts content from Mistral's streaming format
        def mistral_stream_generator():
            for chunk in stream:
                if hasattr(chunk, 'data') and hasattr(chunk.data, 'choices'):
                    if chunk.data.choices and chunk.data.choices[0].delta.content:
                        yield chunk.data.choices[0].delta.content
                elif hasattr(chunk, 'choices'):
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        
        response = st.write_stream(mistral_stream_generator())
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
    
    # Display current LLM and embedding providers
    if llm_provider == "openai":
        openai_model = st.session_state.get("openai_model", "gpt-4o-mini")
        st.info(f"💬 Chat: OpenAI ({openai_model})")
    elif llm_provider == "mistral":
        mistral_model = st.session_state.get("mistral_model", "mistral-large-latest")
        st.info(f"💬 Chat: Mistral ({mistral_model})")
    
    # Display embedding provider
    if embedding_provider == "openai":
        st.info(f"🧬 Embeddings: OpenAI (text-embedding-3-large)")
    elif embedding_provider == "mistral":
        st.info(f"🧬 Embeddings: Mistral (mistral-embed)")
    
    # Add settings button to reconfigure
    if st.button("⚙️ Change LLM Provider", use_container_width=True):
        # Clear all configuration
        st.session_state.api_keys_configured = False
        st.session_state.openai_client = None
        st.session_state.mistral_client = None
        st.session_state.embedding_provider = "openai"
        st.session_state.messages = []  # Clear chat history
        st.rerun()
    
    st.markdown("---")
    
    # Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📁 Upload Document")
    uploaded_file = st.file_uploader(
        "Drag & drop or click to upload",
        type=["pdf", "docx", "xlsx", "pptx", "md", "html", "htm", "xhtml", "png", "jpg", "jpeg", "tiff", "bmp"],
        help="Upload a document for processing (PDF, DOCX, XLSX, PPTX, Markdown, HTML, Images)",
        label_visibility="collapsed"
    )
    
    st.subheader("🔗 Or enter URL")
    url = st.text_input(
        "Document URL",
        placeholder="https://example.com/document.pdf",
        help="Enter URL to document or webpage (PDF, DOCX, HTML, etc.)",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
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
            st.warning("📝 Please upload a document file or enter a URL first")
    
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
st.markdown('<div class="main-header">📚 Document Q&A Assistant</div>', unsafe_allow_html=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages in centered container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("💬 Ask a question about the document..."):
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
