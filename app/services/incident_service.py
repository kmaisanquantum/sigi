from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Tuple
from datetime import datetime, date
import uuid

from app.models.incident import Incident, IncidentStatus, IncidentSeverity, IncidentCategory
from app.schemas.incident import IncidentCreate, IncidentUpdate

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
) -> Tuple[int, List[Incident]]:
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
