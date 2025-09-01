import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

# Initialize OpenAI client
client = OpenAI()

def get_embedding(text):
    """Get embedding for text using OpenAI API"""
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return response.data[0].embedding

def search_embeddings(query, top_k=3):
    """Search through stored embeddings for similar content"""
    # Load embeddings from JSON file
    try:
        with open("data/embeddings.json", "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except FileNotFoundError:
        print("Error: embeddings.json not found. Please run 3-embedding-alternative.py first.")
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