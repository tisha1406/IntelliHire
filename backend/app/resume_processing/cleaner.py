import re

class ResumeCleaner:
    """
    Cleans and normalizes extracted resume text before passing to the LLM.
    """

    @staticmethod
    def clean_text(raw_text: str) -> str:
        text = raw_text

        # Remove null bytes or non-printable chars
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # Normalize whitespace (replace multiple spaces/newlines with single)
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)

        # Remove very long sequences of special characters (like lines _____________)
        text = re.sub(r'[_=\-]{4,}', '\n', text)

        return text.strip()
