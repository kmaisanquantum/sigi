from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings
import os

db_url = os.getenv("DATABASE_URL", get_settings().database_url)

# Render DBs often require SSL
if "render.com" in db_url and "sslmode" not in db_url:
    if "?" in db_url:
        db_url += "&sslmode=require"
    else:
        db_url += "?sslmode=require"

engine_args = {}
if not db_url.startswith("sqlite"):
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20

engine = create_engine(
    db_url,
    echo=get_settings().debug,
    **engine_args
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
