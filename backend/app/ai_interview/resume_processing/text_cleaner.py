import re

class TextCleaner:
    @staticmethod
    def clean(raw_text: str) -> str:
        """
        Deterministically cleans resume text.
        Removes weird characters, normalizes spacing, but preserves line breaks.
        """
        # Remove null bytes or non-printable chars
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', raw_text)

        # Normalize carriage returns
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Replace multiple spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)

        # Remove repeated empty lines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Heuristic page number removal like "Page 1 of 2"
        text = re.sub(r'(?i)\bpage \d+ (of \d+)?\b', '', text)

        return text.strip()
