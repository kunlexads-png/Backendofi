def test_negative_stock_prevention(client, officer_headers, supervisor_headers, admin_headers):
    # Try to reduce stock without prior balance
    # Supervisor attempting adjustment that leads to negative balance without allow_negative:
    res = client.post(
        "/api/stock/adjust",
        headers=supervisor_headers,
        json={
            "product": "Nibs",
            "module": "BYPRODUCT",
            "batch": "NIB-TEST-99",
            "adjustment_weight": 500.0,
            "adjustment_quantity": 10.0,
            "reason": "Found during physical audit",
            "allow_negative": False
        }
    )
    assert res.status_code == 200

    # Supervisor attempting negative without Admin
    res_neg_fail = client.post(
        "/api/stock/adjust",
        headers=supervisor_headers,
        json={
            "product": "Nibs",
            "module": "BYPRODUCT",
            "batch": "NIB-TEST-99",
            "adjustment_weight": -1000.0,
            "adjustment_quantity": -20.0,
            "reason": "Deficit write-off",
            "allow_negative": True
        }
    )
    assert res_neg_fail.status_code == 403  # Admin required for allow_negative

    # Admin performing with explicit authorization
    res_admin_ok = client.post(
        "/api/stock/adjust",
        headers=admin_headers,
        json={
            "product": "Nibs",
            "module": "BYPRODUCT",
            "batch": "NIB-TEST-99",
            "adjustment_weight": -1000.0,
            "adjustment_quantity": -20.0,
            "reason": "Authorized warehouse deficit adjustment",
            "allow_negative": True
        }
    )
    assert res_admin_ok.status_code == 200
    assert res_admin_ok.json()["data"]["new_balance"] == -500.0
