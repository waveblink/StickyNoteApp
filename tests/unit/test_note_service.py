"""Test note service functionality."""

import pytest
from datetime import datetime
from src.aurora_notes.services.note_service import NoteService
from src.aurora_notes.crypto.encryption import encryption_service
from src.aurora_notes.models.base import init_db


@pytest.fixture
def note_service():
    """Create note service with test database."""
    # Initialize test database
    init_db()
    
    # Initialize encryption with test key
    encryption_service._key = b'test' * 8
    
    return NoteService()


class TestNoteService:
    """Test note CRUD operations."""
    
    def test_create_note(self, note_service):
        """Test note creation."""
        note = note_service.create_note(
            title="Test Note",
            body="<p>Test content</p>"
        )
        
        assert note.id is not None
        assert note.title == "Test Note"
        assert note.body_enc is not None
        assert note.created_at is not None
    
    def test_get_note(self, note_service):
        """Test note retrieval."""
        # Create note
        note = note_service.create_note(
            title="Test",
            body="<p>Content</p>"
        )
        
        # Retrieve
        result = note_service.get_note(note.id)
        assert result is not None
        
        retrieved_note, body = result
        assert retrieved_note.id == note.id
        assert body == "<p>Content</p>"
    
    def test_update_note(self, note_service):
        """Test note update."""
        # Create note
        note = note_service.create_note(
            title="Original",
            body="<p>Original</p>"
        )
        
        # Update
        updated = note_service.update_note(
            note.id,
            title="Updated",
            body="<p>Updated</p>"
        )
        
        assert updated.title == "Updated"
        
        # Verify encrypted body changed
        assert updated.body_enc != note.body_enc
        
        # Verify decryption
        _, body = note_service.get_note(note.id)
        assert body == "<p>Updated</p>"
    
    def test_search_notes(self, note_service):
        """Test fuzzy search."""
        # Create test notes
        note_service.create_note("Python Tutorial", "Learn Python basics")
        note_service.create_note("JavaScript Guide", "JS fundamentals")
        note_service.create_note("Python Advanced", "Advanced Python concepts")
        
        # Search
        results = note_service.search_notes("python")
        
        assert len(results) == 2
        assert all("python" in note.title.lower() for note, _, _ in results)
        
        # Check scores are sorted
        scores = [score for _, _, score in results]
        assert scores == sorted(scores, reverse=True)