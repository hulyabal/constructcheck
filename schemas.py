from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    location: str
    client: str


class ProjectOut(ProjectCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class BOQItemCreate(BaseModel):
    code: str
    description: str
    unit: str
    planned_quantity: float
    unit_price: float


class BOQItemOut(BOQItemCreate):
    id: int
    project_id: int

    model_config = ConfigDict(from_attributes=True)

class ProgressEntryCreate(BaseModel):
    date: str
    verified_quantity: float
    notes: str | None = None


class ProgressEntryOut(ProgressEntryCreate):
    id: int
    boq_item_id: int

    model_config = ConfigDict(from_attributes=True)

class PaymentClaimCreate(BaseModel):
    date: str
    claimed_quantity: float


class PaymentClaimOut(PaymentClaimCreate):
    id: int
    boq_item_id: int
    approved_quantity: float
    discrepancy_quantity: float
    potential_overpayment: float
    status: str

    model_config = ConfigDict(from_attributes=True)
    