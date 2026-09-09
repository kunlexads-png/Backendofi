from datetime import date


def test_create_arrival_by_officer(client, officer_headers):
    payload = {
        "date": str(date.today()),
        "time": "09:30",
        "truck_number": "GH-204-24",
        "driver_name": "Kwame Mensah",
        "supplier": "Kumasi Cocoa Co-op",
        "customer": "OFI Processing Plant",
        "product": "Cocoa Beans",
        "number_of_bags": 320,
        "gross_weight": 20800.0,
        "tare_weight": 1600.0,
        "batch_number": "BAT-2026-001",
        "warehouse": "Shed 1",
        "cluster": "Ashanti West",
        "moisture": 7.2,
        "status": "Arrived",
        "offloading_status": "Waiting",
        "remarks": "Standard Grade 1 cocoa"
    }
    response = client.post("/api/arrivals", headers=officer_headers, json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["net_weight"] == 19200.0
    assert data["truck_number"] == "GH-204-24"
    assert data["arrival_id"].startswith("ARR-")


def test_viewer_cannot_create_arrival(client, viewer_headers):
    payload = {
        "date": str(date.today()),
        "time": "10:00",
        "truck_number": "GH-111-20",
        "driver_name": "Test Driver",
        "supplier": "Test Supplier",
        "product": "Cocoa Beans",
        "number_of_bags": 100,
        "gross_weight": 7000.0,
        "tare_weight": 500.0,
        "batch_number": "BAT-002",
        "warehouse": "Shed 2",
        "cluster": "Cluster A",
        "moisture": 7.5,
        "status": "Pending",
        "offloading_status": "Not Started"
    }
    response = client.post("/api/arrivals", headers=viewer_headers, json=payload)
    assert response.status_code == 403


def test_weight_validation_error(client, officer_headers):
    payload = {
        "date": str(date.today()),
        "time": "10:00",
        "truck_number": "GH-999-22",
        "driver_name": "Test Driver",
        "supplier": "Test Supplier",
        "product": "Cocoa Beans",
        "number_of_bags": 100,
        "gross_weight": 500.0,
        "tare_weight": 1000.0,  # Invalid: tare > gross
        "batch_number": "BAT-003",
        "warehouse": "Shed 1",
        "cluster": "Cluster B",
        "moisture": 7.5,
        "status": "Pending",
        "offloading_status": "Not Started"
    }
    response = client.post("/api/arrivals", headers=officer_headers, json=payload)
    assert response.status_code == 422


def test_arrival_status_update_and_stock(client, supervisor_headers, officer_headers):
    # 1. Create
    payload = {
        "date": str(date.today()),
        "time": "11:00",
        "truck_number": "GH-555-25",
        "driver_name": "John Doe",
        "supplier": "Sunyani Farm Union",
        "product": "Cocoa Beans",
        "number_of_bags": 200,
        "gross_weight": 13000.0,
        "tare_weight": 1000.0,
        "batch_number": "BAT-2026-SUN",
        "warehouse": "Main Hub",
        "cluster": "Bono Region",
        "moisture": 7.0,
        "status": "Waiting for Offloading",
        "offloading_status": "Queued"
    }
    create_res = client.post("/api/arrivals", headers=officer_headers, json=payload)
    arr_id = create_res.json()["data"]["id"]

    # 2. Update to Completed by supervisor
    update_res = client.put(
        f"/api/arrivals/{arr_id}",
        headers=supervisor_headers,
        json={"status": "Completed", "offloading_status": "Done"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["status"] == "Completed"

    # 3. Check stock balance
    stock_res = client.get("/api/stock/summary", headers=supervisor_headers)
    assert stock_res.status_code == 200
    assert stock_res.json()["data"]["total_cocoa_stock"] >= 12000.0
