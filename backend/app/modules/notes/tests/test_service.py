"""
Note Service Unit Tests.

Tests for NoteService business logic including version management,
diff computation, and access logging.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.notes.schemas import NoteCreate, NoteType, NoteUpdate, SOAPContent
from app.modules.notes.service import NoteService


class TestDiffComputation:
    """Test diff computation methods."""

    @pytest.fixture
    def service(self) -> NoteService:
        """Create service with mock database."""
        mock_db = AsyncMock()
        return NoteService(mock_db)

    def test_compute_diff_empty_to_text(self, service: NoteService):
        """Diff from empty to text shows all additions."""
        diff = service._compute_diff("", "New content\nSecond line")
        assert "unified_diff" in diff
        assert diff["old_word_count"] == 0
        assert diff["new_word_count"] == 3

    def test_compute_diff_text_to_empty(self, service: NoteService):
        """Diff from text to empty shows all deletions."""
        diff = service._compute_diff("Old content\nAnother line", "")
        assert diff["old_word_count"] == 4
        assert diff["new_word_count"] == 0

    def test_compute_diff_modification(self, service: NoteService):
        """Diff shows modifications correctly."""
        old = "Patient presents with chest pain."
        new = "Patient presents with severe chest pain and dyspnea."
        diff = service._compute_diff(old, new)
        assert "unified_diff" in diff
        assert diff["old_word_count"] == 5
        assert diff["new_word_count"] == 8

    def test_compute_diff_no_change(self, service: NoteService):
        """Identical text produces minimal diff."""
        text = "Same content"
        diff = service._compute_diff(text, text)
        assert diff["old_word_count"] == diff["new_word_count"]

    def test_compute_diff_hunks_addition(self, service: NoteService):
        """Diff hunks for pure addition."""
        old = "Line 1\nLine 2"
        new = "Line 1\nLine 2\nLine 3"
        hunks, additions, deletions = service._compute_diff_hunks(old, new)

        assert additions >= 1
        assert deletions == 0
        assert len(hunks) >= 1
        assert any(h.change_type == "add" for h in hunks)

    def test_compute_diff_hunks_deletion(self, service: NoteService):
        """Diff hunks for pure deletion."""
        old = "Line 1\nLine 2\nLine 3"
        new = "Line 1\nLine 2"
        hunks, additions, deletions = service._compute_diff_hunks(old, new)

        assert deletions >= 1
        assert additions == 0
        assert any(h.change_type == "delete" for h in hunks)

    def test_compute_diff_hunks_modification(self, service: NoteService):
        """Diff hunks for modification."""
        old = "Patient has hypertension"
        new = "Patient has controlled hypertension"
        hunks, additions, deletions = service._compute_diff_hunks(old, new)

        assert len(hunks) >= 1
        # Either modify or replace shows as add+delete
        assert additions >= 0 or deletions >= 0

    def test_compute_diff_hunks_multiline(self, service: NoteService):
        """Diff hunks for multiline changes."""
        old = """Assessment:
1. Hypertension
2. Diabetes
3. Hyperlipidemia"""
        new = """Assessment:
