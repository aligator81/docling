#!/usr/bin/env python3
"""
Database Content Checker for Neon Database
Run this script to check what's actually stored in your Neon database
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neon database connection
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

if not NEON_CONNECTION_STRING:
    print("❌ NEON_CONNECTION_STRING environment variable is required but not set!")
    print("Please set it in your .env file or environment variables.")
    sys.exit(1)

def get_db_connection():
    """Get connection to Neon database"""
    try:
        conn = psycopg2.connect(NEON_CONNECTION_STRING)
        # Test the connection
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Connection string: {NEON_CONNECTION_STRING[:50]}...")
        return None
    except:
        print("❌ Unexpected error connecting to database")
        return None

def check_database_contents():
    """Check and display all database contents"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        print("🔍 Checking Neon Database Contents...\n")

        with conn.cursor() as cur:
            # Check existing tables
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('documents', 'document_chunks', 'embeddings')
            """)
            existing_tables = [row[0] for row in cur.fetchall()]

            print("📊 DATABASE TABLES:")
            print("=" * 50)

            for table in ['documents', 'document_chunks', 'embeddings']:
                if table in existing_tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    print(f"✅ {table}: {count} records")
                else:
                    print(f"❌ {table}: table does not exist")

            print(f"\n{'='*50}")

            # Documents details
            if 'documents' in existing_tables:
                cur.execute("SELECT COUNT(*) FROM documents")
                doc_count = cur.fetchone()[0]

                if doc_count > 0:
                    print(f"\n📄 DOCUMENTS ({doc_count} total):")
                    print("-" * 30)
                    cur.execute("""
                        SELECT id, filename, file_size, file_type, processed, upload_date
                        FROM documents
                        ORDER BY upload_date DESC
                    """)
                    docs = cur.fetchall()
                    for doc in docs:
                        doc_id, filename, file_size, file_type, processed, upload_date = doc
                        status = "✅ PROCESSED" if processed else "⏳ UNPROCESSED"
                        print(f"[{doc_id}] {filename}")
                        print(f"    Size: {file_size} bytes | Type: {file_type} | Status: {status}")
                        print(f"    Uploaded: {upload_date}")
                        print()

            # Chunks details
            if 'document_chunks' in existing_tables:
                cur.execute("SELECT COUNT(*) FROM document_chunks")
                chunk_count = cur.fetchone()[0]

                if chunk_count > 0:
                    print(f"\n🔪 DOCUMENT CHUNKS ({chunk_count} total):")
                    print("-" * 30)
                    cur.execute("""
                        SELECT dc.id, d.filename, dc.chunk_index, LENGTH(dc.chunk_text) as text_length, dc.token_count
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        ORDER BY dc.created_at DESC
                        LIMIT 10
                    """)
                    chunks = cur.fetchall()
                    for chunk in chunks:
                        chunk_id, filename, chunk_index, text_length, token_count = chunk
                        print(f"[{chunk_id}] {filename} - Chunk {chunk_index}")
                        print(f"    Length: {text_length} chars | Tokens: {token_count}")
                        print(f"    Preview: {chunk[2][:100]}...")
                        print()

            # Embeddings details
            if 'embeddings' in existing_tables:
                cur.execute("SELECT COUNT(*) FROM embeddings")
                embedding_count = cur.fetchone()[0]

                if embedding_count > 0:
                    print(f"\n🧬 EMBEDDINGS ({embedding_count} total):")
                    print("-" * 30)

                    # Group by provider
                    cur.execute("SELECT embedding_provider, COUNT(*) FROM embeddings GROUP BY embedding_provider")
                    provider_counts = cur.fetchall()

                    for provider, count in provider_counts:
                        print(f"📊 {provider}: {count} embeddings")

                    print("\n🔍 Recent embeddings:")
                    cur.execute("""
                        SELECT e.id, d.filename, e.embedding_provider, e.embedding_model, e.created_at
                        FROM embeddings e
                        JOIN document_chunks dc ON e.chunk_id = dc.id
                        JOIN documents d ON dc.document_id = d.id
                        ORDER BY e.created_at DESC
                        LIMIT 5
                    """)
                    embeddings = cur.fetchall()

                    for emb in embeddings:
                        emb_id, filename, provider, model, created_at = emb
                        print(f"[{emb_id}] {filename} - {provider} ({model})")
                        print(f"    Created: {created_at}")
                        print()

            # Summary
            print(f"{'='*50}")
            print("📈 SUMMARY:")
            print(f"• Documents: {doc_count}")
            print(f"• Chunks: {chunk_count}")
            print(f"• Embeddings: {embedding_count}")

            if embedding_count > 0:
                print("\n✅ SUCCESS: Your Neon database contains embeddings!")
                print("🚀 You can now use the chat interface to ask questions about your documents.")
            else:
                print("\n❌ No embeddings found in your Neon database.")
                print("💡 Run the embedding process to create embeddings from your chunks.")

    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 Neon Database Content Checker")
    print("=" * 50)
    check_database_contents()