from typing import List
import json
import os
import glob

from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from openai import OpenAI
from mistralai import Mistral
from utils.tokenizer import OpenAITokenizerWrapper

load_dotenv()

# Check which embedding provider to use
embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()

# Initialize clients based on provider
openai_client = None
mistral_client = None

if embedding_provider == "openai":
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable is not set. Please configure it in your .env file.")
        exit(1)
    openai_client = OpenAI(api_key=api_key)
    print("🤖 Using OpenAI for embeddings")
elif embedding_provider == "mistral":
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ MISTRAL_API_KEY environment variable is not set. Please configure it in your .env file.")
        exit(1)
    mistral_client = Mistral(api_key=api_key)
    print("🤖 Using Mistral for embeddings")
else:
    print("❌ Invalid EMBEDDING_PROVIDER. Use 'openai' or 'mistral'")
    exit(1)

tokenizer = OpenAITokenizerWrapper()  # Load our custom tokenizer for OpenAI
MAX_TOKENS = 8191  # text-embedding-3-large's maximum context length

# Initialize DocumentConverter
converter = DocumentConverter()

# --------------------------------------------------------------
# Read from extraction files in output directory
# --------------------------------------------------------------

# Find all extraction files in the output directory
extraction_files = glob.glob("output/*_extracted.md")

if not extraction_files:
    raise FileNotFoundError("No extraction files found in output directory. Run 1-extraction.py first.")

print(f"Found {len(extraction_files)} extraction file(s)")

# Process all extraction files and collect chunks
all_chunks = []
for extraction_file in extraction_files:
    print(f"Processing extraction file: {extraction_file}")
    
    # Extract filename for metadata
    filename = os.path.basename(extraction_file)
    
    # Use the DocumentConverter to process the markdown file
    result = converter.convert(extraction_file)
    
    # Apply hybrid chunking
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=MAX_TOKENS,
        merge_peers=True,
    )
    
    chunk_iter = chunker.chunk(dl_doc=result.document)
    chunks = list(chunk_iter)
    
    # Store the extraction filename for each chunk by extending the chunks list
    # We'll store it as a tuple (chunk, filename) to preserve the filename info
    for chunk in chunks:
        all_chunks.append((chunk, filename))

print(f"Total chunks from all extraction files: {len(all_chunks)}")

# --------------------------------------------------------------
# Generate embeddings using configured provider
# --------------------------------------------------------------

def get_embedding(text):
    """Get embedding for text using configured provider"""
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

# Process chunks and generate embeddings
processed_chunks = []
for i, (chunk, filename) in enumerate(all_chunks):
    try:
        embedding = get_embedding(chunk.text)
        processed_chunks.append({
            "text": chunk.text,
            "filename": filename,  # Use extraction filename
            "original_filename": chunk.meta.origin.filename if chunk.meta.origin else None,
            "page_numbers": [
                page_no
                for page_no in sorted(
                    set(
                        prov.page_no
                        for item in chunk.meta.doc_items
                        for prov in item.prov
                    )
                )
            ]
            or None,
            "title": chunk.meta.headings[0] if chunk.meta.headings else None,
            "embedding": embedding
        })
        print(f"Processed chunk {i+1}/{len(all_chunks)} using {embedding_provider}")
    except Exception as e:
        print(f"Error processing chunk: {e}")
        continue

# --------------------------------------------------------------
# Save to JSON file instead of LanceDB
# --------------------------------------------------------------

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Save processed chunks to JSON
with open("data/embeddings.json", "w", encoding="utf-8") as f:
    json.dump(processed_chunks, f, indent=2, ensure_ascii=False)

print(f"Successfully processed and saved {len(processed_chunks)} chunks to data/embeddings.json using {embedding_provider}")
print("You can now use 4-search-alternative.py to search through these embeddings")