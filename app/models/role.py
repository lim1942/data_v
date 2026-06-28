from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    permissions = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user_links = relationship("UserRole", back_populates="role")
    dashboard_links = relationship("RoleDashboard", back_populates="role")
