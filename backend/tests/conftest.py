import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..app.database import Base, get_db
from ..app.main import app
from ..app.models import User, Document, DocumentChunk, Embedding

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    """Create test client"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="user",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def admin_user(test_db):
    """Create a test admin user"""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash="hashed_password",
        role="admin",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_document(test_db, test_user):
    """Create a test document"""
    document = Document(
        filename="test.pdf",
        original_filename="test.pdf",
        file_path="data/uploads/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        user_id=test_user.id,
        status="not processed"
    )
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    return document

@pytest.fixture
def test_chunks(test_db, test_document):
    """Create test document chunks"""
    chunks = []
    for i in range(3):
        chunk = DocumentChunk(
            document_id=test_document.id,
            chunk_text=f"Test chunk content {i}",
            chunk_index=i
        )
        test_db.add(chunk)
        chunks.append(chunk)

    test_db.commit()
    for chunk in chunks:
        test_db.refresh(chunk)
    return chunks

@pytest.fixture
def test_embeddings(test_db, test_chunks):
    """Create test embeddings"""
    embeddings = []
    for chunk in test_chunks:
        embedding = Embedding(
            chunk_id=chunk.id,
            filename="test.pdf",
            embedding_vector="[0.1, 0.2, 0.3]",
            embedding_provider="openai",
            embedding_model="text-embedding-ada-002"
        )
        test_db.add(embedding)
        embeddings.append(embedding)

    test_db.commit()
    for embedding in embeddings:
        test_db.refresh(embedding)
    return embeddings