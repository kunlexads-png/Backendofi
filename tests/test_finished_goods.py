from datetime import date


def test_finished_goods_flow(client, officer_headers, supervisor_headers):
    # 1. Add finished goods
    payload = {
        "date": str(date.today()),
        "product": "Cocoa Butter",
        "product_type": "Deodorized Pure Prime Press",
        "batch_number": "FG-BUT-01",
        "quantity": 100.0,
        "number_of_bags": 100,
        "weight": 2500.0,
        "warehouse_location": "Bay 4 Cold Storage",
        "customer": "Nestle Switzerland",
        "status": "In Stock"
    }
    create_res = client.post("/api/finished-goods", headers=officer_headers, json=payload)
    assert create_res.status_code == 201
    fg_id = create_res.json()["data"]["id"]
    assert create_res.json()["data"]["record_id"].startswith("FG-")

    # 2. Check stock
    summary = client.get("/api/stock/summary", headers=supervisor_headers).json()["data"]
    assert summary["total_finished_goods_stock"] >= 2500.0

    # 3. Dispatch finished goods
    dispatch_res = client.post(
        f"/api/finished-goods/{fg_id}/dispatch",
        headers=supervisor_headers,
        json={
            "quantity": 50.0,
            "weight": 1250.0,
            "customer": "Nestle Switzerland",
            "reference_number": "SO-882741"
        }
    )
    assert dispatch_res.status_code == 200

    # 4. Check reduced balance
    summary_after = client.get("/api/stock/summary", headers=supervisor_headers).json()["data"]
    assert summary_after["total_finished_goods_stock"] == 1250.0
