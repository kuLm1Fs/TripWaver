from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from tripweaver.core.db import Base


class Vote(Base):
    """投票记录表"""
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"), nullable=False, comment="行程ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="投票用户ID")
    plan_index = Column(Integer, nullable=False, comment="投票选择的方案索引")
    user_ident = Column(String(64), comment="用户唯一标识(IP+UA哈希，用于去重)")
    created_at = Column(DateTime, server_default=func.now(), comment="投票时间")

    itinerary = relationship("Itinerary", back_populates="votes")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        {"comment": "投票记录表"},
    )
