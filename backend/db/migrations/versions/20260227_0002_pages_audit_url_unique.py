"""add unique constraint for pages(audit_id, url)

Revision ID: 20260227_0002
Revises: 20260226_0001
Create Date: 2026-02-27 15:10:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260227_0002"
down_revision: str | Sequence[str] | None = "20260226_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint("uq_pages_audit_url", "pages", ["audit_id", "url"])


def downgrade() -> None:
    op.drop_constraint("uq_pages_audit_url", "pages", type_="unique")
