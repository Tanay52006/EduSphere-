from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    status: str
    error_code: str | None
    page_count: int | None
    ocr_required: bool
    job_id: str
    job_status: str
    progress: int
    created_at: datetime
