from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class Filter(Base):
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False)
    label = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    default_value = Column(JSON, nullable=True)
    options = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    creator = relationship("User")
