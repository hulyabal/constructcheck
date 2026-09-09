from io import StringIO

import pandas as pd

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .services.payment_service import calculate_payment_decision


# Create database tables
models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="ConstructCheck",
    description="Construction Progress and Payment Verification System",
    version="0.1.0"
)


# Serve frontend files
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "ConstructCheck API is running"
    }


# --------------------------------------------------
# PROJECTS
# --------------------------------------------------

@app.post(
    "/projects",
    response_model=schemas.ProjectOut
)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db)
):
    new_project = models.Project(
        name=project.name,
        location=project.location,
        client=project.client
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@app.get(
    "/projects",
    response_model=list[schemas.ProjectOut]
)
def get_projects(
    db: Session = Depends(get_db)
):
    return db.query(models.Project).all()


# --------------------------------------------------
# BOQ
# --------------------------------------------------

@app.post(
    "/projects/{project_id}/boq",
    response_model=schemas.BOQItemOut
)
def create_boq_item(
    project_id: int,
    item: schemas.BOQItemCreate,
    db: Session = Depends(get_db)
):
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    new_item = models.BOQItem(
        project_id=project_id,
        code=item.code,
        description=item.description,
        unit=item.unit,
        planned_quantity=item.planned_quantity,
        unit_price=item.unit_price
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


@app.get(
    "/projects/{project_id}/boq",
    response_model=list[schemas.BOQItemOut]
)
def get_boq_items(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return (
        db.query(models.BOQItem)
        .filter(models.BOQItem.project_id == project_id)
        .all()
    )


# --------------------------------------------------
# CSV BOQ IMPORT
# --------------------------------------------------

@app.post("/projects/{project_id}/boq/import-csv")
async def import_boq_csv(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed"
        )

    contents = await file.read()

    try:
        text = contents.decode("utf-8-sig")
        df = pd.read_csv(StringIO(text))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read CSV file"
        )

    required_columns = {
        "code",
        "description",
        "unit",
        "planned_quantity",
        "unit_price"
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing columns: {sorted(missing_columns)}"
        )

    try:
        df["planned_quantity"] = pd.to_numeric(
            df["planned_quantity"]
        )

        df["unit_price"] = pd.to_numeric(
            df["unit_price"]
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Quantity and unit price must be numeric"
        )

    imported_count = 0
    skipped_codes = []

    for _, row in df.iterrows():

        code = str(row["code"])

        existing_item = (
            db.query(models.BOQItem)
            .filter(
                models.BOQItem.project_id == project_id,
                models.BOQItem.code == code
            )
            .first()
        )

        if existing_item:
            skipped_codes.append(code)
            continue

        new_item = models.BOQItem(
            project_id=project_id,
            code=code,
            description=str(row["description"]),
            unit=str(row["unit"]),
            planned_quantity=float(
                row["planned_quantity"]
            ),
            unit_price=float(
                row["unit_price"]
            )
        )

        db.add(new_item)
        imported_count += 1

    db.commit()

    return {
        "message": "BOQ import completed",
        "imported_count": imported_count,
        "skipped_duplicate_codes": skipped_codes
    }


# --------------------------------------------------
# SITE PROGRESS
# --------------------------------------------------

@app.post(
    "/boq/{boq_item_id}/progress",
    response_model=schemas.ProgressEntryOut
)
def create_progress_entry(
    boq_item_id: int,
    progress: schemas.ProgressEntryCreate,
    db: Session = Depends(get_db)
):
    boq_item = (
        db.query(models.BOQItem)
        .filter(models.BOQItem.id == boq_item_id)
        .first()
    )

    if boq_item is None:
        raise HTTPException(
            status_code=404,
            detail="BOQ item not found"
        )

    if progress.verified_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Verified quantity must be greater than zero"
        )

    previous_entries = (
        db.query(models.ProgressEntry)
        .filter(
            models.ProgressEntry.boq_item_id
            == boq_item_id
        )
        .all()
    )

    previous_verified = sum(
        entry.verified_quantity
        for entry in previous_entries
    )

    new_total = (
        previous_verified
        + progress.verified_quantity
    )

    if new_total > boq_item.planned_quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                "Total verified quantity cannot exceed "
                f"planned quantity "
                f"({boq_item.planned_quantity})"
            )
        )

    new_entry = models.ProgressEntry(
        boq_item_id=boq_item_id,
        date=progress.date,
        verified_quantity=progress.verified_quantity,
        notes=progress.notes
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return new_entry


@app.get(
    "/boq/{boq_item_id}/progress",
    response_model=list[schemas.ProgressEntryOut]
)
def get_progress_entries(
    boq_item_id: int,
    db: Session = Depends(get_db)
):
    boq_item = (
        db.query(models.BOQItem)
        .filter(models.BOQItem.id == boq_item_id)
        .first()
    )

    if boq_item is None:
        raise HTTPException(
            status_code=404,
            detail="BOQ item not found"
        )

    return (
        db.query(models.ProgressEntry)
        .filter(
            models.ProgressEntry.boq_item_id
            == boq_item_id
        )
        .all()
    )


# --------------------------------------------------
# PAYMENT CLAIMS
# --------------------------------------------------

@app.post(
    "/boq/{boq_item_id}/claims",
    response_model=schemas.PaymentClaimOut
)
def create_payment_claim(
    boq_item_id: int,
    claim: schemas.PaymentClaimCreate,
    db: Session = Depends(get_db)
):
    boq_item = (
        db.query(models.BOQItem)
        .filter(models.BOQItem.id == boq_item_id)
        .first()
    )

    if boq_item is None:
        raise HTTPException(
            status_code=404,
            detail="BOQ item not found"
        )

    if claim.claimed_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Claimed quantity must be greater than zero"
        )

    # Total verified construction work
    progress_entries = (
        db.query(models.ProgressEntry)
        .filter(
            models.ProgressEntry.boq_item_id
            == boq_item_id
        )
        .all()
    )

    total_verified = sum(
        entry.verified_quantity
        for entry in progress_entries
    )

    # Quantities already approved before
    previous_claims = (
        db.query(models.PaymentClaim)
        .filter(
            models.PaymentClaim.boq_item_id
            == boq_item_id
        )
        .all()
    )

    previously_approved = sum(
        previous.approved_quantity
        for previous in previous_claims
    )

    # Business logic is handled by service
    decision = calculate_payment_decision(
        total_verified=total_verified,
        previously_approved=previously_approved,
        claimed_quantity=claim.claimed_quantity,
        unit_price=boq_item.unit_price
    )

    new_claim = models.PaymentClaim(
        boq_item_id=boq_item_id,
        date=claim.date,
        claimed_quantity=claim.claimed_quantity,
        approved_quantity=decision[
            "approved_quantity"
        ],
        discrepancy_quantity=decision[
            "discrepancy_quantity"
        ],
        potential_overpayment=decision[
            "potential_overpayment"
        ],
        status=decision["status"]
    )

    db.add(new_claim)
    db.commit()
    db.refresh(new_claim)

    return new_claim


