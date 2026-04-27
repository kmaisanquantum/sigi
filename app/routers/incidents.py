from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app.config import get_settings
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentOut, IncidentListOut, AttachmentOut
from app.models.incident import Incident, IncidentAttachment, IncidentStatus, IncidentSeverity, IncidentCategory
from app.services.incident_service import create_incident, list_incidents, update_incident
from app.services.storage_service import upload_incident_photo, get_presigned_url
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/incidents", tags=["Incidents"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_FILE_SIZE_MB = 15

@router.post("/", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def create_incident_endpoint(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Submit a new incident report."""
    incident = create_incident(db, payload, current_user.id)
    return _enrich_with_urls(incident, get_settings())

@router.post("/{incident_id}/attachments", response_model=AttachmentOut)
async def upload_attachment(
    incident_id: uuid.UUID,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    settings = Depends(get_settings),
):
    """Upload a photo or document to an existing incident."""
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, f"File type not allowed. Use: {', '.join(ALLOWED_MIME_TYPES)}")

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    result = upload_incident_photo(raw, file.filename, file.content_type, settings)

    attachment = IncidentAttachment(
        incident_id=incident_id,
        uploaded_by=current_user.id,
        filename=file.filename,
        storage_key=result["storage_key"],
        mime_type=file.content_type,
        file_size_bytes=result["file_size_bytes"],
        caption=caption,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return AttachmentOut(
        **attachment.__dict__,
        url=get_presigned_url(attachment.storage_key, settings)
    )

@router.get("/", response_model=IncidentListOut)
def list_incidents_endpoint(
    site_id: Optional[uuid.UUID] = Query(None),
    status: Optional[IncidentStatus] = Query(None),
    severity: Optional[IncidentSeverity] = Query(None),
    category: Optional[IncidentCategory] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    total, items = list_incidents(db, site_id, status, severity, category, skip=skip, limit=limit)
    settings = get_settings()
    return IncidentListOut(total=total, items=[_enrich_with_urls(i, settings) for i in items])

@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return _enrich_with_urls(incident, get_settings())

@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident_endpoint(
    incident_id: uuid.UUID,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    incident = update_incident(db, incident_id, payload)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return _enrich_with_urls(incident, get_settings())

def _enrich_with_urls(incident: Incident, settings) -> IncidentOut:
    """Attach pre-signed URLs to attachment objects."""
    out = IncidentOut.model_validate(incident)
    out.attachments = [
        AttachmentOut(
            **a.__dict__,
            url=get_presigned_url(a.storage_key, settings)
        )
        for a in incident.attachments
    ]
    return out
