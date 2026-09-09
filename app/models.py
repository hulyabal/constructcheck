from sqlalchemy import Column, Integer, String, Float, ForeignKey

from .database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    location = Column(String, nullable=False)

    client = Column(String, nullable=False)


class BOQItem(Base):
    __tablename__ = "boq_items"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True
    )

    code = Column(String, nullable=False)

    description = Column(String, nullable=False)

    unit = Column(String, nullable=False)

    planned_quantity = Column(Float, nullable=False)

    unit_price = Column(Float, nullable=False)

class ProgressEntry(Base):
    __tablename__ = "progress_entries"

    id = Column(Integer, primary_key=True, index=True)

    boq_item_id = Column(
        Integer,
        ForeignKey("boq_items.id"),
        nullable=False,
        index=True
    )

    date = Column(String, nullable=False)

    verified_quantity = Column(Float, nullable=False)

    notes = Column(String, nullable=True)

class PaymentClaim(Base):
    __tablename__ = "payment_claims"

    id = Column(Integer, primary_key=True, index=True)

    boq_item_id = Column(
        Integer,
        ForeignKey("boq_items.id"),
        nullable=False,
        index=True
    )

    date = Column(String, nullable=False)

    claimed_quantity = Column(Float, nullable=False)

    approved_quantity = Column(Float, nullable=False)

    discrepancy_quantity = Column(Float, nullable=False)

    potential_overpayment = Column(Float, nullable=False)

    status = Column(String, nullable=False)