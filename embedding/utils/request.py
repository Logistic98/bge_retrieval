# -*- coding: utf-8 -*-

from typing import List, Optional
from pydantic import BaseModel


class EmbeddingsRequest(BaseModel):
    input: List[str]
    model: Optional[str] = None
