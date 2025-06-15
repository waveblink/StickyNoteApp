"""Note CRUD service layer."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select
from ..models.base import Note, create_db_engine
from ..crypto.encryption import encryption_service


class NoteService:
    """Handles note operations with encryption."""
    
    def __init__(self):
        self.engine = create_db_engine()
    
    def create_note(
        self,
        title: str,
        body: str,
        folder_id: Optional[UUID] = None,
        pinned: bool = False,
        reminder_at: Optional[datetime] = None
    ) -> Note:
        """Create encrypted note."""
        with Session(self.engine) as session:
            note = Note(
                title=title,
                body_enc=encryption_service.encrypt(body),
                folder_id=folder_id,
                pinned=pinned,
                reminder_at=reminder_at
            )
            session.add(note)
            session.commit()
            session.refresh(note)
            return note
    
    def update_note(
        self,
        note_id: UUID,
        title: Optional[str] = None,
        body: Optional[str] = None,
        folder_id: Optional[UUID] = None,
        pinned: Optional[bool] = None,
        reminder_at: Optional[datetime] = None
    ) -> Optional[Note]:
        """Update note with encryption."""
        with Session(self.engine) as session:
            note = session.get(Note, note_id)
            if not note:
                return None
            
            if title is not None:
                note.title = title
            if body is not None:
                note.body_enc = encryption_service.encrypt(body)
            if folder_id is not None:
                note.folder_id = folder_id
            if pinned is not None:
                note.pinned = pinned
            if reminder_at is not None:
                note.reminder_at = reminder_at
            
            note.updated_at = datetime.utcnow()
            session.add(note)
            session.commit()
            session.refresh(note)
            return note
    
    def get_note(self, note_id: UUID) -> Optional[tuple[Note, str]]:
        """Get note with decrypted body."""
        with Session(self.engine) as session:
            note = session.get(Note, note_id)
            if note:
                body = encryption_service.decrypt(note.body_enc)
                return note, body
            return None
    
    def get_all_notes(self, folder_id: Optional[UUID] = None) -> List[tuple[Note, str]]:
        """Get all notes with decrypted bodies."""
        with Session(self.engine) as session:
            statement = select(Note)
            if folder_id:
                statement = statement.where(Note.folder_id == folder_id)
            
            notes = session.exec(statement).all()
            result = []
            for note in notes:
                body = encryption_service.decrypt(note.body_enc)
                result.append((note, body))
            return result
    
    def delete_note(self, note_id: UUID) -> bool:
        """Delete note."""
        with Session(self.engine) as session:
            note = session.get(Note, note_id)
            if note:
                session.delete(note)
                session.commit()
                return True
            return False
    
    def search_notes(self, query: str) -> List[tuple[Note, str, float]]:
        """Search notes using fuzzy matching."""
        from rapidfuzz import fuzz
        
        all_notes = self.get_all_notes()
        results = []
        
        for note, body in all_notes:
            # Score based on title and body
            title_score = fuzz.partial_ratio(query.lower(), note.title.lower())
            body_score = fuzz.partial_ratio(query.lower(), body.lower())
            combined_score = max(title_score, body_score * 0.8)
            
            if combined_score > 60:  # Threshold
                results.append((note, body, combined_score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[2], reverse=True)
        return results  