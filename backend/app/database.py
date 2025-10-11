from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv("NEON_CONNECTION_STRING")

if not DATABASE_URL:
    raise ValueError("NEON_CONNECTION_STRING environment variable is required!")

# Enhanced engine configuration with optimized settings for Neon PostgreSQL
engine = create_engine(
    DATABASE_URL,
    # Enhanced connection pool settings for better performance and stability
    poolclass=QueuePool,
    pool_pre_ping=True,      # Verify connections before reuse
    pool_recycle=3600,       # Recycle connections after 1 hour (prevents stale connections)
    pool_timeout=30,         # Connection timeout (seconds)
    pool_size=10,           # Base pool size (increased from 5)
    max_overflow=20,        # Additional connections beyond pool_size (increased from 10)
    pool_reset_on_return='commit',  # Reset connections on return

    # SSL and connection settings optimized for Neon
    connect_args={
        "connect_timeout": 15,           # Increased timeout for stability
        "application_name": "DoclingApp",
        "sslmode": "require",           # Ensure SSL is required for security
    },

    # Query execution settings
    echo=False,             # Set to True for SQL debugging in development
    future=True,
    # Performance optimizations
    execution_options={
        "autocommit": False,
        "autoflush": False,
    },
)

# Enhanced session configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent expired object issues
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()