@app.get(
    "/boq/{boq_item_id}/claims",
    response_model=list[schemas.PaymentClaimOut]
)
def get_payment_claims(
    boq_item_id: int,
    db: Session = Depends(get_db)
):
    boq_item = (
        db.query(models.BOQItem)
        .filter(models.BOQItem.id == boq_item_id)
        .first()
    )

    if boq_item is None:
        raise HTTPException(
            status_code=404,
            detail="BOQ item not found"
        )

    return (
        db.query(models.PaymentClaim)
        .filter(
            models.PaymentClaim.boq_item_id
            == boq_item_id
        )
        .all()
    )


# --------------------------------------------------
# PROJECT SUMMARY
# --------------------------------------------------

@app.get("/projects/{project_id}/summary")
def get_project_summary(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    boq_items = (
        db.query(models.BOQItem)
        .filter(
            models.BOQItem.project_id
            == project_id
        )
        .all()
    )

    total_budget = 0
    total_verified_value = 0
    total_approved_payment = 0
    total_potential_overpayment = 0

    for item in boq_items:

        # Total project budget
        item_budget = (
            item.planned_quantity
            * item.unit_price
        )

        total_budget += item_budget

        # Verified work
        progress_entries = (
            db.query(models.ProgressEntry)
            .filter(
                models.ProgressEntry.boq_item_id
                == item.id
            )
            .all()
        )

        verified_quantity = sum(
            entry.verified_quantity
            for entry in progress_entries
        )

        total_verified_value += (
            verified_quantity
            * item.unit_price
        )

        # Payment claims
        claims = (
            db.query(models.PaymentClaim)
            .filter(
                models.PaymentClaim.boq_item_id
                == item.id
            )
            .all()
        )

        total_approved_payment += sum(
            claim.approved_quantity
            * item.unit_price
            for claim in claims
        )

        total_potential_overpayment += sum(
            claim.potential_overpayment
            for claim in claims
        )

    if total_budget > 0:
        progress_percentage = (
            total_verified_value
            / total_budget
        ) * 100
    else:
        progress_percentage = 0

    return {
        "project_id": project.id,
        "project_name": project.name,

        "total_budget": round(
            total_budget,
            2
        ),

        "verified_work_value": round(
            total_verified_value,
            2
        ),

        "approved_payments": round(
            total_approved_payment,
            2
        ),

        "potential_overpayment": round(
            total_potential_overpayment,
            2
        ),

        "progress_percentage": round(
            progress_percentage,
            2
        )
    }


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.get("/dashboard")
def dashboard():
    return FileResponse(
        "app/static/index.html"
    )