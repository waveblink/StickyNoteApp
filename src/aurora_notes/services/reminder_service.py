"""Reminder scheduling service."""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID
from PySide6.QtCore import QObject, Signal
from apscheduler.schedulers.qt import QtScheduler
from apscheduler.triggers.date import DateTrigger
import dateparser


class ReminderService(QObject):
    """Handles reminder scheduling and notifications."""
    
    reminderTriggered = Signal(UUID, str, str)  # note_id, title, body
    
    def __init__(self):
        super().__init__()
        self.scheduler = QtScheduler()
        self.active_reminders: Dict[UUID, str] = {}  # note_id -> job_id
        self.scheduler.start()
    
    def parse_reminder(self, text: str) -> Optional[datetime]:
        """Parse natural language date/time."""
        # Lock to English for v1
        result = dateparser.parse(
            text,
            languages=['en'],
            settings={
                'PREFER_DATES_FROM': 'future',
                'RETURN_AS_TIMEZONE_AWARE': False
            }
        )
        return result
    
    def schedule_reminder(
        self,
        note_id: UUID,
        reminder_at: datetime,
        title: str,
        body_preview: str
    ):
        """Schedule a reminder for a note."""
        # Cancel existing reminder for this note
        self.cancel_reminder(note_id)
        
        # Schedule new reminder
        job = self.scheduler.add_job(
            func=self._trigger_reminder,
            trigger=DateTrigger(run_date=reminder_at),
            args=[note_id, title, body_preview],
            id=f"reminder_{note_id}",
            replace_existing=True
        )
        
        self.active_reminders[note_id] = job.id
    
    def _trigger_reminder(self, note_id: UUID, title: str, body_preview: str):
        """Trigger reminder notification."""
        self.reminderTriggered.emit(note_id, title, body_preview)
        
        # Remove from active reminders
        if note_id in self.active_reminders:
            del self.active_reminders[note_id]
    
    def cancel_reminder(self, note_id: UUID):
        """Cancel reminder for a note."""
        if note_id in self.active_reminders:
            job_id = self.active_reminders[note_id]
            try:
                self.scheduler.remove_job(job_id)
                del self.active_reminders[note_id]
            except:
                pass
    
    def reschedule_all_reminders(self, note_service):
        """Reschedule all reminders on app start."""
        from ..services.note_service import NoteService
        
        notes = note_service.get_all_notes()
        now = datetime.utcnow()
        
        for note, body in notes:
            if note.reminder_at and note.reminder_at > now:
                # Extract first 50 chars as preview
                body_preview = body[:50] + "..." if len(body) > 50 else body
                self.schedule_reminder(
                    note.id,
                    note.reminder_at,
                    note.title,
                    body_preview
                )
    
    def shutdown(self):
        """Shutdown scheduler."""
        self.scheduler.shutdown(wait=False)