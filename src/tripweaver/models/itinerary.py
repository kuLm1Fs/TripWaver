from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from tripweaver.core.db import Base


class Itinerary(Base):
    """行程表"""
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者用户ID")
    destination = Column(String(100), nullable=False, comment="目的地")
    days = Column(Integer, default=1, comment="游玩天数")
    interests = Column(JSON, default=list, comment="兴趣标签")
    user_params = Column(JSON, default=dict, comment="用户额外参数")
    plan_results = Column(JSON, comment="生成的多路线方案结果")
    final_plan_index = Column(Integer, comment="最终确认的方案索引")
    is_locked = Column(Boolean, default=False, comment="是否已锁定")
    locked_at = Column(DateTime, comment="锁定时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    creator = relationship("User", foreign_keys=[creator_id])
    share_links = relationship("ShareLink", back_populates="itinerary")
    votes = relationship("Vote", back_populates="itinerary")
    members = relationship("ItineraryMember", back_populates="itinerary")


class ItineraryMember(Base):
    """行程群组成员表"""
    __tablename__ = "itinerary_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"), nullable=False, comment="行程ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    joined_at = Column(DateTime, server_default=func.now(), comment="加入时间")

    itinerary = relationship("Itinerary", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        {"comment": "行程群组成员表"},
    )
