from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


json_type = JSON().with_variant(JSONB, "postgresql")


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    niche: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    goal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crawl_depth: Mapped[int] = mapped_column(Integer, nullable=False, server_default="200")
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    seo_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    avri_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    pages_crawled: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    meta: Mapped[dict | list | None] = mapped_column(json_type, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    pages: Mapped[list["Page"]] = relationship(back_populates="audit")
    issues: Mapped[list["Issue"]] = relationship(back_populates="audit")
    reports: Mapped[list["Report"]] = relationship(back_populates="audit")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("audits.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    h1: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical: Mapped[str | None] = mapped_column(String(512), nullable=True)
    robots_meta: Mapped[str | None] = mapped_column(String(100), nullable=True)
    json_ld: Mapped[dict | list | None] = mapped_column(json_type, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inlinks_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pagespeed_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_scores: Mapped[dict | list | None] = mapped_column(json_type, nullable=True)
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )

    audit: Mapped[Audit] = relationship(back_populates="pages")
    issues: Mapped[list["Issue"]] = relationship(back_populates="page")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("audits.id"), nullable=False, index=True)
    page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True, index=True)
    rule_id: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(2), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    affected_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    audit: Mapped[Audit] = relationship(back_populates="issues")
    page: Mapped[Page | None] = relationship(back_populates="issues")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("audits.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )

    audit: Mapped[Audit] = relationship(back_populates="reports")
