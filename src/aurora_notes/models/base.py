"""SQLModel base configuration and models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
import os


class Note(SQLModel, table=True):
    """Encrypted note model."""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=255)
    body_enc: bytes  # AES-256-GCM encrypted HTML
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pinned: bool = Field(default=False)
    reminder_at: Optional[datetime] = Field(default=None)
    folder_id: Optional[UUID] = Field(default=None, foreign_key="folder.id")


class Folder(SQLModel, table=True):
    """Note folder/category."""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True)


class Settings(SQLModel, table=True):
    """Encrypted application settings."""
    
    key: str = Field(primary_key=True, max_length=100)
    value_enc: bytes  # Encrypted JSON value


def get_db_path() -> str:
    """Get database path in user's app data directory."""
    if os.name == 'nt':  # Windows
        base = os.environ.get('APPDATA', '.')
    else:  # macOS/Linux
        base = os.path.expanduser('~/.config')
    
    app_dir = os.path.join(base, 'AuroraNotes')
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, 'notes.db')


def create_db_engine():
    """Create SQLAlchemy engine with optimizations."""
    db_path = get_db_path()
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={
            "check_same_thread": False,
            "timeout": 30.0,
        },
        poolclass=StaticPool,
    )
    
    # Apply performance pragmas
    with engine.connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
    
    return engine


def init_db():
    """Initialize database tables."""
    engine = create_db_engine()
    SQLModel.metadata.create_all(engine)
    return engine