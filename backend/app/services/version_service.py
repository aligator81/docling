from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

from ..models import Document, DocumentVersion, DocumentCollaborator, DocumentComment, DocumentActivity, User

logger = logging.getLogger(__name__)

class DocumentVersionService:
    def __init__(self, db: Session):
        self.db = db

    def create_version(self, document_id: int, user_id: int, changes_description: str = None) -> Dict:
        """Create a new version of a document"""
        try:
            # Get the document
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {"success": False, "error": "Document not found"}

            # Get the latest version number
            latest_version = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(DocumentVersion.version_number.desc()).first()

            new_version_number = (latest_version.version_number + 1) if latest_version else 1

            # Create new version
            new_version = DocumentVersion(
                document_id=document_id,
                version_number=new_version_number,
                content=document.content,
                changes=changes_description or "Content updated",
                created_by=user_id
            )

            self.db.add(new_version)

            # Log the activity
            activity = DocumentActivity(
                document_id=document_id,
                user_id=user_id,
                activity_type="version_created",
                description=f"Version {new_version_number} created",
                metadata_=json.dumps({
                    "version_number": new_version_number,
                    "changes": changes_description
                })
            )
            self.db.add(activity)

            self.db.commit()

            return {
                "success": True,
                "version": new_version,
                "message": f"Version {new_version_number} created successfully"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating document version: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_versions(self, document_id: int) -> Dict:
        """Get all versions of a document"""
        try:
            versions = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(DocumentVersion.version_number.desc()).all()

            return {
                "success": True,
                "versions": versions,
                "total_count": len(versions)
            }

        except Exception as e:
            logger.error(f"Error getting document versions: {str(e)}")
            return {"success": False, "error": str(e), "versions": []}

    def restore_version(self, document_id: int, version_number: int, user_id: int) -> Dict:
        """Restore a document to a specific version"""
        try:
            # Get the target version
            target_version = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == version_number
            ).first()

            if not target_version:
                return {"success": False, "error": "Version not found"}

            # Get current document
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {"success": False, "error": "Document not found"}

            # Create a new version with current content before restoring
            current_content = document.content
            self.create_version(
                document_id,
                user_id,
                f"Backup before restoring to version {version_number}"
            )

            # Restore to target version
            document.content = target_version.content
            document.processed_at = datetime.utcnow()
            self.db.commit()

            # Log the activity
            activity = DocumentActivity(
                document_id=document_id,
                user_id=user_id,
                activity_type="version_restored",
                description=f"Document restored to version {version_number}",
                metadata_=json.dumps({"restored_version": version_number})
            )
            self.db.add(activity)
            self.db.commit()

            return {
                "success": True,
                "message": f"Document restored to version {version_number} successfully"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error restoring document version: {str(e)}")
            return {"success": False, "error": str(e)}

class DocumentCollaborationService:
    def __init__(self, db: Session):
        self.db = db

    def add_collaborator(self, document_id: int, user_id: int, collaborator_email: str, permission_level: str, added_by: int) -> Dict:
        """Add a collaborator to a document"""
        try:
            # Verify the document exists and user has permission
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {"success": False, "error": "Document not found"}

            # Check if adder has permission (owner or admin)
            if document.user_id != added_by:
                adder_role = self.db.query(User.role).filter(User.id == added_by).first()
                if not adder_role or adder_role.role != "admin":
                    return {"success": False, "error": "Insufficient permissions to add collaborators"}

            # Find the user to add as collaborator
            collaborator = self.db.query(User).filter(
                User.email == collaborator_email,
                User.is_active == True
            ).first()

            if not collaborator:
                return {"success": False, "error": "User not found or inactive"}

            # Check if already a collaborator
            existing = self.db.query(DocumentCollaborator).filter(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == collaborator.id
            ).first()

            if existing:
                return {"success": False, "error": "User is already a collaborator"}

            # Add collaborator
            new_collaborator = DocumentCollaborator(
                document_id=document_id,
                user_id=collaborator.id,
                permission_level=permission_level,
                added_by=added_by
            )

            self.db.add(new_collaborator)

            # Log the activity
            activity = DocumentActivity(
                document_id=document_id,
                user_id=added_by,
                activity_type="collaborator_added",
                description=f"Added {collaborator.username} as {permission_level}",
                metadata_=json.dumps({
                    "collaborator_id": collaborator.id,
                    "permission_level": permission_level
                })
            )
            self.db.add(activity)

            self.db.commit()

            return {
                "success": True,
                "collaborator": new_collaborator,
                "message": f"Added {collaborator.username} as {permission_level} successfully"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding collaborator: {str(e)}")
            return {"success": False, "error": str(e)}

    def remove_collaborator(self, document_id: int, collaborator_id: int, removed_by: int) -> Dict:
        """Remove a collaborator from a document"""
        try:
            # Get the collaboration record
            collaboration = self.db.query(DocumentCollaborator).filter(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == collaborator_id
            ).first()

            if not collaboration:
                return {"success": False, "error": "Collaborator not found"}

            # Check permissions
            if collaboration.added_by != removed_by:
                remover_role = self.db.query(User.role).filter(User.id == removed_by).first()
                if not remover_role or remover_role.role != "admin":
                    return {"success": False, "error": "Insufficient permissions to remove collaborators"}

            # Soft delete by marking as inactive
            collaboration.is_active = False

            # Log the activity
            removed_user = self.db.query(User.username).filter(User.id == collaborator_id).first()
            username = removed_user.username if removed_user else "unknown"

            activity = DocumentActivity(
                document_id=document_id,
                user_id=removed_by,
                activity_type="collaborator_removed",
                description=f"Removed {username} from collaborators",
                metadata_=json.dumps({"removed_collaborator_id": collaborator_id})
            )
            self.db.add(activity)

            self.db.commit()

            return {
                "success": True,
                "message": f"Removed collaborator successfully"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing collaborator: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_collaborators(self, document_id: int) -> Dict:
        """Get all active collaborators for a document"""
        try:
            collaborators = self.db.query(DocumentCollaborator).filter(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.is_active == True
            ).all()

            return {
                "success": True,
                "collaborators": collaborators,
                "total_count": len(collaborators)
            }

        except Exception as e:
            logger.error(f"Error getting collaborators: {str(e)}")
            return {"success": False, "error": str(e), "collaborators": []}

    def check_collaborator_permission(self, document_id: int, user_id: int, required_permission: str) -> bool:
        """Check if a user has the required permission level for a document"""
        try:
            # Document owner always has full permissions
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if document and document.user_id == user_id:
                return True

            # Check collaborator permissions
            collaboration = self.db.query(DocumentCollaborator).filter(
                DocumentCollaborator.document_id == document_id,
                DocumentCollaborator.user_id == user_id,
                DocumentCollaborator.is_active == True
            ).first()

            if not collaboration:
                return False

            permission_levels = {
                "viewer": ["viewer"],
                "editor": ["viewer", "editor"],
                "owner": ["viewer", "editor", "owner"]
            }

            allowed_permissions = permission_levels.get(collaboration.permission_level, [])
            return required_permission in allowed_permissions

        except Exception as e:
            logger.error(f"Error checking collaborator permission: {str(e)}")
            return False

class DocumentCommentService:
    def __init__(self, db: Session):
        self.db = db

    def add_comment(self, document_id: int, user_id: int, content: str, comment_type: str = "general", position_data: str = None) -> Dict:
        """Add a comment to a document"""
        try:
            comment = DocumentComment(
                document_id=document_id,
                user_id=user_id,
                content=content,
                comment_type=comment_type,
                position_data=position_data
            )

            self.db.add(comment)

            # Log the activity
            activity = DocumentActivity(
                document_id=document_id,
                user_id=user_id,
                activity_type="comment_added",
                description=f"Added {comment_type} comment",
                metadata_=json.dumps({
                    "comment_type": comment_type,
                    "comment_id": comment.id
                })
            )
            self.db.add(activity)

            self.db.commit()

            return {
                "success": True,
                "comment": comment,
                "message": "Comment added successfully"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding comment: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_comments(self, document_id: int) -> Dict:
        """Get all comments for a document"""
        try:
            comments = self.db.query(DocumentComment).filter(
                DocumentComment.document_id == document_id
            ).order_by(DocumentComment.created_at.desc()).all()

            return {
                "success": True,
                "comments": comments,
                "total_count": len(comments)
            }

        except Exception as e:
            logger.error(f"Error getting comments: {str(e)}")
            return {"success": False, "error": str(e), "comments": []}

    def resolve_comment(self, comment_id: int, user_id: int) -> Dict:
        """Mark a comment as resolved"""
        try:
            comment = self.db.query(DocumentComment).filter(DocumentComment.id == comment_id).first()

            if not comment:
                return {"success": False, "error": "Comment not found"}

            # Check if user has permission to resolve comments
            if comment.user_id != user_id:
                # Check if user is document owner or admin
                document = self.db.query(Document).filter(Document.id == comment.document_id).first()
                if not document or (document.user_id != user_id):
                    user_role = self.db.query(User.role).filter(User.id == user_id).first()
                    if not user_role or user_role.role != "admin":
                        return {"success": False, "error": "Insufficient permissions to resolve comments"}

            comment.is_resolved = True
            self.db.commit()

            return {
                "success": True,
                "message": "Comment marked as resolved"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resolving comment: {str(e)}")
            return {"success": False, "error": str(e)}

class DocumentActivityService:
    def __init__(self, db: Session):
        self.db = db

    def log_activity(self, document_id: int, user_id: int, activity_type: str, description: str, metadata: Dict = None) -> None:
        """Log a document activity"""
        try:
            activity = DocumentActivity(
                document_id=document_id,
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                metadata_=json.dumps(metadata) if metadata else None
            )

            self.db.add(activity)
            self.db.commit()

        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
            # Don't rollback for activity logging failures

    def get_activities(self, document_id: int, limit: int = 50) -> Dict:
        """Get recent activities for a document"""
        try:
            activities = self.db.query(DocumentActivity).filter(
                DocumentActivity.document_id == document_id
            ).order_by(DocumentActivity.created_at.desc()).limit(limit).all()

            return {
                "success": True,
                "activities": activities,
                "total_count": len(activities)
            }

        except Exception as e:
            logger.error(f"Error getting activities: {str(e)}")
            return {"success": False, "error": str(e), "activities": []}

# Factory functions for creating services
def create_version_service(db: Session) -> DocumentVersionService:
    return DocumentVersionService(db)

def create_collaboration_service(db: Session) -> DocumentCollaborationService:
    return DocumentCollaborationService(db)

def create_comment_service(db: Session) -> DocumentCommentService:
    return DocumentCommentService(db)

def create_activity_service(db: Session) -> DocumentActivityService:
    return DocumentActivityService(db)