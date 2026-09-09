def calculate_payment_decision(
    total_verified: float,
    previously_approved: float,
    claimed_quantity: float,
    unit_price: float
):
    available_verified = max(
        total_verified - previously_approved,
        0
    )

    approved_quantity = min(
        claimed_quantity,
        available_verified
    )

    discrepancy_quantity = (
        claimed_quantity - approved_quantity
    )

    potential_overpayment = (
        discrepancy_quantity * unit_price
    )

    if approved_quantity == 0:
        status = "REJECTED"

    elif discrepancy_quantity > 0:
        status = "PARTIALLY_APPROVED"

    else:
        status = "APPROVED"

    return {
        "approved_quantity": approved_quantity,
        "discrepancy_quantity": discrepancy_quantity,
        "potential_overpayment": potential_overpayment,
        "status": status
    }