"""initial foundation schema

Revision ID: 20260226_0001
Revises:
Create Date: 2026-02-26 13:20:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260226_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=True),
        sa.Column("niche", sa.String(length=255), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("goal", sa.String(length=50), nullable=True),
        sa.Column("crawl_depth", sa.Integer(), nullable=False, server_default=sa.text("200")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("seo_score", sa.Float(), nullable=True),
        sa.Column("avri_score", sa.Float(), nullable=True),
        sa.Column("pages_crawled", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "pages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("audit_id", sa.Integer(), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("h1", sa.Text(), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("canonical", sa.String(length=512), nullable=True),
        sa.Column("robots_meta", sa.String(length=100), nullable=True),
        sa.Column("json_ld", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("inlinks_count", sa.Integer(), nullable=True),
        sa.Column("pagespeed_score", sa.Float(), nullable=True),
        sa.Column("ai_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("crawled_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pages_audit_id", "pages", ["audit_id"])

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("audit_id", sa.Integer(), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column("page_id", sa.Integer(), sa.ForeignKey("pages.id"), nullable=True),
        sa.Column("rule_id", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=2), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("affected_url", sa.String(length=512), nullable=True),
    )
    op.create_index("ix_issues_audit_id", "issues", ["audit_id"])
    op.create_index("ix_issues_page_id", "issues", ["page_id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("audit_id", sa.Integer(), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reports_audit_id", "reports", ["audit_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_audit_id", table_name="reports")
    op.drop_table("reports")

    op.drop_index("ix_issues_page_id", table_name="issues")
    op.drop_index("ix_issues_audit_id", table_name="issues")
    op.drop_table("issues")

    op.drop_index("ix_pages_audit_id", table_name="pages")
    op.drop_table("pages")

    op.drop_table("audits")
