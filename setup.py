from setuptools import setup
setup(
    name="sigi",
    version="0.1",
    py_modules=["backend_incidents"],
    install_requires=[
        "fastapi==0.111.0",
        "uvicorn[standard]==0.29.0",
        "sqlalchemy==2.0.30",
        "alembic==1.13.1",
        "psycopg2-binary==2.9.9",
        "python-multipart==0.0.9",
        "pydantic[email]==2.7.1",
        "pydantic-settings==2.2.1",
        "minio==7.2.7",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "pillow==10.3.0",
        "celery[redis]==5.4.0",
    ],
    entry_points={
        "console_scripts": [
            "build=backend_incidents:app", # Dummy mapping for build script
            "start=backend_incidents:app", # Dummy mapping for start script
        ],
    },
)
