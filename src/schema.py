from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime

class Article(BaseModel):
    id: str = Field(..., min_length=1)
    title: str
    summary: str
    source_url: Optional[HttpUrl] = None
    extracted_at: datetime

class ArticleList(BaseModel):
    items: List[Article]
