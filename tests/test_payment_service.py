from app.services.payment_service import calculate_payment_decision


def test_partial_approval():
    result = calculate_payment_decision(
        total_verified=500,
        previously_approved=0,
        claimed_quantity=550,
        unit_price=130
    )

    assert result["approved_quantity"] == 500
    assert result["discrepancy_quantity"] == 50
    assert result["potential_overpayment"] == 6500
    assert result["status"] == "PARTIALLY_APPROVED"


def test_full_approval():
    result = calculate_payment_decision(
        total_verified=500,
        previously_approved=0,
        claimed_quantity=400,
        unit_price=130
    )

    assert result["approved_quantity"] == 400
    assert result["discrepancy_quantity"] == 0
    assert result["potential_overpayment"] == 0
    assert result["status"] == "APPROVED"


def test_rejected_when_no_unpaid_verified_work():
    result = calculate_payment_decision(
        total_verified=500,
        previously_approved=500,
        claimed_quantity=100,
        unit_price=130
    )

    assert result["approved_quantity"] == 0
    assert result["discrepancy_quantity"] == 100
    assert result["potential_overpayment"] == 13000
    assert result["status"] == "REJECTED"