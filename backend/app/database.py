from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

engine_kwargs = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def init_db() -> None:
    from app import models  # noqa: F401

    if DATABASE_URL.startswith("postgresql"):
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)

    if DATABASE_URL.startswith("postgresql"):
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE document_jobs ADD COLUMN IF NOT EXISTS result_compliance JSON")
            )

    from app.services.rules_service import seed_default_rules_if_empty

    seed_default_rules_if_empty()
