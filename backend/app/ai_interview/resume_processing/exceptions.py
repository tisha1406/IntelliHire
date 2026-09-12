class ResumeProcessingError(Exception):
    """Base exception for all pipeline errors."""
    pass

class UnsupportedFileTypeError(ResumeProcessingError):
    pass

class FileTooLargeError(ResumeProcessingError):
    pass

class EmptyFileError(ResumeProcessingError):
    pass

class CorruptedFileError(ResumeProcessingError):
    """Raised when parser fails to read the document."""
    pass

class ExtractionFailedError(ResumeProcessingError):
    pass
