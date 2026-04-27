from sqlalchemy import Column, DateTime, Integer, String, func

from tripweaver.core.db import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone = Column(String(11), unique=True, index=True, nullable=False, comment="手机号")
    nickname = Column(String(50), comment="昵称")
    avatar = Column(String(255), comment="头像地址")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_login_at = Column(DateTime, comment="最后登录时间")
