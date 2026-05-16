"""Setup de SQLAlchemy + sesión global."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency injection para FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea todas las tablas. Llamado al arrancar el servidor."""
    # Importar modelos para que SQLAlchemy los registre
    from src.models import user, fragment  # noqa: F401
    Base.metadata.create_all(bind=engine)
