from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from openai import OpenAI
from utils.tokenizer import OpenAITokenizerWrapper
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

# Initialize OpenAI client
client = OpenAI()

tokenizer = OpenAITokenizerWrapper()
MAX_TOKENS = 8191

# Extract and chunk the document
converter = DocumentConverter()
result = converter.convert("test_document.md")

chunker = HybridChunker(
    tokenizer=tokenizer,
    max_tokens=MAX_TOKENS,
    merge_peers=True,
)

chunk_iter = chunker.chunk(dl_doc=result.document)
chunks = list(chunk_iter)

print(f"Number of chunks created: {len(chunks)}")

# Create embeddings for each chunk using OpenAI
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# Create embeddings for all chunks
chunk_embeddings = []
for i, chunk in enumerate(chunks):
    print(f"Creating embedding for chunk {i+1}...")
    embedding = get_embedding(chunk.text)
    chunk_embeddings.append(embedding)

# Simple search function
def search_chunks(query, chunks, embeddings, top_k=3):
    # Get embedding for the query
    query_embedding = get_embedding(query)
    
    # Calculate cosine similarity
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    
    # Get top-k results
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        results.append({
            'chunk': chunks[idx],
            'similarity': similarities[idx],
            'text': chunks[idx].text
        })
    
    return results

# Test the search
query = "What is Docling?"
results = search_chunks(query, chunks, chunk_embeddings)

print(f"\nSearch results for: '{query}'")
print("=" * 50)
for i, result in enumerate(results):
    print(f"\nResult {i+1} (similarity: {result['similarity']:.4f}):")
    print("-" * 30)
    print(result['text'])
    print()