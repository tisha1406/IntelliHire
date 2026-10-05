from pydantic import BaseModel
from typing import Dict

class M(BaseModel):
    d: Dict[str, str]

M(d={'a': None})
