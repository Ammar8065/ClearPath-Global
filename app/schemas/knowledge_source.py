from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models.knowledge_source import SourceType


class KnowledgeSourceBase(BaseModel):
    jurisdiction: str
    title: str
    url: HttpUrl
    source_type: SourceType


class KnowledgeSourceCreate(KnowledgeSourceBase):
    pass


class KnowledgeSourceRead(KnowledgeSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
