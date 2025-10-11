#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("NEON_CONNECTION_STRING")

if not DATABASE_URL:
    print("Error: NEON_CONNECTION_STRING not found in environment variables")
    sys.exit(1)

try:
    # Create engine
    engine = create_engine(DATABASE_URL)

    # Test connection
    with engine.connect() as conn:
        print("OK: Database connection successful")

        # Get table names
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        print(f"OK: Found tables: {table_names}")

        # Check each table structure
        for table_name in table_names:
            print(f"\n--- {table_name.upper()} ---")
            columns = inspector.get_columns(table_name)
            for column in columns:
                pk_indicator = '(PK)' if column.get('primary_key', False) else ''
                print(f"  {column['name']}: {column['type']} {pk_indicator}")

        # Test a simple query
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        print(f"\nOK: Users table has {user_count} records")

        # Check if all required tables exist
        required_tables = ['users', 'documents', 'document_chunks', 'embeddings', 'api_sessions', 'chat_history']
        missing_tables = [table for table in required_tables if table not in table_names]

        if missing_tables:
            print(f"WARNING: Missing tables: {missing_tables}")
        else:
            print("OK: All required tables exist")

except Exception as e:
    print(f"ERROR: Database error: {e}")
    sys.exit(1)