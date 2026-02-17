import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class Vulnerability(UUIDMixin, Base):
    __tablename__ = "vulnerabilities"
    __table_args__ = (
        # Composite index for common queries
    )

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    vuln_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    cvss_score: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False, default=0.0)
    cvss_vector: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    owasp_category: Mapped[str] = mapped_column(String(10), nullable=False, default="", index=True)
    cwe_id: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    affected_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    affected_parameter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[str] = mapped_column(String(10), nullable=False, default="firm")
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    scan: Mapped["Scan"] = relationship(back_populates="vulnerabilities")
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="vulnerability", cascade="all, delete-orphan", lazy="selectin"
    )


class Evidence(UUIDMixin, Base):
    __tablename__ = "evidence"

    vulnerability_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vulnerabilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(SmallInteger, default=0)

    vulnerability: Mapped["Vulnerability"] = relationship(back_populates="evidence")
