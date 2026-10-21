"""Database engine factory supporting SQLite and PostgreSQL.
Provides connection pooling, session makers, table auto-creation, and connection health checks.
"""
import logging
import os
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from src.database.models import Base

logger = logging.getLogger(__name__)


class DatabaseEngineFactory:
    """Manages SQLAlchemy engine lifecycles and creates database sessions."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///database/dataflow.db")
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    def get_engine(self) -> Engine:
        """Lazily initialize and return SQLAlchemy engine with appropriate connection parameters."""
        if self._engine is None:
            connect_args = {}
            if self.database_url.startswith("sqlite"):
                # SQLite specific settings: check_same_thread=False for multi-thread support
                connect_args["check_same_thread"] = False
                # Ensure local directory exists
                db_path = self.database_url.replace("sqlite:///", "")
                if db_path and not db_path.startswith(":memory:"):
                    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

            self._engine = create_engine(
                self.database_url,
                connect_args=connect_args,
                pool_pre_ping=True
            )
            logger.info(f"Initialized database engine for: {self._mask_url(self.database_url)}")

        return self._engine

    def get_session(self) -> Session:
        """Create a new SQLAlchemy ORM session."""
        if self._session_factory is None:
            engine = self.get_engine()
            self._session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        return self._session_factory()

    def create_tables(self) -> None:
        """Automatically create all declared database tables if they do not exist."""
        engine = self.get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Verified/created all declared tables in database.")

    def ping(self) -> bool:
        """Check database reachability via SELECT 1 query."""
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask credentials from connection URL for safe logging."""
        if "@" in url:
            scheme, rest = url.split("://", 1)
            creds, host_part = rest.split("@", 1)
            return f"{scheme}://***:***@{host_part}"
        return url
