from datetime import datetime, timedelta

import shortuuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tripweaver.core.db import get_db
from tripweaver.core.deps import get_current_user, get_current_user_id
from tripweaver.domain.schemas.share import (
    CreateShareRequest,
    CreateShareResponse,
    ItineraryDetailResponse,
)
from tripweaver.domain.schemas.vote import VoteRequest, VoteResponse
from tripweaver.models.itinerary import Itinerary, ItineraryMember
from tripweaver.models.share import ShareLink
from tripweaver.models.user import User
from tripweaver.models.vote import Vote

router = APIRouter(prefix="/itinerary", tags=["行程扩展功能"])


@router.post("/share", response_model=CreateShareResponse, summary="生成行程分享链接")
async def create_share_link(
    request: CreateShareRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """生成行程分享短链接"""
    # 校验行程是否存在且是当前用户创建的
    result = await db.execute(
        select(Itinerary).where(
            Itinerary.id == request.itinerary_id,
            Itinerary.creator_id == user.id
        )
    )
    itinerary = result.scalar_one_or_none()
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在或无权限操作"
        )
    
    # 生成短链接ID
    share_id = shortuuid.uuid()[:8].lower()
    
    # 计算过期时间
    expire_at = None
    if request.expire_days > 0:
        expire_at = datetime.utcnow() + timedelta(days=request.expire_days)
    
    # 创建分享链接
    share_link = ShareLink(
        share_id=share_id,
        itinerary_id=request.itinerary_id,
        creator_id=user.id,
        expire_at=expire_at
    )
    
    db.add(share_link)
    await db.commit()
    await db.refresh(share_link)
    
    # 生成分享URL
    share_url = f"/share/{share_id}"
    
    return CreateShareResponse(
        share_id=share_id,
        share_url=share_url,
        expire_at=expire_at,
        created_at=share_link.created_at
    )


@router.get("/share/{share_id}", response_model=ItineraryDetailResponse, summary="通过分享链接获取行程详情")
async def get_itinerary_by_share_id(
    share_id: str,
    req: Request,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """通过分享ID获取行程详情，自动加入行程群组"""
    # 查询分享链接是否有效
    result = await db.execute(
        select(ShareLink).where(
            ShareLink.share_id == share_id,
            ShareLink.is_active.is_(True),
            (ShareLink.expire_at.is_(None)) | (ShareLink.expire_at > datetime.utcnow())
        )
    )
    share_link = result.scalar_one_or_none()
    if not share_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分享链接不存在或已过期"
        )
    
    # 更新访问次数
    share_link.view_count += 1
    await db.commit()
    
    # 查询行程详情
    itinerary = await db.get(Itinerary, share_link.itinerary_id)
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    # 查询创建者信息
    creator = await db.get(User, itinerary.creator_id)
    
    # 自动加入群组（如果还没加入）
    exist_member = await db.execute(
        select(ItineraryMember).where(
            ItineraryMember.itinerary_id == itinerary.id,
            ItineraryMember.user_id == user_id
        )
    )
    if not exist_member.scalar_one_or_none():
        new_member = ItineraryMember(
            itinerary_id=itinerary.id,
            user_id=user_id
        )
        db.add(new_member)
        await db.commit()
    
    # 查询成员列表
    members_result = await db.execute(
        select(ItineraryMember, User.nickname, User.avatar)
        .join(User, ItineraryMember.user_id == User.id)
        .where(ItineraryMember.itinerary_id == itinerary.id)
        .order_by(ItineraryMember.joined_at)
    )
    members = []
    for member, nickname, avatar in members_result.all():
        members.append({
            "user_id": member.user_id,
            "nickname": nickname,
            "avatar": avatar,
            "joined_at": member.joined_at
        })
    
    # 查询投票统计
    vote_stats_result = await db.execute(
        select(Vote.plan_index, func.count(Vote.id).label("count"))
        .where(Vote.itinerary_id == itinerary.id)
        .group_by(Vote.plan_index)
    )
    vote_stats = []
    for plan_index, count in vote_stats_result.all():
        vote_stats.append({
            "plan_index": plan_index,
            "count": count
        })
    
    # 查询当前用户的投票
    current_user_vote = None
    user_vote_result = await db.execute(
        select(Vote.plan_index).where(
            Vote.itinerary_id == itinerary.id,
            Vote.user_id == user_id
        )
    )
    vote = user_vote_result.scalar_one_or_none()
    if vote is not None:
        current_user_vote = vote
    
    return ItineraryDetailResponse(
        itinerary_id=itinerary.id,
        destination=itinerary.destination,
        days=itinerary.days,
        interests=itinerary.interests,
        plan_results=itinerary.plan_results,
        is_locked=itinerary.is_locked,
        locked_at=itinerary.locked_at,
        final_plan_index=itinerary.final_plan_index,
        creator_id=itinerary.creator_id,
        creator_nickname=creator.nickname if creator else "未知用户",
        created_at=itinerary.created_at,
        updated_at=itinerary.updated_at,
        members=members,
        vote_stats=vote_stats,
        current_user_vote=current_user_vote,
        is_creator=itinerary.creator_id == user_id
    )


