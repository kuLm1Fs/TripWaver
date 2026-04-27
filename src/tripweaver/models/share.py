from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from tripweaver.core.db import Base


class ShareLink(Base):
    """分享链接表"""
    __tablename__ = "share_links"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    share_id = Column(String(16), unique=True, index=True, nullable=False, comment="短链接ID")
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"), nullable=False, comment="行程ID")
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")
    expire_at = Column(DateTime, comment="过期时间，为空则永久有效")
    view_count = Column(Integer, default=0, comment="访问次数")
    is_active = Column(Boolean, default=True, comment="是否有效")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    itinerary = relationship("Itinerary", back_populates="share_links")
    creator = relationship("User", foreign_keys=[creator_id])
