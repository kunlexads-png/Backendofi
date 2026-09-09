from datetime import date


def test_byproduct_flow(client, officer_headers, supervisor_headers):
    # 1. Add Dust byproduct
    payload = {
        "date": str(date.today()),
        "product": "Dust",
        "quantity": 25.0,
        "weight": 1250.0,
        "batch_number": "BP-DST-001",
        "source": "Winnowing Cyclone",
        "warehouse_location": "Shed 3 By-products",
        "status": "Available"
    }
    create_res = client.post("/api/byproducts", headers=officer_headers, json=payload)
    assert create_res.status_code == 201
    bp_id = create_res.json()["data"]["id"]

    # 2. Check byproducts balance
    balance_res = client.get("/api/byproducts/balance", headers=supervisor_headers)
    assert balance_res.status_code == 200
    assert balance_res.json()["data"]["balances"]["Dust"] == 1250.0

    # 3. Dispose part of the Dust material
    dispose_res = client.post(
        f"/api/byproducts/{bp_id}/dispose",
        headers=supervisor_headers,
        json={
            "quantity": 5.0,
            "weight": 250.0,
            "reason": "Water moisture contamination in cyclone bin"
        }
    )
    assert dispose_res.status_code == 200

    # 4. Check balance decreased
    balance_after = client.get("/api/byproducts/balance", headers=supervisor_headers).json()["data"]
    assert balance_after["balances"]["Dust"] == 1000.0
