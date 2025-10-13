from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import numpy as np
from datetime import datetime

from ..database import get_db
from ..models import User, Document, DocumentChunk, Embedding, ChatHistory
from ..schemas import ChatMessage, ChatResponse
from ..auth import get_current_active_user
from ..config import settings

# Import existing chat logic
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
@router.post("/chat/", response_model=ChatResponse)
@router.post("", response_model=ChatResponse)  # Handle empty path as well
async def chat_with_documents(
    message: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Chat with documents using embeddings and LLM"""

    # Handle case where message is received as string (JSON parsing issue)
    if isinstance(message, str):
        try:
            import json
            message_dict = json.loads(message)
            # Create a ChatMessage object from the dict
            message = ChatMessage(**message_dict)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"ERROR: Failed to parse message as JSON: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message format"
            )

    # Check if API keys are configured
    openai_key = os.getenv("OPENAI_API_KEY")
    mistral_key = os.getenv("MISTRAL_API_KEY")

    print(f"🔑 API Key Check - OpenAI: {'✅' if openai_key else '❌'}, Mistral: {'✅' if mistral_key else '❌'}")

    if not openai_key and not mistral_key:
        print("❌ No LLM API keys configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM API keys not configured. Please configure OpenAI or Mistral API keys."
        )

    # Determine LLM provider
    if openai_key:
        llm_provider = "openai"
        model_name = "gpt-4o-mini"
        print(f"🤖 Using OpenAI provider with model: {model_name}")
    elif mistral_key:
        llm_provider = "mistral"
        model_name = "mistral-large-latest"
        print(f"🤖 Using Mistral provider with model: {model_name}")
    else:
        print("❌ No LLM provider available despite API key check")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM provider available"
        )

    # Validate document_ids if provided
    if message.document_ids:
        # Ensure document_ids is a list
        if isinstance(message.document_ids, str):
            try:
                import json
                document_ids_list = json.loads(message.document_ids)
            except (json.JSONDecodeError, ValueError):
                document_ids_list = []
        else:
            document_ids_list = message.document_ids

        for doc_id in document_ids_list:
            # Admin and super_admin users can access any document
            if current_user.role in ["admin", "super_admin"]:
                document = db.query(Document).filter(Document.id == doc_id).first()
            else:
                document = db.query(Document).filter(
                    Document.id == doc_id,
                    Document.user_id == current_user.id
                ).first()

            if not document:
                print(f"DEBUG: Document with ID {doc_id} not found for user {current_user.id} (role: {current_user.role})")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document with ID {doc_id} not found or you don't have access to it. Please refresh the page and select available documents."
                )

            # Check if document is fully processed
            if document.status != "processed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document '{document.original_filename}' (ID: {doc_id}) is not fully processed yet. Current status: {document.status}. Please wait for processing to complete."
                )

    # Get relevant context using embeddings
    if message.document_ids:
        if isinstance(message.document_ids, str):
            try:
                import json
                document_ids_list = json.loads(message.document_ids)
            except (json.JSONDecodeError, ValueError):
                document_ids_list = []
        else:
            document_ids_list = message.document_ids
        # Admin and super_admin users can search all documents, regular users only their own
        user_id_filter = None if current_user.role in ["admin", "super_admin"] else current_user.id
        context, references = await get_context_from_db(message.message, db, document_ids_list, user_id_filter)
    else:
        # When no specific documents selected, search only current user's documents (admin/super_admin can search all)
        user_id_filter = None if current_user.role in ["admin", "super_admin"] else current_user.id
        if user_id_filter:
            # Regular users only search their own documents
            user_document_ids = [doc.id for doc in db.query(Document.id).filter(Document.user_id == current_user.id).all()]
            context, references = await get_context_from_db(message.message, db, user_document_ids, current_user.id)
        else:
            # Admin users can search all documents
            context, references = await get_context_from_db(message.message, db, None, None)

    if not context:
        # No relevant context found
        response_text = "I couldn't find any relevant information in your documents to answer this question. Please try asking a different question or ensure your documents have been properly processed."
        model_used = model_name

        # Save chat history
        chat_record = ChatHistory(
            user_id=current_user.id,
            message=message.message,
            response=response_text,
            context_docs="[]",
            model_used=model_used
        )
        db.add(chat_record)
        db.commit()

        return ChatResponse(
            response=response_text,
            context_docs=[],
            model_used=model_used
        )

    # Generate response using LLM
    response_text = await generate_llm_response(
        message.message,
        context,
        references,
        llm_provider,
        model_name,
        message.document_ids
    )

    # Extract context document IDs for response
    context_doc_ids = [ref.get("id", 0) for ref in references] if references else []

    # Save chat history
    chat_record = ChatHistory(
        user_id=current_user.id,
        message=message.message,
        response=response_text,
        context_docs=str(context_doc_ids),
        model_used=model_name
    )
    db.add(chat_record)
    db.commit()

    return ChatResponse(
        response=response_text,
        context_docs=context_doc_ids,
        model_used=model_name
    )

@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's chat history"""
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).order_by(ChatHistory.created_at.desc()).limit(limit).all()

    return [
        {
            "id": record.id,
            "message": record.message,
            "response": record.response,
            "context_docs": record.context_docs,
            "model_used": record.model_used,
            "created_at": record.created_at
        }
        for record in history
    ]

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    try:
        a_array = np.array(a)
        b_array = np.array(b)

        # Calculate dot product
        dot_product = np.dot(a_array, b_array)

        # Calculate magnitudes
        norm_a = np.linalg.norm(a_array)
        norm_b = np.linalg.norm(b_array)

        # Avoid division by zero
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))
    except Exception as e:
        print(f"Error calculating cosine similarity: {e}")
        return 0.0

