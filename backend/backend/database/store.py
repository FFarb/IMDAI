"""Database models for the POD Merch Swarm."""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "pod_swarm.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Strategy(Base):
    """Stores the JSON logic from Agent-Analyst."""
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)  # e.g., "Retro Sunset Cat"
    data_json: Mapped[str] = mapped_column(Text)  # JSON string of the strategy
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    embedding_id: Mapped[str | None] = mapped_column(String, nullable=True)  # ID in ChromaDB

    generations = relationship("Generation", back_populates="strategy")

    def set_data(self, data: dict[str, Any]):
        self.data_json = json.dumps(data)

    def get_data(self) -> dict[str, Any]:
        return json.loads(self.data_json) if self.data_json else {}


class Generation(Base):
    """Stores specific image runs."""
    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    strategy_id: Mapped[int] = mapped_column(Integer, ForeignKey("strategies.id"))
    prompt_text: Mapped[str] = mapped_column(Text)
    image_path: Mapped[str] = mapped_column(String)  # Local path (empty until saved to library)
    rating: Mapped[int] = mapped_column(Integer, default=0)  # 0-5
    actions_taken: Mapped[str] = mapped_column(String, default="")  # Comma-separated: "upscaled,vectorized"
    metadata_json_str: Mapped[str] = mapped_column(Text, default="{}")  # JSON metadata including base64 image

    strategy = relationship("Strategy", back_populates="generations")

    def add_action(self, action: str):
        current = self.actions_taken.split(",") if self.actions_taken else []
        if action not in current:
            current.append(action)
            self.actions_taken = ",".join(current)
    
    @property
    def metadata_json(self) -> dict[str, Any]:
        """Get metadata as dict."""
        return json.loads(self.metadata_json_str) if self.metadata_json_str else {}
    
    @metadata_json.setter
    def metadata_json(self, value: dict[str, Any]):
        """Set metadata from dict."""
        self.metadata_json_str = json.dumps(value)


def init_db():
    """Initialize the database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
