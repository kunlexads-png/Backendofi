import io


def test_upload_and_import_csv(client, officer_headers):
    # Prepare sample CSV content
    csv_content = (
        "truck_number,driver_name,supplier,number_of_bags,gross_weight,tare_weight,net_weight,batch_number,warehouse,cluster,moisture\n"
        "GH-CSV-01,Kofi Annan,Volta Cocoa Alliance,150,9750.0,750.0,9000.0,BAT-CSV-01,Warehouse A,Volta Cluster,7.1\n"
        "GH-CSV-02,Aba Mansa,Eastern Growers,200,13000.0,1000.0,12000.0,BAT-CSV-02,Warehouse B,Eastern Cluster,7.3\n"
    )

    files = {
        "file": ("cocoa_arrivals_batch.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }

    # 1. Upload
    res = client.post("/api/uploads", headers=officer_headers, files=files)
    assert res.status_code == 201
    file_id = res.json()["data"]["id"]
    preview = res.json()["data"]["preview_data"]
    assert preview["valid_count"] == 2

    # 2. Get upload details
    get_res = client.get(f"/api/uploads/{file_id}", headers=officer_headers)
    assert get_res.status_code == 200

    # 3. Commit reviewed import into arrivals
    import_res = client.post(
        f"/api/uploads/{file_id}/import?target_module=arrival",
        headers=officer_headers
    )
    assert import_res.status_code == 200
    assert import_res.json()["data"]["imported_count"] == 2
