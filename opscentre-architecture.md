# Deeps Systems — OpsCentre Architecture

## Project Overview
A self-hosted, vendor-neutral security operations platform for Papua New Guinea field operations.
White-label ready. Mobile-first. Data-sovereign.

---

## Recommended Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Backend API** | FastAPI (Python 3.11+) | Async, auto-docs (OpenAPI), lightweight |
| **Frontend** | Vue 3 + Vite + Tailwind CSS | Mobile-responsive, PWA-capable |
| **Database** | PostgreSQL 15 | ACID-compliant, spatial via PostGIS |
| **File Storage** | MinIO (S3-compatible) | Self-hosted, no cloud dependency |
| **Auth** | Keycloak (OIDC) | Role-based, self-hosted SSO |
| **Reverse Proxy** | Nginx | TLS termination, static serving |
| **Container Orchestration** | Docker Compose (prod: Portainer) | Simple on-premise deployment |
| **Background Jobs** | Celery + Redis | Async photo processing, alerts |
| **Monitoring** | Grafana + Prometheus | Infrastructure health dashboards |

---

## Project File Structure

```
deeps-opscentre/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Environment/settings
│   │   ├── database.py              # SQLAlchemy engine + session
│   │   ├── dependencies.py          # Auth, DB session injection
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── patrol_log.py
│   │   │   ├── incident.py
│   │   │   ├── asset.py
│   │   │   └── site.py
│   │   │
│   │   ├── schemas/                 # Pydantic request/response models
│   │   │   ├── patrol_log.py
│   │   │   ├── incident.py
│   │   │   └── asset.py
│   │   │
│   │   ├── routers/                 # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── patrol_logs.py
│   │   │   ├── incidents.py
│   │   │   ├── assets.py
│   │   │   └── dashboard.py
│   │   │
│   │   ├── services/                # Business logic
│   │   │   ├── patrol_service.py
│   │   │   ├── incident_service.py
│   │   │   ├── asset_service.py
│   │   │   └── storage_service.py   # MinIO integration
│   │   │
│   │   └── workers/                 # Celery tasks
│   │       ├── celery_app.py
│   │       └── tasks.py             # Alerts, image processing
│   │
│   ├── alembic/                     # DB migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   ├── stores/                  # Pinia state management
│   │   │   ├── auth.js
│   │   │   ├── incidents.js
│   │   │   └── patrol.js
│   │   │
│   │   ├── views/
│   │   │   ├── Dashboard.vue
│   │   │   ├── PatrolLogs.vue
│   │   │   ├── IncidentReport.vue
│   │   │   ├── AssetHealth.vue
│   │   │   └── Login.vue
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppShell.vue
│   │   │   │   └── MobileNav.vue
│   │   │   ├── incidents/
│   │   │   │   ├── IncidentForm.vue
│   │   │   │   ├── PhotoUploader.vue
│   │   │   │   └── IncidentCard.vue
│   │   │   ├── patrol/
│   │   │   │   ├── CheckInButton.vue
│   │   │   │   └── PatrolMap.vue
│   │   │   └── assets/
│   │   │       ├── AssetStatusCard.vue
│   │   │       └── HealthChart.vue
│   │   │
│   │   └── api/                     # Axios API clients
│   │       ├── incidents.js
│   │       ├── patrol.js
│   │       └── assets.js
│   │
│   ├── public/
│   │   └── manifest.json            # PWA manifest
│   ├── Dockerfile
│   └── vite.config.js
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx/
│   │   └── nginx.conf
│   └── postgres/
│       └── init.sql
│
├── docs/
│   ├── architecture.md
│   ├── deployment-guide.md
│   └── api-reference.md
│
└── .env.example
```

---

## PostgreSQL Database Schema

