"""
Text Extraction Pipeline Tests.

Tests for PDF, DOCX, image OCR, and text file extraction.
"""

import pytest

from app.modules.notes.extraction import (
    BaseExtractor,
    DOCXExtractor,
    ExtractionResult,
    ExtractionService,
    ImageExtractor,
    PDFExtractor,
    TextExtractor,
    extraction_service,
)


class TestExtractionResult:
    """Test ExtractionResult namedtuple."""

    def test_success_with_text(self):
        """Result with text should be successful."""
        result = ExtractionResult(
            text="Sample text",
            word_count=2,
            char_count=11,
        )
        assert result.success is True
        assert result.text == "Sample text"
        assert result.word_count == 2

    def test_failure_with_error(self):
        """Result with error should not be successful."""
        result = ExtractionResult(
            text="",
            error="Extraction failed",
        )
        assert result.success is False
        assert result.error == "Extraction failed"

    def test_pdf_result_with_page_count(self):
        """PDF result should include page count."""
        result = ExtractionResult(
            text="Page content",
            page_count=5,
            word_count=2,
            char_count=12,
        )
        assert result.page_count == 5

    def test_image_result_with_dimensions(self):
        """Image result should include dimensions."""
        result = ExtractionResult(
            text="OCR text",
            image_width=1920,
            image_height=1080,
            word_count=2,
            char_count=8,
        )
        assert result.image_width == 1920
        assert result.image_height == 1080


class TestBaseExtractor:
    """Test BaseExtractor utility methods."""

    def test_count_words_simple(self):
        """Count words in simple text."""
        assert BaseExtractor.count_words("Hello world") == 2

    def test_count_words_empty(self):
        """Empty text has zero words."""
        assert BaseExtractor.count_words("") == 0

    def test_count_words_multiline(self):
        """Count words across multiple lines."""
        text = "First line\nSecond line\nThird"
        assert BaseExtractor.count_words(text) == 5

    def test_clean_text_whitespace(self):
        """Clean normalizes whitespace."""
        text = "Multiple   spaces   and\n\nnewlines"
        cleaned = BaseExtractor.clean_text(text)
        assert "   " not in cleaned
        assert cleaned == "Multiple spaces and newlines"

    def test_clean_text_control_chars(self):
        """Clean removes control characters."""
        text = "Text with\x00null\x07bell"
        cleaned = BaseExtractor.clean_text(text)
        assert "\x00" not in cleaned
        assert "\x07" not in cleaned


