"""
Deeps Systems — OpsCentre Backend
Incident Reporting Module
FastAPI + SQLAlchemy + MinIO
"""

# ─── requirements.txt ────────────────────────────────────────────────────────
# fastapi==0.111.0
# uvicorn[standard]==0.29.0
# sqlalchemy==2.0.30
# alembic==1.13.1
# psycopg2-binary==2.9.9
# python-multipart==0.0.9
# pydantic[email]==2.7.1
# pydantic-settings==2.2.1
# minio==7.2.7
# python-jose[cryptography]==3.3.0
# passlib[bcrypt]==1.7.4
# pillow==10.3.0
# celery[redis]==5.4.0

# ─── app/config.py ───────────────────────────────────────────────────────────
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Deeps Systems OpsCentre"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://opscentre:secret@localhost:5432/opscentre"

    # JWT
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_USE_256BIT_RANDOM"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8h shift coverage

    # MinIO (local S3-compatible storage)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "opscentre-media"
    minio_secure: bool = False

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()


# ─── app/database.py ─────────────────────────────────────────────────────────
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_engine(
    get_settings().database_url,
    pool_size=10,
    max_overflow=20,
    echo=get_settings().debug,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── app/models/incident.py ──────────────────────────────────────────────────
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Enum, DateTime, ForeignKey,
    BigInteger, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum as pyenum

class IncidentSeverity(str, pyenum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IncidentStatus(str, pyenum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class IncidentCategory(str, pyenum.Enum):
    theft = "theft"
    vandalism = "vandalism"
    trespass = "trespass"
    medical = "medical"
    fire = "fire"
    suspicious_activity = "suspicious_activity"
    equipment_fault = "equipment_fault"
    access_breach = "access_breach"
    workplace_injury = "workplace_injury"
    other = "other"

class Incident(Base):
    __tablename__ = "incidents"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_no   = Column(String(30), unique=True, nullable=False)
    site_id        = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    reported_by    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    title          = Column(String(300), nullable=False)
    description    = Column(Text, nullable=False)
    category       = Column(Enum(IncidentCategory), nullable=False)
    severity       = Column(Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.medium)
    status         = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.open)

    occurred_at    = Column(DateTime(timezone=True), nullable=False)
    location_desc  = Column(String(500))
    latitude       = Column(String(20))   # stored as string to avoid float precision issues
    longitude      = Column(String(20))

    resolved_at    = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)

    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    attachments    = relationship("IncidentAttachment", back_populates="incident", cascade="all, delete-orphan")

class IncidentAttachment(Base):
    __tablename__ = "incident_attachments"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id   = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    uploaded_by   = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename      = Column(String(255), nullable=False)
    storage_key   = Column(Text, nullable=False)
    mime_type     = Column(String(100))
    file_size_bytes = Column(BigInteger)
    caption       = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident", back_populates="attachments")


# ─── app/schemas/incident.py ─────────────────────────────────────────────────
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class AttachmentOut(BaseModel):
    id: uuid.UUID
    filename: str
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    caption: Optional[str]
    url: str                    # pre-signed MinIO URL
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


# ─── app/services/storage_service.py ─────────────────────────────────────────
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
import io, uuid
from PIL import Image

def get_minio_client(settings) -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )

def ensure_bucket(client: Minio, bucket: str):
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

def upload_incident_photo(
    file_bytes: bytes,
    original_filename: str,
    mime_type: str,
    settings,
    max_dimension: int = 2048,
) -> dict:
    """
    Compress, strip EXIF (privacy), upload to MinIO.
    Returns storage key + file size.
    """
    client = get_minio_client(settings)
    ensure_bucket(client, settings.minio_bucket)

    # Resize and strip EXIF for privacy / bandwidth
    img = Image.open(io.BytesIO(file_bytes))
    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
    # Strip EXIF by re-saving without it
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))

    buf = io.BytesIO()
    fmt = "JPEG" if mime_type == "image/jpeg" else "PNG"
    clean.save(buf, format=fmt, optimize=True, quality=82)
    buf.seek(0)
    processed = buf.read()

    storage_key = f"incidents/{uuid.uuid4()}/{original_filename}"
    client.put_object(
        settings.minio_bucket,
        storage_key,
        io.BytesIO(processed),
        length=len(processed),
        content_type=mime_type,
    )
    return {"storage_key": storage_key, "file_size_bytes": len(processed)}

def get_presigned_url(storage_key: str, settings, expires_hours: int = 4) -> str:
    client = get_minio_client(settings)
    return client.presigned_get_object(
        settings.minio_bucket,
        storage_key,
        expires=timedelta(hours=expires_hours),
    )


# ─── app/services/incident_service.py ────────────────────────────────────────
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import Optional
from datetime import datetime, date
import uuid

def generate_reference(db: Session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"INC-{today}-"
    count = db.query(Incident).filter(
        Incident.reference_no.like(f"{prefix}%")
    ).count()
    return f"{prefix}{str(count + 1).zfill(4)}"

def create_incident(db: Session, payload: IncidentCreate, reporter_id: uuid.UUID) -> Incident:
    incident = Incident(
        reference_no=generate_reference(db),
        reported_by=reporter_id,
        **payload.model_dump()
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident

def list_incidents(
    db: Session,
    site_id: Optional[uuid.UUID] = None,
    status: Optional[IncidentStatus] = None,
    severity: Optional[IncidentSeverity] = None,
    category: Optional[IncidentCategory] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
):
    q = db.query(Incident)
    if site_id:   q = q.filter(Incident.site_id == site_id)
    if status:    q = q.filter(Incident.status == status)
    if severity:  q = q.filter(Incident.severity == severity)
    if category:  q = q.filter(Incident.category == category)
    if date_from: q = q.filter(Incident.occurred_at >= date_from)
    if date_to:   q = q.filter(Incident.occurred_at <= date_to)
    total = q.count()
    items = q.order_by(desc(Incident.occurred_at)).offset(skip).limit(limit).all()
    return total, items

def update_incident(db: Session, incident_id: uuid.UUID, payload: IncidentUpdate) -> Optional[Incident]:
    incident = db.get(Incident, incident_id)
    if not incident:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    if payload.status == IncidentStatus.resolved and not incident.resolved_at:
        incident.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    return incident


# ─── app/routers/incidents.py ─────────────────────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

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


# ─── app/main.py ─────────────────────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Deeps Systems OpsCentre API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue dev server; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)  # incidents router

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
