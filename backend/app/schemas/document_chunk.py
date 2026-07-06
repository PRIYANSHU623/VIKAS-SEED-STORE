from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class ChunkResponse(BaseModel):

    id: int

    document_id: int

    chunk_index: int

    chunk_text: str

    embedding_id: str | None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )