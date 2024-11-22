"""Custom exceptions and error handling for Filing Cabinet."""

class FilingError(Exception):
    """Base exception for all Filing Cabinet errors."""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or "FILING_ERROR"
        super().__init__(self.message)

class FileNotFoundError(FilingError):
    """Raised when a file cannot be found."""
    def __init__(self, path: str):
        super().__init__(
            f"File not found: {path}",
            code="FILE_NOT_FOUND"
        )

class UnsupportedFileTypeError(FilingError):
    """Raised when trying to process an unsupported file type."""
    def __init__(self, mime_type: str):
        super().__init__(
            f"Unsupported file type: {mime_type}",
            code="UNSUPPORTED_FILE_TYPE"
        )

class ProcessingError(FilingError):
    """Raised when file processing fails."""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(
            f"Processing failed: {message}",
            code="PROCESSING_ERROR"
        )
        self.original_error = original_error

class ConfigurationError(FilingError):
    """Raised when there's a configuration error."""
    def __init__(self, message: str):
        super().__init__(
            f"Configuration error: {message}",
            code="CONFIG_ERROR"
        )

class AIServiceError(FilingError):
    """Raised when AI service encounters an error."""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(
            f"AI service error: {message}",
            code="AI_SERVICE_ERROR"
        )
        self.original_error = original_error
