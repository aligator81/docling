from sqlalchemy import or_, and_, func, desc
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

from ..models import Document, DocumentChunk, Embedding, User

logger = logging.getLogger(__name__)

class AdvancedSearch:
    def __init__(self, db: Session):
        self.db = db

    def search_documents(self, query: str = None, filters: Dict = None, user_id: int = None, user_role: str = "user") -> Dict:
        """Advanced document search with filters and pagination"""
        try:
            # Start with base query
            base_query = self.db.query(Document)

            # Apply user-based filtering
            if user_role != "admin":
                base_query = base_query.filter(Document.user_id == user_id)

            # Apply text search if query provided
            if query and query.strip():
                search_term = f"%{query.strip()}%"
                base_query = base_query.filter(
                    or_(
                        Document.original_filename.ilike(search_term),
                        Document.filename.ilike(search_term),
                        Document.content.ilike(search_term),
                        Document.mime_type.ilike(search_term)
                    )
                )

            # Apply filters
            if filters:
                base_query = self._apply_filters(base_query, filters)

            # Get total count before pagination
            total_count = base_query.count()

            # Apply sorting
            sort_by = filters.get('sort_by', 'created_at') if filters else 'created_at'
            sort_order = filters.get('sort_order', 'desc') if filters else 'desc'

            if sort_by == 'created_at':
                base_query = base_query.order_by(desc(Document.created_at) if sort_order == 'desc' else Document.created_at)
            elif sort_by == 'file_size':
                base_query = base_query.order_by(desc(Document.file_size) if sort_order == 'desc' else Document.file_size)
            elif sort_by == 'filename':
                base_query = base_query.order_by(desc(Document.filename) if sort_order == 'desc' else Document.filename)

            # Apply pagination
            page = int(filters.get('page', 1)) if filters else 1
            per_page = int(filters.get('per_page', 20)) if filters else 20
            offset = (page - 1) * per_page

            documents = base_query.offset(offset).limit(per_page).all()

            return {
                "success": True,
                "documents": documents,
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_count + per_page - 1) // per_page,
                "has_next": offset + per_page < total_count,
                "has_prev": page > 1
            }

        except Exception as e:
            logger.error(f"Error in document search: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "documents": [],
                "total_count": 0
            }

    def _apply_filters(self, query, filters: Dict):
        """Apply various filters to the query"""
        try:
            # Status filter
            if 'status' in filters and filters['status']:
                query = query.filter(Document.status == filters['status'])

            # File type filter
            if 'file_type' in filters and filters['file_type']:
                query = query.filter(Document.mime_type.ilike(f"%{filters['file_type']}%"))

            # Date range filters
            if 'date_from' in filters and filters['date_from']:
                try:
                    date_from = datetime.fromisoformat(filters['date_from'].replace('Z', '+00:00'))
                    query = query.filter(Document.created_at >= date_from)
                except ValueError:
                    logger.warning(f"Invalid date_from format: {filters['date_from']}")

            if 'date_to' in filters and filters['date_to']:
                try:
                    date_to = datetime.fromisoformat(filters['date_to'].replace('Z', '+00:00'))
                    query = query.filter(Document.created_at <= date_to)
                except ValueError:
                    logger.warning(f"Invalid date_to format: {filters['date_to']}")

            # File size filters
            if 'min_size' in filters and filters['min_size']:
                try:
                    min_size = int(filters['min_size'])
                    query = query.filter(Document.file_size >= min_size)
                except ValueError:
                    logger.warning(f"Invalid min_size format: {filters['min_size']}")

            if 'max_size' in filters and filters['max_size']:
                try:
                    max_size = int(filters['max_size'])
                    query = query.filter(Document.file_size <= max_size)
                except ValueError:
                    logger.warning(f"Invalid max_size format: {filters['max_size']}")

            # Content search in chunks (for processed documents)
            if 'content_search' in filters and filters['content_search']:
                content_term = f"%{filters['content_search']}%"
                # Join with chunks table for content search
                query = query.join(DocumentChunk).filter(
                    DocumentChunk.content.ilike(content_term)
                ).distinct()

            return query

        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
            return query

    def search_similar_documents(self, document_id: int, limit: int = 10) -> Dict:
        """Find similar documents using embeddings"""
        try:
            # Get embeddings for the source document
            source_embeddings = self.db.query(Embedding).join(
                DocumentChunk, Embedding.chunk_id == DocumentChunk.id
            ).filter(
                DocumentChunk.document_id == document_id
            ).all()

            if not source_embeddings:
                return {
                    "success": False,
                    "error": "Source document has no embeddings",
                    "similar_documents": []
                }

            # This is a simplified similarity search
            # In a production system, you would use vector similarity (cosine similarity, etc.)
            similar_docs = []

            # For now, return recently processed documents as "similar"
            # TODO: Implement proper vector similarity search
            recent_docs = self.db.query(Document).filter(
                Document.id != document_id,
                Document.status == "embedding"
            ).order_by(desc(Document.processed_at)).limit(limit).all()

            for doc in recent_docs:
                similar_docs.append({
                    "document": doc,
                    "similarity_score": 0.8  # Placeholder score
                })

            return {
                "success": True,
                "similar_documents": similar_docs
            }

        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "similar_documents": []
            }

    def get_search_suggestions(self, query: str, user_id: int, limit: int = 10) -> List[str]:
        """Get search suggestions based on existing document names and content"""
        try:
            suggestions = set()

            if len(query) < 2:
                return list(suggestions)

            search_term = f"%{query}%"

            # Get suggestions from filenames
            filename_results = self.db.query(Document.original_filename).filter(
                Document.original_filename.ilike(search_term),
                Document.user_id == user_id
            ).distinct().limit(limit // 2).all()

            for result in filename_results:
                suggestions.add(result.original_filename)

            # Get suggestions from content (for processed documents)
            content_results = self.db.query(Document.content).filter(
                Document.content.ilike(search_term),
                Document.user_id == user_id,
                Document.content.isnot(None)
            ).distinct().limit(limit // 2).all()

            for result in content_results:
                # Extract meaningful phrases from content
                words = result.content.split()[:5]  # First 5 words
                if words:
                    suggestions.add(" ".join(words) + "...")

            return list(suggestions)[:limit]

        except Exception as e:
            logger.error(f"Error getting search suggestions: {str(e)}")
            return []

    def get_document_statistics(self, user_id: int = None, user_role: str = "user") -> Dict:
        """Get statistics about documents in the system"""
        try:
            base_query = self.db.query(Document)

            if user_role != "admin":
                base_query = base_query.filter(Document.user_id == user_id)

            # Overall statistics
            total_documents = base_query.count()

            # Status breakdown
            status_counts = dict(
                base_query.with_entities(Document.status, func.count(Document.id))
                .group_by(Document.status).all()
            )

            # File type breakdown
            file_types = dict(
                base_query.with_entities(Document.mime_type, func.count(Document.id))
                .group_by(Document.mime_type).limit(10).all()
            )

            # Size statistics
            size_stats = base_query.with_entities(
                func.avg(Document.file_size),
                func.min(Document.file_size),
                func.max(Document.file_size)
            ).first()

            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow().replace(day=1)
            recent_docs = base_query.filter(Document.created_at >= thirty_days_ago).count()

            return {
                "success": True,
                "statistics": {
                    "total_documents": total_documents,
                    "status_breakdown": status_counts,
                    "file_types": file_types,
                    "size_statistics": {
                        "average_size": size_stats[0] or 0,
                        "min_size": size_stats[1] or 0,
                        "max_size": size_stats[2] or 0
                    },
                    "recent_activity": recent_docs,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error getting document statistics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Search router functions
def create_search_service(db: Session) -> AdvancedSearch:
    """Factory function to create search service"""
    return AdvancedSearch(db)

def search_documents_endpoint(
    query: str = None,
    status: str = None,
    file_type: str = None,
    date_from: str = None,
    date_to: str = None,
    min_size: str = None,
    max_size: str = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 20,
    current_user: User = None,
    db: Session = None
) -> Dict:
    """Main search endpoint function"""
    search_service = AdvancedSearch(db)

    # Build filters
    filters = {
        'status': status,
        'file_type': file_type,
        'date_from': date_from,
        'date_to': date_to,
        'min_size': min_size,
        'max_size': max_size,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'page': page,
        'per_page': per_page
    }

    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    return search_service.search_documents(
        query=query,
        filters=filters,
        user_id=current_user.id if current_user else None,
        user_role=current_user.role if current_user else "user"
    )