```sql
-- =============================================================
-- DEEPS SYSTEMS — OPSCENTRE DATABASE SCHEMA
-- PostgreSQL 15 | PostGIS enabled
-- =============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- ─────────────────────────────────────────
-- SITES (client locations / contracts)
-- ─────────────────────────────────────────
CREATE TABLE sites (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(200) NOT NULL,
    client_name     VARCHAR(200) NOT NULL,
    address         TEXT,
    geom            GEOGRAPHY(POINT, 4326),  -- PostGIS spatial point
    timezone        VARCHAR(64) DEFAULT 'Pacific/Port_Moresby',
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- USERS (guards, supervisors, admins)
-- ─────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('guard', 'supervisor', 'admin', 'client_viewer');

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id     VARCHAR(50) UNIQUE NOT NULL,
    full_name       VARCHAR(200) NOT NULL,
    email           VARCHAR(254) UNIQUE,
    phone           VARCHAR(30),
    role            user_role NOT NULL DEFAULT 'guard',
    site_id         UUID REFERENCES sites(id) ON DELETE SET NULL,
    password_hash   TEXT NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    last_seen_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_users_site ON users(site_id);

-- ─────────────────────────────────────────
-- PATROL CHECKPOINTS (predefined stops)
-- ─────────────────────────────────────────
CREATE TABLE patrol_checkpoints (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id     UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    name        VARCHAR(200) NOT NULL,
    geom        GEOGRAPHY(POINT, 4326) NOT NULL,
    qr_code     VARCHAR(128) UNIQUE,        -- for QR-based check-in
    nfc_tag     VARCHAR(128) UNIQUE,        -- for NFC check-in
    active      BOOLEAN DEFAULT TRUE
);

-- ─────────────────────────────────────────
-- PATROL LOGS (GPS check-ins)
-- ─────────────────────────────────────────
CREATE TYPE checkin_method AS ENUM ('gps', 'qr_code', 'nfc', 'manual');

CREATE TABLE patrol_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    guard_id        UUID NOT NULL REFERENCES users(id),
    site_id         UUID NOT NULL REFERENCES sites(id),
    checkpoint_id   UUID REFERENCES patrol_checkpoints(id),
    checked_in_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    geom            GEOGRAPHY(POINT, 4326),  -- actual GPS coords at check-in
    accuracy_m      FLOAT,                  -- GPS accuracy in metres
    method          checkin_method DEFAULT 'gps',
    notes           TEXT,
    shift_id        UUID,                   -- links to a shift session
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_patrol_guard ON patrol_logs(guard_id);
CREATE INDEX idx_patrol_site  ON patrol_logs(site_id);
CREATE INDEX idx_patrol_time  ON patrol_logs(checked_in_at DESC);

-- ─────────────────────────────────────────
-- INCIDENTS
-- ─────────────────────────────────────────
CREATE TYPE incident_severity  AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE incident_status    AS ENUM ('open', 'in_progress', 'resolved', 'closed');
CREATE TYPE incident_category  AS ENUM (
    'theft', 'vandalism', 'trespass', 'medical',
    'fire', 'suspicious_activity', 'equipment_fault',
    'access_breach', 'workplace_injury', 'other'
);

CREATE TABLE incidents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_no    VARCHAR(30) UNIQUE NOT NULL,  -- e.g. INC-20240426-0042
    site_id         UUID NOT NULL REFERENCES sites(id),
    reported_by     UUID NOT NULL REFERENCES users(id),
    assigned_to     UUID REFERENCES users(id),

    title           VARCHAR(300) NOT NULL,
    description     TEXT NOT NULL,
    category        incident_category NOT NULL,
    severity        incident_severity NOT NULL DEFAULT 'medium',
    status          incident_status NOT NULL DEFAULT 'open',

    occurred_at     TIMESTAMPTZ NOT NULL,
    geom            GEOGRAPHY(POINT, 4326),       -- incident location
    location_desc   VARCHAR(500),                 -- human-readable location

    resolved_at     TIMESTAMPTZ,
    resolution_notes TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_incident_site     ON incidents(site_id);
CREATE INDEX idx_incident_status   ON incidents(status);
CREATE INDEX idx_incident_severity ON incidents(severity);
CREATE INDEX idx_incident_time     ON incidents(occurred_at DESC);

-- Auto-increment reference number trigger
CREATE SEQUENCE incident_seq START 1;
CREATE OR REPLACE FUNCTION set_incident_reference()
RETURNS TRIGGER AS $$
BEGIN
    NEW.reference_no := 'INC-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' ||
                        LPAD(nextval('incident_seq')::TEXT, 4, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_incident_reference
    BEFORE INSERT ON incidents
    FOR EACH ROW EXECUTE FUNCTION set_incident_reference();

-- ─────────────────────────────────────────
-- INCIDENT ATTACHMENTS (photos/docs)
-- ─────────────────────────────────────────
CREATE TABLE incident_attachments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id     UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    uploaded_by     UUID NOT NULL REFERENCES users(id),
    filename        VARCHAR(255) NOT NULL,
    storage_key     TEXT NOT NULL,         -- MinIO object path
    mime_type       VARCHAR(100),
    file_size_bytes BIGINT,
    caption         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- NETWORK ASSETS (hardware being monitored)
-- ─────────────────────────────────────────
CREATE TYPE asset_type   AS ENUM ('camera', 'access_point', 'switch', 'nvr', 'server', 'ups', 'sensor', 'other');
CREATE TYPE asset_status AS ENUM ('online', 'offline', 'degraded', 'maintenance', 'decommissioned');

CREATE TABLE assets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id         UUID NOT NULL REFERENCES sites(id),
    asset_tag       VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    type            asset_type NOT NULL,
    manufacturer    VARCHAR(100),
    model           VARCHAR(150),
    serial_number   VARCHAR(150),
    ip_address      INET,
    mac_address     MACADDR,
    firmware_ver    VARCHAR(100),
    geom            GEOGRAPHY(POINT, 4326),
    location_desc   VARCHAR(300),
    status          asset_status DEFAULT 'online',
    last_seen_at    TIMESTAMPTZ,
    installed_at    DATE,
    warranty_expiry DATE,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_asset_site   ON assets(site_id);
CREATE INDEX idx_asset_status ON assets(status);

-- ─────────────────────────────────────────
-- ASSET HEALTH TELEMETRY
-- ─────────────────────────────────────────
CREATE TABLE asset_health_logs (
    id              BIGSERIAL PRIMARY KEY,
    asset_id        UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          asset_status NOT NULL,
    cpu_pct         FLOAT,
    mem_pct         FLOAT,
    disk_pct        FLOAT,
    uptime_seconds  BIGINT,
    ping_ms         FLOAT,
    temperature_c   FLOAT,
    raw_payload     JSONB           -- store full SNMP/API response
);
-- Time-series optimisation
CREATE INDEX idx_health_asset_time ON asset_health_logs(asset_id, recorded_at DESC);
-- Optional: use TimescaleDB hypertable for scale
-- SELECT create_hypertable('asset_health_logs', 'recorded_at');

-- ─────────────────────────────────────────
-- AUDIT LOG (immutable trail)
-- ─────────────────────────────────────────
CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    actor_id    UUID REFERENCES users(id),
    action      VARCHAR(100) NOT NULL,   -- e.g. 'incident.create'
    table_name  VARCHAR(100),
    record_id   UUID,
    before_val  JSONB,
    after_val   JSONB,
    ip_address  INET,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_actor  ON audit_log(actor_id);
CREATE INDEX idx_audit_record ON audit_log(table_name, record_id);
```
