from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from openai import OpenAI
from utils.tokenizer import OpenAITokenizerWrapper

load_dotenv()

# Initialize OpenAI client (make sure you have OPENAI_API_KEY in your environment variables)
client = OpenAI()


tokenizer = OpenAITokenizerWrapper()  # Load our custom tokenizer for OpenAI
MAX_TOKENS = 8191  # text-embedding-3-large's maximum context length


# --------------------------------------------------------------
# Read from extraction files in output directory
# --------------------------------------------------------------

import glob
import os

# Find all extraction files in the output directory
extraction_files = glob.glob("output/*_extracted.md")

if not extraction_files:
    raise FileNotFoundError("No extraction files found in output directory. Run 1-extraction.py first.")

print(f"Found {len(extraction_files)} extraction file(s)")

# Process the first extraction file found
extraction_file = extraction_files[0]
print(f"Processing extraction file: {extraction_file}")

# Use the DocumentConverter to process the markdown file
converter = DocumentConverter()
result = converter.convert(extraction_file)


# --------------------------------------------------------------
# Apply hybrid chunking
# --------------------------------------------------------------

chunker = HybridChunker(
    tokenizer=tokenizer,
    max_tokens=MAX_TOKENS,
    merge_peers=True,
)

chunk_iter = chunker.chunk(dl_doc=result.document)
chunks = list(chunk_iter)

print(f"Number of chunks created: {len(chunks)}")
print("\nChunks:")
for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i+1} ---")
    print(chunk.text)
