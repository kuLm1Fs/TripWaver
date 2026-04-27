"""初始表结构

Revision ID: e53602af1ab9
Revises:
Create Date: 2026-04-27 16:14:52.206754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e53602af1ab9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("phone", sa.String(11), nullable=False, comment="手机号"),
        sa.Column("nickname", sa.String(50), comment="昵称"),
        sa.Column("avatar", sa.String(255), comment="头像地址"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), comment="更新时间"),
        sa.Column("last_login_at", sa.DateTime(), comment="最后登录时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)

    # itineraries
    op.create_table(
        "itineraries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, comment="创建者用户ID"),
        sa.Column("destination", sa.String(100), nullable=False, comment="目的地"),
        sa.Column("days", sa.Integer(), server_default="1", comment="游玩天数"),
        sa.Column("interests", sa.JSON(), comment="兴趣标签"),
        sa.Column("user_params", sa.JSON(), comment="用户额外参数"),
        sa.Column("plan_results", sa.JSON(), comment="生成的多路线方案结果"),
        sa.Column("final_plan_index", sa.Integer(), comment="最终确认的方案索引"),
        sa.Column("is_locked", sa.Boolean(), server_default="false", comment="是否已锁定"),
        sa.Column("locked_at", sa.DateTime(), comment="锁定时间"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_itineraries_id", "itineraries", ["id"])

    # itinerary_members
    op.create_table(
        "itinerary_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("itinerary_id", sa.Integer(), sa.ForeignKey("itineraries.id"), nullable=False, comment="行程ID"),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, comment="用户ID"),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now(), comment="加入时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_itinerary_members_id", "itinerary_members", ["id"])

    # share_links
    op.create_table(
        "share_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("share_id", sa.String(16), nullable=False, comment="短链接ID"),
        sa.Column("itinerary_id", sa.Integer(), sa.ForeignKey("itineraries.id"), nullable=False, comment="行程ID"),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, comment="创建者ID"),
        sa.Column("expire_at", sa.DateTime(), comment="过期时间，为空则永久有效"),
        sa.Column("view_count", sa.Integer(), server_default="0", comment="访问次数"),
        sa.Column("is_active", sa.Boolean(), server_default="true", comment="是否有效"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_share_links_id", "share_links", ["id"])
    op.create_index("ix_share_links_share_id", "share_links", ["share_id"], unique=True)

    # votes
    op.create_table(
        "votes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("itinerary_id", sa.Integer(), sa.ForeignKey("itineraries.id"), nullable=False, comment="行程ID"),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, comment="投票用户ID"),
        sa.Column("plan_index", sa.Integer(), nullable=False, comment="投票选择的方案索引"),
        sa.Column("user_ident", sa.String(64), comment="用户唯一标识"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), comment="投票时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_votes_id", "votes", ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("votes")
    op.drop_table("share_links")
    op.drop_table("itinerary_members")
    op.drop_table("itineraries")
    op.drop_table("users")