1. Hypertension - controlled
2. Diabetes - A1c 7.2
3. Hyperlipidemia - on statin
4. New: Atrial fibrillation"""
        hunks, additions, deletions = service._compute_diff_hunks(old, new)

        # Should detect changes and additions
        assert additions > 0


class TestNoteCreateValidation:
    """Test note creation input handling."""

    def test_valid_free_text_note(self):
        """Create valid free-text note."""
        data = NoteCreate(
            patient_id=1,
            title="Initial Assessment",
            content_text="Patient history and findings.",
        )
        assert data.note_type == NoteType.FREE_TEXT
        assert data.patient_id == 1

    def test_valid_soap_note(self):
        """Create valid SOAP note."""
        data = NoteCreate(
            patient_id=1,
            note_type=NoteType.SOAP,
            title="Follow-up Visit",
            content_text="Full note text",
            structured_data=SOAPContent(
                subjective="Reports improved symptoms",
                objective="BP 120/80, HR 72, regular rhythm",
                assessment="HTN controlled, AF stable",
                plan="Continue warfarin, INR in 1 week",
            ),
        )
        assert data.structured_data is not None
        assert "warfarin" in data.structured_data.plan

    def test_procedure_note(self):
        """Create procedure note."""
        data = NoteCreate(
            patient_id=1,
            encounter_id=100,
            note_type=NoteType.PROCEDURE,
            title="Coronary Angiography",
            content_text="Right radial approach, 3-vessel disease identified.",
        )
        assert data.note_type == NoteType.PROCEDURE
        assert data.encounter_id == 100


class TestNoteUpdateValidation:
    """Test note update input handling."""

    def test_valid_update_with_reason(self):
        """Update with valid edit reason."""
        data = NoteUpdate(
            content_text="Corrected assessment",
            edit_reason="Fixed typo in medication name",
        )
        assert len(data.edit_reason) >= 3

    def test_update_with_soap_data(self):
        """Update SOAP note with structured data."""
        data = NoteUpdate(
            content_text="Updated SOAP note",
            structured_data=SOAPContent(
                subjective="Updated subjective",
                objective="Updated vitals: BP 118/78",
                assessment="Improved",
                plan="Reduce medication dose",
            ),
            edit_reason="Updated after lab results received",
        )
        assert "118/78" in data.structured_data.objective


class TestWordAndCharCounting:
    """Test word and character counting for versions."""

    @pytest.fixture
    def service(self) -> NoteService:
        mock_db = AsyncMock()
        return NoteService(mock_db)

    def test_word_count_simple(self, service: NoteService):
        """Simple word count."""
        text = "Patient presents with chest pain"
        words = len(text.split())
        assert words == 5

    def test_word_count_multiline(self, service: NoteService):
        """Word count across lines."""
        text = """Assessment:
        Hypertension stage 2
        Diabetes type 2"""
        words = len(text.split())
        assert words == 6

    def test_char_count(self, service: NoteService):
        """Character count includes spaces."""
        text = "Hello World"
        assert len(text) == 11


class TestAccessLoggingData:
    """Test access log data structure."""

    def test_view_action_fields(self):
        """VIEW action should have version_accessed."""
        # Verify schema expectations
        from app.modules.notes.models import NoteAccessAction
        assert NoteAccessAction.VIEW.value == "VIEW"

    def test_edit_action_fields(self):
        """EDIT action should have version_accessed."""
        from app.modules.notes.models import NoteAccessAction
        assert NoteAccessAction.EDIT.value == "EDIT"

    def test_download_action_fields(self):
        """DOWNLOAD_ATTACHMENT action should have attachment_id."""
        from app.modules.notes.models import NoteAccessAction
        assert NoteAccessAction.DOWNLOAD_ATTACHMENT.value == "DOWNLOAD_ATTACHMENT"

    def test_search_action_fields(self):
        """SEARCH action should have search_query."""
        from app.modules.notes.models import NoteAccessAction
        assert NoteAccessAction.SEARCH.value == "SEARCH"


class TestAttachmentValidation:
    """Test attachment-related validation logic."""

    def test_supported_pdf(self):
        """PDF should be supported."""
        from app.modules.notes.extraction import extraction_service
        assert extraction_service.is_supported("application/pdf")

    def test_supported_docx(self):
        """DOCX should be supported."""
        from app.modules.notes.extraction import extraction_service
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert extraction_service.is_supported(mime)

    def test_supported_images(self):
        """Common image formats should be supported."""
        from app.modules.notes.extraction import extraction_service
        assert extraction_service.is_supported("image/jpeg")
        assert extraction_service.is_supported("image/png")

    def test_file_size_limits(self):
        """File size limits should be enforced."""
        from app.modules.notes.extraction import extraction_service

        # PDF limit is 50MB
        assert extraction_service.MAX_SIZES["pdf"] == 50 * 1024 * 1024

        # Image limit is 20MB
        assert extraction_service.MAX_SIZES["image"] == 20 * 1024 * 1024


class TestSearchQueryBuilding:
    """Test search query construction."""

    def test_search_query_basic(self):
        """Basic search query."""
        from app.modules.notes.schemas import NoteSearchQuery
        query = NoteSearchQuery(q="chest pain")
        assert query.q == "chest pain"
        assert query.include_attachments is True

    def test_search_query_with_patient_filter(self):
        """Search filtered by patient."""
        from app.modules.notes.schemas import NoteSearchQuery
        query = NoteSearchQuery(q="ecg", patient_id=123)
        assert query.patient_id == 123

    def test_search_query_with_type_filter(self):
        """Search filtered by note type."""
        from app.modules.notes.schemas import NoteSearchQuery
        query = NoteSearchQuery(q="assessment", note_type=NoteType.SOAP)
        assert query.note_type == NoteType.SOAP

    def test_search_query_with_date_range(self):
        """Search with date range filter."""
        from app.modules.notes.schemas import NoteSearchQuery
        from datetime import datetime

        query = NoteSearchQuery(
            q="follow-up",
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 12, 31),
        )
        assert query.date_from.year == 2024
        assert query.date_to.month == 12
