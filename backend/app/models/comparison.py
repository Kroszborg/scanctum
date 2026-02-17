import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class ScanComparison(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scan_comparisons"
    __table_args__ = (
        UniqueConstraint("scan_a_id", "scan_b_id", name="uq_scan_comparison"),
    )

    scan_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False
    )
    scan_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False
    )
    diff_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