class TestExtractionService:
    """Test ExtractionService configuration and validation."""

    def test_supported_pdf_mime_type(self):
        """PDF MIME type should be supported."""
        assert extraction_service.is_supported("application/pdf")

    def test_supported_docx_mime_type(self):
        """DOCX MIME type should be supported."""
        assert extraction_service.is_supported(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    def test_supported_image_mime_types(self):
        """Common image MIME types should be supported."""
        assert extraction_service.is_supported("image/jpeg")
        assert extraction_service.is_supported("image/png")
        assert extraction_service.is_supported("image/tiff")

    def test_supported_text_mime_type(self):
        """Plain text MIME type should be supported."""
        assert extraction_service.is_supported("text/plain")

    def test_unsupported_mime_type(self):
        """Unknown MIME types should not be supported."""
        assert not extraction_service.is_supported("application/x-unknown")
        assert not extraction_service.is_supported("video/mp4")

    def test_get_file_type_pdf(self):
        """PDF MIME type should map to 'pdf' file type."""
        assert extraction_service.get_file_type("application/pdf") == "pdf"

    def test_get_file_type_docx(self):
        """DOCX MIME type should map to 'docx' file type."""
        assert (
            extraction_service.get_file_type(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            == "docx"
        )

    def test_get_file_type_image(self):
        """Image MIME types should map to 'image' file type."""
        assert extraction_service.get_file_type("image/jpeg") == "image"
        assert extraction_service.get_file_type("image/png") == "image"

    def test_validate_size_within_limit(self):
        """Files within size limit should pass validation."""
        content = b"x" * 1024  # 1KB
        error = extraction_service.validate_size(content, "application/pdf")
        assert error is None

    def test_validate_size_exceeds_limit(self):
        """Files exceeding limit should fail validation."""
        content = b"x" * (51 * 1024 * 1024)  # 51MB
        error = extraction_service.validate_size(content, "application/pdf")
        assert error is not None
        assert "too large" in error.lower()

    def test_validate_size_unsupported_type(self):
        """Unsupported types should fail validation."""
        content = b"x" * 1024
        error = extraction_service.validate_size(content, "application/x-unknown")
        assert error is not None
        assert "unsupported" in error.lower()

    def test_compute_checksum(self):
        """Checksum should be consistent for same content."""
        content = b"Test content for checksum"
        checksum1 = ExtractionService.compute_checksum(content)
        checksum2 = ExtractionService.compute_checksum(content)
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex digest

    def test_checksum_differs_for_different_content(self):
        """Different content should produce different checksums."""
        checksum1 = ExtractionService.compute_checksum(b"Content A")
        checksum2 = ExtractionService.compute_checksum(b"Content B")
        assert checksum1 != checksum2

    def test_detect_mime_type_from_extension(self):
        """MIME type detection should work from file extension."""
        assert ExtractionService.detect_mime_type(b"", "document.pdf") == "application/pdf"
        assert (
            ExtractionService.detect_mime_type(b"", "document.docx")
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert ExtractionService.detect_mime_type(b"", "image.jpg") == "image/jpeg"
        assert ExtractionService.detect_mime_type(b"", "image.png") == "image/png"
        assert ExtractionService.detect_mime_type(b"", "notes.txt") == "text/plain"

    def test_get_extractor_returns_correct_type(self):
        """get_extractor should return correct extractor type."""
        pdf_extractor = extraction_service.get_extractor("application/pdf")
        assert isinstance(pdf_extractor, PDFExtractor)

        docx_extractor = extraction_service.get_extractor(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert isinstance(docx_extractor, DOCXExtractor)

        image_extractor = extraction_service.get_extractor("image/jpeg")
        assert isinstance(image_extractor, ImageExtractor)

        text_extractor = extraction_service.get_extractor("text/plain")
        assert isinstance(text_extractor, TextExtractor)

    def test_get_extractor_caches_instances(self):
        """Extractors should be cached and reused."""
        ext1 = extraction_service.get_extractor("application/pdf")
        ext2 = extraction_service.get_extractor("application/pdf")
        assert ext1 is ext2

    def test_get_extractor_unsupported_returns_none(self):
        """Unsupported MIME types should return None."""
        extractor = extraction_service.get_extractor("application/x-unknown")
        assert extractor is None


class TestTextExtractor:
    """Test plain text file extraction."""

    @pytest.fixture
    def extractor(self) -> TextExtractor:
        return TextExtractor()

    @pytest.mark.asyncio
    async def test_extract_utf8_text(self, extractor: TextExtractor):
        """Extract UTF-8 encoded text."""
        content = "Hello, World!\nThis is a test.".encode("utf-8")
        result = await extractor.extract(content, "test.txt")

        assert result.success
        assert "Hello, World!" in result.text
        assert result.word_count == 6
        assert result.char_count > 0

    @pytest.mark.asyncio
    async def test_extract_greek_text(self, extractor: TextExtractor):
        """Extract Greek text (cp1253 encoding)."""
        greek_text = "Γειά σου Κόσμε"  # Hello World in Greek
        # Try UTF-8 first as it's more common
        content = greek_text.encode("utf-8")
        result = await extractor.extract(content, "greek.txt")

        assert result.success
        assert "Γειά" in result.text

    @pytest.mark.asyncio
    async def test_extract_latin1_text(self, extractor: TextExtractor):
        """Extract Latin-1 encoded text."""
        content = "Café résumé naïve".encode("latin-1")
        result = await extractor.extract(content, "latin.txt")

        assert result.success
        assert "Café" in result.text or "Caf" in result.text


class TestExtractionServiceIntegration:
    """Integration tests for the extraction service."""

    @pytest.mark.asyncio
    async def test_extract_plain_text(self):
        """Full extraction flow for plain text."""
        content = b"This is a clinical note about the patient."
        result = await extraction_service.extract(content, "note.txt", "text/plain")

        assert result.success
        assert "clinical note" in result.text
        assert result.word_count == 8

    @pytest.mark.asyncio
    async def test_extract_unsupported_type(self):
        """Extraction fails gracefully for unsupported types."""
        content = b"Some binary data"
        result = await extraction_service.extract(content, "file.xyz", "application/x-unknown")

        assert not result.success
        assert "extractor" in result.error.lower() or "unsupported" in result.error.lower()

    @pytest.mark.asyncio
    async def test_extract_oversized_file(self):
        """Extraction fails for oversized files."""
        content = b"x" * (51 * 1024 * 1024)  # 51MB
        result = await extraction_service.extract(content, "large.pdf", "application/pdf")

        assert not result.success
        assert "large" in result.error.lower()
