from pydantic import BaseModel, ConfigDict
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    uploaded_by: str | None
    file_type: str
    source_type: str | None = "Foreign"
    is_indian: bool | None = False
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)