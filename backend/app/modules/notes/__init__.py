"""Doctor's Notes module for clinical documentation."""

from app.modules.notes.models import (
    ClinicalNote,
    NoteVersion,
    NoteAttachment,
    NoteAccessLog,
    NoteType,
)
from app.modules.notes.service import NoteService
from app.modules.notes.router import router as notes_router

__all__ = [
    "ClinicalNote",
    "NoteVersion",
    "NoteAttachment",
    "NoteAccessLog",
    "NoteType",
    "NoteService",
    "notes_router",
]
