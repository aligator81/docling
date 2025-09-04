import argparse
import json
import numpy as np
import os
from openai import OpenAI
from mistralai import Mistral
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

# Parse command line arguments
parser = argparse.ArgumentParser(description='Search embeddings using provider-specific files')
parser.add_argument('--embedding-provider', type=str, default=None,
                    help='Embedding provider: openai or mistral')
parser.add_argument('--openai-api-key', type=str, default=None,
                    help='OpenAI API key (required if using OpenAI)')
parser.add_argument('--mistral-api-key', type=str, default=None,
                    help='Mistral API key (required if using Mistral)')
args = parser.parse_args()

# Load environment variables as fallback
load_dotenv()

# Determine embedding provider - command line args take precedence
if args.embedding_provider:
    embedding_provider = args.embedding_provider.lower()
else:
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()

# Initialize clients based on provider
openai_client = None
mistral_client = None

if embedding_provider == "openai":
    # Get API key - command line args take precedence over env vars
    api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key is required. Provide it via --openai-api-key argument or OPENAI_API_KEY environment variable.")
        exit(1)
    openai_client = OpenAI(api_key=api_key)
    print("Using OpenAI for embeddings")
elif embedding_provider == "mistral":
    # Get API key - command line args take precedence over env vars
    api_key = args.mistral_api_key or os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("Mistral API key is required. Provide it via --mistral-api-key argument or MISTRAL_API_KEY environment variable.")
        exit(1)
    mistral_client = Mistral(api_key=api_key)
    print("Using Mistral for embeddings")
else:
    print("Invalid EMBEDDING_PROVIDER. Use 'openai' or 'mistral'")
    exit(1)

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

def search_embeddings(query, top_k=3):
    """Search through stored embeddings for similar content"""
    # Load embeddings from provider-specific JSON file
    embedding_filename = f"data/{embedding_provider}_embeddings.json"
    try:
        with open(embedding_filename, "r", encoding="utf-8") as f:
            embeddings_data = json.load(f)
        
        # Check if it's the new format with metadata
        if isinstance(embeddings_data, dict) and "chunks" in embeddings_data:
            stored_embedding_provider = embeddings_data.get("embedding_provider")
            chunks = embeddings_data["chunks"]
            
            # Check for provider mismatch (shouldn't happen with provider-specific files, but good to check)
            if stored_embedding_provider and stored_embedding_provider != embedding_provider:
                print(f"❌ Error: Embeddings file contains {stored_embedding_provider.upper()} embeddings, but current setting is {embedding_provider.upper()}")
                print(f"Please use the correct provider or regenerate embeddings with {embedding_provider.upper()}.")
                return []
        else:
            # Old format without metadata - use as chunks directly
            chunks = embeddings_data
            
    except FileNotFoundError:
        print(f"Error: {embedding_filename} not found. Please run 3-embedding-alternative.py with --embedding-provider {embedding_provider} first.")
        return []
    
    # Get embedding for query
    query_embedding = get_embedding(query)
    query_embedding = np.array(query_embedding).reshape(1, -1)
    
    # Calculate similarities
    similarities = []
    for chunk in chunks:
        chunk_embedding = np.array(chunk["embedding"]).reshape(1, -1)
        similarity = cosine_similarity(query_embedding, chunk_embedding)[0][0]
        similarities.append((similarity, chunk))
    
    # Sort by similarity and return top results
    similarities.sort(key=lambda x: x[0], reverse=True)
    return similarities[:top_k]

# --------------------------------------------------------------
# Search the embeddings
# --------------------------------------------------------------

query = "what's docling?"
results = search_embeddings(query, top_k=3)

print(f"Search results for: '{query}'")
print("=" * 50)

for i, (score, result) in enumerate(results, 1):
    print(f"\nResult {i} (Similarity: {score:.4f}):")
    print(f"Title: {result.get('title', 'No title')}")
    print(f"Filename: {result.get('filename', 'No filename')}")
    print(f"Pages: {result.get('page_numbers', 'No pages')}")
    print(f"Text preview: {result['text'][:200]}...")
    print("-" * 50)