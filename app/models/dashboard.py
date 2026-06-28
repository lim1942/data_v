from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Dashboard(Base):
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    layout_config = Column(JSON, default=list, nullable=False)
    global_filters = Column(JSON, default=list, nullable=False)
    filter_ids = Column(JSON, nullable=True, default=None)
    is_published = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    creator = relationship("User")
    role_links = relationship("RoleDashboard", back_populates="dashboard")


class RoleDashboard(Base):
    __tablename__ = "role_dashboards"
    __table_args__ = (UniqueConstraint("role_id", "dashboard_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"), nullable=False)
    can_view = Column(Boolean, default=True, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)

    role = relationship("Role", back_populates="dashboard_links")
    dashboard = relationship("Dashboard", back_populates="role_links")