async def get_context_from_db(query: str, db: Session, document_ids: Optional[List[int]] = None, user_id: Optional[int] = None) -> tuple[str, list]:
    """Get relevant context from database using embeddings"""
    try:
        # Get embedding for query
        query_embedding = await get_embedding(query)
        if not query_embedding:
            return "", []

        # Build base query
        query_base = db.query(
            DocumentChunk.id,
            DocumentChunk.chunk_text,
            Document.filename
        ).join(
            Embedding, DocumentChunk.id == Embedding.chunk_id
        ).join(
            Document, DocumentChunk.document_id == Document.id
        ).filter(
            Embedding.embedding_vector.isnot(None)
        )

        # Apply user filtering for non-admin users
        if user_id:
            query_base = query_base.filter(Document.user_id == user_id)

        # If document_ids is specified, filter to only those documents
        if document_ids:
            query_base = query_base.filter(Document.id.in_(document_ids))

        # Get all chunks with embeddings for similarity calculation
        all_chunks = query_base.all()

        if not all_chunks:
            return "", []

        # Calculate similarity scores for all chunks
        similarities = []
        for chunk_id, chunk_text, filename in all_chunks:
            # Get the embedding vector for this chunk
            embedding_result = db.query(Embedding).filter(Embedding.chunk_id == chunk_id).first()
            if embedding_result and embedding_result.embedding_vector:
                try:
                    # Convert JSON string to list of floats if needed
                    if isinstance(embedding_result.embedding_vector, str):
                        import json
                        embedding_vector = json.loads(embedding_result.embedding_vector)
                    else:
                        embedding_vector = embedding_result.embedding_vector

                    # Ensure it's a list of floats
                    if embedding_vector and isinstance(embedding_vector, list):
                        embedding_vector = [float(x) for x in embedding_vector]
                        # Calculate cosine similarity
                        similarity = cosine_similarity(query_embedding, embedding_vector)
                        similarities.append((chunk_id, chunk_text, filename, similarity))
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    print(f"Error processing embedding vector for chunk {chunk_id}: {e}")
                    continue

        # Sort by similarity score (highest first) and take top 5
        similarities.sort(key=lambda x: x[3], reverse=True)
        results = similarities[:5]

        if not results:
            return "", []

        # Build context and references
        context_parts = []
        references = []

        for i, (chunk_id, chunk_text, filename, similarity) in enumerate(results, 1):
            # Add to context
            context_parts.append(f"Document: {filename}")
            context_parts.append(f"Content: {chunk_text}")
            context_parts.append("---")

            # Add to references
            references.append({
                "id": chunk_id,
                "filename": filename,
                "page_numbers": "N/A",
                "title": "",
                "similarity": similarity
            })

        context = "\n".join(context_parts)
        return context, references

    except Exception as e:
        print(f"Error getting context: {e}")
        return "", []

async def get_embedding(text: str) -> Optional[List[float]]:
    """Get embedding for text using configured provider"""
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        mistral_key = os.getenv("MISTRAL_API_KEY")

        if openai_key:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding

        elif mistral_key:
            from mistralai import Mistral
            client = Mistral(api_key=mistral_key)
            response = client.embeddings.create(
                model="mistral-embed",
                inputs=[text]
            )
            return response.data[0].embedding

        return None

    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

async def generate_llm_response(
    message: str,
    context: str,
    references: list,
    provider: str,
    model: str,
    document_ids: Optional[List[int]] = None
) -> str:
    """Generate response using LLM"""
    try:
        # Format references for the prompt
        references_text = ""
        if references:
            references_text = "\n\nSource References:\n"
            for ref in references:
                ref_line = f"• {ref['filename']}"
                if ref['page_numbers'] != "N/A":
                    ref_line += f" (Page(s): {ref['page_numbers']})"
                if ref['title']:
                    ref_line += f" - {ref['title']}"
                references_text += ref_line + "\n"

        # Create system prompt
        selected_docs_text = ""
        if document_ids:
            # Ensure document_ids is a list
            if isinstance(document_ids, str):
                try:
                    import json
                    document_ids_list = json.loads(document_ids)
                except (json.JSONDecodeError, ValueError):
                    document_ids_list = []
            else:
                document_ids_list = document_ids

            if document_ids_list and len(document_ids_list) > 1:
                selected_docs_text = f"You are answering questions based on {len(document_ids_list)} selected documents. "

        system_prompt = f"""You are a helpful assistant that answers questions based on the provided document context from selected documents.

        {selected_docs_text}Use ONLY the information from the context to answer questions. Consider information from ALL provided document sources when forming your response.

        Context:
        {context}

        {references_text}

        When answering, please:
        1. Be direct and helpful
        2. Reference specific documents when relevant (mention which document the information comes from)
        3. Synthesize information from multiple documents when possible
        4. If no relevant information is found in any document, clearly state that"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]

        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content

        elif provider == "mistral":
            from mistralai import Mistral
            client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content

        return "Error: No LLM provider available"

    except Exception as e:
        print(f"Error generating response: {e}")
        return f"I encountered an error while processing your question: {str(e)}"