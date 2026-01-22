"""
Pydantic Schema Validation Tests.

Tests for Notes module request/response schemas.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.modules.notes.schemas import (
    DiffHunk,
    NoteCreate,
    NoteSearchQuery,
    NoteType,
    NoteUpdate,
    NoteVersionResponse,
    SOAPContent,
    VersionDiffResponse,
)


class TestNoteCreate:
    """Test NoteCreate schema validation."""

    def test_valid_free_text_note(self):
        """Valid free-text note should pass validation."""
        data = NoteCreate(
            patient_id=1,
            title="Initial Assessment",
            content_text="Patient presents with chest pain.",
        )
        assert data.patient_id == 1
        assert data.title == "Initial Assessment"
        assert data.note_type == NoteType.FREE_TEXT

    def test_valid_soap_note(self):
        """Valid SOAP note with structured data should pass."""
        data = NoteCreate(
            patient_id=1,
            encounter_id=100,
            note_type=NoteType.SOAP,
            title="Follow-up Visit",
            content_text="SOAP note content",
            structured_data=SOAPContent(
                subjective="Patient reports improved symptoms.",
                objective="BP 120/80, HR 72",
                assessment="Hypertension controlled",
                plan="Continue current medications",
            ),
        )
        assert data.note_type == NoteType.SOAP
        assert data.structured_data.subjective == "Patient reports improved symptoms."

    def test_invalid_patient_id_zero(self):
        """Patient ID must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(
                patient_id=0,
                title="Test",
                content_text="Content",
            )
        assert "greater than 0" in str(exc_info.value).lower()

    def test_invalid_patient_id_negative(self):
        """Patient ID cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(
                patient_id=-1,
                title="Test",
                content_text="Content",
            )
        assert "greater than 0" in str(exc_info.value).lower()

    def test_title_too_long(self):
        """Title exceeding max length should fail."""
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(
                patient_id=1,
                title="x" * 256,
                content_text="Content",
            )
        assert "255" in str(exc_info.value) or "max_length" in str(exc_info.value).lower()

    def test_empty_title(self):
        """Empty title should fail."""
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(
                patient_id=1,
                title="",
                content_text="Content",
            )
        assert "min_length" in str(exc_info.value).lower() or "1" in str(exc_info.value)

    def test_empty_content(self):
        """Empty content should fail."""
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(
                patient_id=1,
                title="Test",
                content_text="",
            )
        assert "min_length" in str(exc_info.value).lower()

    def test_title_strips_whitespace(self):
        """Title should be stripped of whitespace."""
        data = NoteCreate(
            patient_id=1,
            title="  Padded Title  ",
            content_text="Content",
        )
        assert data.title == "Padded Title"


class TestNoteUpdate:
    """Test NoteUpdate schema validation."""

    def test_valid_update(self):
        """Valid update with edit reason should pass."""
        data = NoteUpdate(
            content_text="Updated content",
            edit_reason="Corrected typo in diagnosis",
        )
        assert data.content_text == "Updated content"
        assert data.edit_reason == "Corrected typo in diagnosis"

    def test_edit_reason_required(self):
        """Edit reason is required."""
        with pytest.raises(ValidationError) as exc_info:
            NoteUpdate(
                content_text="Updated content",
            )
        assert "edit_reason" in str(exc_info.value).lower()

    def test_edit_reason_too_short(self):
        """Edit reason must be at least 3 characters."""
        with pytest.raises(ValidationError) as exc_info:
            NoteUpdate(
                content_text="Updated content",
                edit_reason="ab",
            )
        assert "3" in str(exc_info.value) or "characters" in str(exc_info.value).lower()

    def test_edit_reason_strips_whitespace(self):
        """Edit reason should be stripped."""
        data = NoteUpdate(
            content_text="Content",
            edit_reason="  Valid reason  ",
        )
        assert data.edit_reason == "Valid reason"

    def test_edit_reason_whitespace_only_fails(self):
        """Edit reason with only whitespace should fail."""
        with pytest.raises(ValidationError) as exc_info:
            NoteUpdate(
                content_text="Content",
                edit_reason="   ",
            )
        # After strip, it's too short
        error_str = str(exc_info.value).lower()
        assert "3" in error_str or "characters" in error_str


class TestSOAPContent:
    """Test SOAP structured content schema."""

    def test_default_empty_fields(self):
        """SOAP fields should default to empty strings."""
        data = SOAPContent()
        assert data.subjective == ""
        assert data.objective == ""
        assert data.assessment == ""
        assert data.plan == ""

    def test_full_soap_note(self):
        """All SOAP fields can be populated."""
        data = SOAPContent(
            subjective="Chief complaint: chest pain for 2 days",
            objective="BP 140/90, HR 88, ECG shows ST depression",
            assessment="Unstable angina, ACS r/o",
            plan="Admit, cardiac enzymes, cardiology consult",
        )
        assert "chest pain" in data.subjective
        assert "BP 140/90" in data.objective
        assert "angina" in data.assessment
        assert "cardiology" in data.plan


class TestNoteSearchQuery:
    """Test search query schema validation."""

    def test_valid_search(self):
        """Valid search query should pass."""
        data = NoteSearchQuery(q="chest pain")
        assert data.q == "chest pain"
        assert data.include_attachments is True

    def test_search_with_filters(self):
        """Search with filters should pass."""
        data = NoteSearchQuery(
            q="cardiac",
            patient_id=123,
            note_type=NoteType.SOAP,
            author_id=5,
        )
        assert data.patient_id == 123
        assert data.note_type == NoteType.SOAP
        assert data.author_id == 5

    def test_query_too_short(self):
        """Search query must be at least 2 characters."""
        with pytest.raises(ValidationError) as exc_info:
            NoteSearchQuery(q="x")
        assert "2" in str(exc_info.value) or "min_length" in str(exc_info.value).lower()

    def test_query_too_long(self):
        """Search query must not exceed 500 characters."""
        with pytest.raises(ValidationError) as exc_info:
            NoteSearchQuery(q="x" * 501)
        assert "500" in str(exc_info.value) or "max_length" in str(exc_info.value).lower()


class TestDiffHunk:
    """Test diff hunk schema."""

    def test_valid_add_hunk(self):
        """Valid addition hunk."""
        hunk = DiffHunk(
            line_start=10,
            line_end=12,
            old_content="",
            new_content="New paragraph added",
            change_type="add",
        )
        assert hunk.change_type == "add"
        assert hunk.new_content == "New paragraph added"

    def test_valid_delete_hunk(self):
        """Valid deletion hunk."""
        hunk = DiffHunk(
            line_start=5,
            line_end=7,
            old_content="Removed text",
            new_content="",
            change_type="delete",
        )
        assert hunk.change_type == "delete"
        assert hunk.old_content == "Removed text"

    def test_valid_modify_hunk(self):
        """Valid modification hunk."""
        hunk = DiffHunk(
            line_start=1,
            line_end=3,
            old_content="Old diagnosis",
            new_content="Corrected diagnosis",
            change_type="modify",
        )
        assert hunk.change_type == "modify"


class TestVersionDiffResponse:
    """Test version diff response schema."""

    def test_valid_diff_response(self):
        """Valid diff response with hunks."""
        diff = VersionDiffResponse(
            note_id=1,
            version_from=1,
            version_to=2,
            hunks=[
                DiffHunk(
                    line_start=1,
                    line_end=1,
                    old_content="Typo",
                    new_content="Fixed",
                    change_type="modify",
                )
            ],
            summary="1 additions, 1 deletions",
            additions=1,
            deletions=1,
        )
        assert diff.note_id == 1
        assert len(diff.hunks) == 1
        assert diff.additions == 1

    def test_empty_diff(self):
        """Diff with no changes (identical versions)."""
        diff = VersionDiffResponse(
            note_id=1,
            version_from=1,
            version_to=1,
            hunks=[],
            summary="0 additions, 0 deletions",
            additions=0,
            deletions=0,
        )
        assert len(diff.hunks) == 0


class TestNoteVersionResponse:
    """Test version response schema."""

    def test_valid_version_response(self):
        """Valid version response."""
        version = NoteVersionResponse(
            version_id=100,
            version_number=3,
            content_text="Clinical note content",
            edited_by=5,
            edit_reason="Added lab results",
            word_count=3,
            char_count=21,
            created_at=datetime.utcnow(),
        )
        assert version.version_number == 3
        assert version.edit_reason == "Added lab results"

    def test_version_with_structured_data(self):
        """Version with SOAP structured data."""
        version = NoteVersionResponse(
            version_id=101,
            version_number=1,
            content_text="Full note text",
            structured_data={
                "subjective": "Patient reports...",
                "objective": "BP 120/80",
                "assessment": "Controlled HTN",
                "plan": "Continue meds",
            },
            edited_by=5,
            word_count=3,
            char_count=14,
            created_at=datetime.utcnow(),
        )
        assert version.structured_data["objective"] == "BP 120/80"
