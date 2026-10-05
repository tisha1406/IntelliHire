import re

file_path = 'tests/unit/transport/test_session_creation_service.py'
with open(file_path, 'r') as f:
    text = f.read()

text = text.replace('"company_id": "comp1"}', '"company_id": "comp1", "interview_mode": "m1"}')

with open(file_path, 'w') as f:
    f.write(text)
