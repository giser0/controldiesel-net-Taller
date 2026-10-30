from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# ¡Nota el "+psycopg2" agregado aquí!
engine = create_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()