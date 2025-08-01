# -*- coding: utf-8 -*-

from typing import List, Optional
from pydantic import BaseModel


class RerankRequest(BaseModel):
    model: Optional[str] = None
    query: str
    documents: List[str]
    top_n: Optional[int] = None
