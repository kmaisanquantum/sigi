from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid
from app.models.incident import IncidentSeverity, IncidentStatus, IncidentCategory

class AttachmentOut(BaseModel):
    id: uuid.UUID
    filename: str
    storage_key: str
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    caption: Optional[str]
    url: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True

class IncidentCreate(BaseModel):
    site_id: uuid.UUID
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10)
    category: IncidentCategory
    severity: IncidentSeverity = IncidentSeverity.medium
    occurred_at: datetime
    location_desc: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[IncidentCategory] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assigned_to: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None

class IncidentOut(BaseModel):
    id: uuid.UUID
    reference_no: str
    site_id: uuid.UUID
    reported_by: uuid.UUID
    title: str
    description: str
    category: IncidentCategory
    severity: IncidentSeverity
    status: IncidentStatus
    occurred_at: datetime
    location_desc: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]
    created_at: datetime
    updated_at: datetime
    attachments: List[AttachmentOut] = []
    class Config: from_attributes = True

class IncidentListOut(BaseModel):
    total: int
    items: List[IncidentOut]
