import re

class ResumeCleaner:
    """
    Cleans and normalizes extracted resume text.
    """

    @staticmethod
    def clean_text(raw_text: str) -> str:
        if not raw_text:
            return ""

        # 1. Normalize line endings
        text = raw_text.replace('\r\n', '\n').replace('\r', '\n')

        # 2. Remove null/control characters (except \n and \t)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

        # 3. Strip each line and normalize repeated spaces
        lines = []
        for line in text.split('\n'):
            # Normalize spaces/tabs
            clean_line = re.sub(r'[ \t]+', ' ', line)
            clean_line = clean_line.strip()
            lines.append(clean_line)
            
        text = '\n'.join(lines)

        # 4. Collapse excessive blank lines (more than 2 consecutive newlines)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()
