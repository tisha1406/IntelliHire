from app.ai_interview.resume_processing.schemas import (
    ExtractedDocument, 
    NormalizedResumeText,
    ExtractionWarning,
)
from app.ai_interview.resume_processing.enums import (
    ExtractionWarningCode,
    ExtractionQualityStatus,
)
from app.ai_interview.resume_processing.config import ResumeProcessingConfig
from app.ai_interview.resume_processing.exceptions import ExtractionFailedError
from typing import Tuple, List

class QualityValidator:
    @staticmethod
    def validate(
        extracted_doc: ExtractedDocument, 
        normalized_text: NormalizedResumeText
    ) -> Tuple[ExtractionQualityStatus, List[ExtractionWarning]]:
        warnings = []
        
        # Check text length
        if extracted_doc.character_count == 0:
            raise ExtractionFailedError("Zero extractable text found in the document.")
            
        if extracted_doc.character_count < ResumeProcessingConfig.MIN_EXTRACTED_TEXT_CHARACTERS:
            warnings.append(
                ExtractionWarning(
                    code=ExtractionWarningCode.LOW_TEXT_CONTENT,
                    message=f"Extracted text character count ({extracted_doc.character_count}) is unusually low.",
                    stage="TEXT_EXTRACTION"
                )
            )

        # Check critical sections
        if "education" not in normalized_text.sections:
            warnings.append(
                ExtractionWarning(
                    code=ExtractionWarningCode.NO_EDUCATION_DETECTED,
                    message="No education section was detected.",
                    stage="NORMALIZATION"
                )
            )
            
        if "experience" not in normalized_text.sections:
            warnings.append(
                ExtractionWarning(
                    code=ExtractionWarningCode.NO_EXPERIENCE_DETECTED,
                    message="No experience section was detected.",
                    stage="NORMALIZATION"
                )
            )

        if "skills" not in normalized_text.sections:
            warnings.append(
                ExtractionWarning(
                    code=ExtractionWarningCode.NO_SKILLS_DETECTED,
                    message="No skills section was detected.",
                    stage="NORMALIZATION"
                )
            )
            
        # Determine status based on warnings
        has_low_text = extracted_doc.character_count < ResumeProcessingConfig.MIN_EXTRACTED_TEXT_CHARACTERS
        missing_sections = sum(1 for sec in ["education", "experience", "skills"] if sec not in normalized_text.sections)
        
        if missing_sections == 3 and has_low_text:
            # All sections missing and practically no text
            status = ExtractionQualityStatus.UNUSABLE
        elif missing_sections > 0 or has_low_text:
            status = ExtractionQualityStatus.PARTIALLY_USABLE
        else:
            status = ExtractionQualityStatus.USABLE
            
        return status, warnings
