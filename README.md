# ConstructCheck

ConstructCheck is a construction progress and payment verification web application developed with Python and FastAPI.

The project combines my Civil Engineering background with my current Computer Science studies. It is designed around a real construction business problem: comparing contractor payment claims with verified site progress in order to detect quantity discrepancies and potential overpayments.

## Business Problem

In construction projects, contractors periodically submit payment claims based on completed work.

However, the claimed quantity may be higher than the quantity actually verified on site.

For example:

- Planned concrete quantity: 1,200 m³
- Verified quantity: 500 m³
- Contractor claim: 550 m³
- Unit price: €130/m³

ConstructCheck automatically calculates:

- Approved quantity: 500 m³
- Discrepancy: 50 m³
- Potential overpayment: €6,500
- Claim status: `PARTIALLY_APPROVED`

This helps project managers and site engineers identify inconsistencies before approving payments.

---

## Features

### Project Management

Users can create and retrieve construction projects.

Each project contains information such as:

- Project name
- Location
- Client

---

### Bill of Quantities (BOQ)

Each project can contain multiple BOQ items.

A BOQ item includes:

- Item code
- Description
- Unit
- Planned quantity
- Unit price

Example:

| Code | Description | Unit | Planned Quantity | Unit Price |
|---|---|---|---:|---:|
| C-001 | Concrete C30/37 | m³ | 1200 | €130 |
| R-001 | Reinforcement Steel | t | 150 | €1200 |
| F-001 | Formwork | m² | 8000 | €35 |

---

### CSV BOQ Import

BOQ data can also be imported directly from a CSV file instead of entering each item manually.

Expected CSV format:

```csv
code,description,unit,planned_quantity,unit_price
EX-001,Excavation,m3,2500,18
C-002,Concrete C25/30,m3,900,120
R-002,Reinforcement Steel,t,110,1180
F-002,Formwork,m2,6200,32
M-002,Masonry,m2,2800,42
