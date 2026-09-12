import time
import logging
from typing import Optional
from app.ai_interview.resume_processing.schemas import (
    ResumeProcessingRequest,
    CandidateInterviewContext,
    ExtractionMetadata,
)
from app.ai_interview.resume_processing.exceptions import ResumeProcessingError
from app.ai_interview.resume_processing.file_validator import FileValidator
from app.ai_interview.resume_processing.text_extractor import TextExtractor
from app.ai_interview.resume_processing.text_cleaner import TextCleaner
from app.ai_interview.resume_processing.resume_normalizer import ResumeNormalizer
from app.ai_interview.resume_processing.structured_extractor import DeterministicResumeStructuredExtractor
from app.ai_interview.resume_processing.quality_validator import QualityValidator
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus

logger = logging.getLogger(__name__)

class ResumeProcessingPipeline:
    def __init__(self, extractor=None):
        self.extractor = extractor or DeterministicResumeStructuredExtractor()
        
    def process(self, request: ResumeProcessingRequest) -> CandidateInterviewContext:
        start_time = time.time()
        candidate_log_ctx = f"Candidate: {request.candidate_id}" if request.candidate_id else "No Candidate ID"
        
        try:
            # 1. File Validation
            logger.info(f"[{candidate_log_ctx}] Stage: FILE_VALIDATION - Starting")
            FileValidator.validate(request.resume_file)
            
            # 2. Text Extraction
            logger.info(f"[{candidate_log_ctx}] Stage: TEXT_EXTRACTION - Starting")
            extracted_doc = TextExtractor.extract(request.resume_file)
            logger.info(f"[{candidate_log_ctx}] Stage: TEXT_EXTRACTION - Extracted {extracted_doc.character_count} chars from {extracted_doc.source_type}")
            
            # 3. Text Cleaning
            logger.info(f"[{candidate_log_ctx}] Stage: TEXT_CLEANING - Starting")
            cleaned_text = TextCleaner.clean(extracted_doc.raw_text)
            
            # 4. Normalization
            logger.info(f"[{candidate_log_ctx}] Stage: NORMALIZATION - Starting")
            normalized_text = ResumeNormalizer.normalize(cleaned_text)
            detected_sections = list(normalized_text.sections.keys())
            
            # 5. Quality Validation
            logger.info(f"[{candidate_log_ctx}] Stage: QUALITY_VALIDATION - Starting")
            quality_status, warnings = QualityValidator.validate(extracted_doc, normalized_text)
            
            if quality_status == ExtractionQualityStatus.UNUSABLE:
                from app.ai_interview.resume_processing.exceptions import ExtractionFailedError
                raise ExtractionFailedError("Resume extraction is UNUSABLE. Cannot proceed.")
            
            # 6. Structured Extraction
            logger.info(f"[{candidate_log_ctx}] Stage: STRUCTURED_EXTRACTION - Starting")
            structured_resume = self.extractor.extract(normalized_text)
            
            duration_ms = (time.time() - start_time) * 1000
            
            metadata = ExtractionMetadata(
                source_type=extracted_doc.source_type,
                extractor_name=self.extractor.__class__.__name__,
                extractor_version="1.0.0",
                character_count=extracted_doc.character_count,
                detected_sections=detected_sections,
                warning_count=len(warnings),
                processing_duration_ms=duration_ms
            )
            
            context = CandidateInterviewContext(
                candidate_id=request.candidate_id,
                structured_resume=structured_resume,
                extraction_metadata=metadata,
                quality_status=quality_status,
                warnings=warnings
            )
            
            logger.info(f"[{candidate_log_ctx}] Pipeline completed successfully in {duration_ms:.2f}ms with status {quality_status}")
            return context
            
        except ResumeProcessingError as e:
            logger.error(f"[{candidate_log_ctx}] Pipeline failed at stage: {e.__class__.__name__} - {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"[{candidate_log_ctx}] Unexpected error in pipeline: {str(e)}")
            raise ResumeProcessingError(f"An unexpected error occurred during resume processing: {str(e)}")