@router.post("/vote", response_model=VoteResponse, summary="行程方案投票")
async def vote_plan(
    request: VoteRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """为行程方案投票，禁止重复投票"""
    # 查询行程是否存在
    itinerary = await db.get(Itinerary, request.itinerary_id)
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    # 行程已锁定则不允许投票
    if itinerary.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="行程已锁定，无法投票"
        )
    
    # 检查是否已经投过票
    exist_vote = await db.execute(
        select(Vote).where(
            Vote.itinerary_id == request.itinerary_id,
            Vote.user_id == user_id
        )
    )
    if exist_vote.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已经投过票了，无法重复投票"
        )
    
    # 创建投票记录
    # 简单生成用户标识，用于去重
    user_ident = f"{user_id}_{datetime.utcnow().timestamp()}"
    new_vote = Vote(
        itinerary_id=request.itinerary_id,
        user_id=user_id,
        plan_index=request.plan_index,
        user_ident=user_ident
    )
    db.add(new_vote)
    await db.commit()
    
    # 查询最新投票统计
    vote_stats_result = await db.execute(
        select(Vote.plan_index, func.count(Vote.id).label("count"))
        .where(Vote.itinerary_id == request.itinerary_id)
        .group_by(Vote.plan_index)
    )
    vote_stats = []
    for plan_index, count in vote_stats_result.all():
        vote_stats.append({
            "plan_index": plan_index,
            "count": count
        })
    
    return VoteResponse(
        success=True,
        message="投票成功",
        itinerary_id=request.itinerary_id,
        plan_index=request.plan_index,
        vote_stats=vote_stats
    )


@router.post("/lock", summary="发起者锁定/解锁行程")
async def lock_itinerary(
    itinerary_id: int,
    plan_index: int = None,
    action: str = "lock",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发起者锁定行程，确认最终方案；支持重新解锁"""
    # 查询行程是否存在且是当前用户创建的
    itinerary = await db.get(Itinerary, itinerary_id)
    if not itinerary or itinerary.creator_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在或无权限操作"
        )
    
    if action == "lock":
        # 锁定行程
        itinerary.is_locked = True
        itinerary.locked_at = datetime.utcnow()
        if plan_index is not None:
            itinerary.final_plan_index = plan_index
        message = "行程锁定成功"
    elif action == "unlock":
        # 解锁行程
        itinerary.is_locked = False
        itinerary.locked_at = None
        message = "行程解锁成功"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效操作，仅支持lock/unlock"
        )
    
    await db.commit()
    return {
        "success": True,
        "message": message,
        "is_locked": itinerary.is_locked,
        "final_plan_index": itinerary.final_plan_index
    }

