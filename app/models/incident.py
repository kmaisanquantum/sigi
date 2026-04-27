import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Float, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base

class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IncidentStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class IncidentCategory(str, enum.Enum):
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_no = Column(String(30), unique=True, nullable=False)
    site_id = Column(UUID(as_uuid=True), nullable=False)
    reported_by = Column(UUID(as_uuid=True), nullable=False)
    assigned_to = Column(UUID(as_uuid=True))

    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(IncidentCategory), nullable=False)
    severity = Column(SQLEnum(IncidentSeverity), nullable=False, default=IncidentSeverity.medium)
    status = Column(SQLEnum(IncidentStatus), nullable=False, default=IncidentStatus.open)

    occurred_at = Column(DateTime(timezone=True), nullable=False)
    location_desc = Column(String(500))
    latitude = Column(String(50))
    longitude = Column(String(50))

    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    attachments = relationship("IncidentAttachment", back_populates="incident", cascade="all, delete-orphan")

class IncidentAttachment(Base):
    __tablename__ = "incident_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_key = Column(Text, nullable=False)
    mime_type = Column(String(100))
    file_size_bytes = Column(BigInteger)
    caption = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    incident = relationship("Incident", back_populates="attachments")
