def test_user_registration(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "new_manager",
            "email": "manager@ofi.com",
            "full_name": "Warehouse Manager One",
            "password": "securepassword123",
            "role": "Warehouse Manager"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "new_manager"


def test_user_login_success(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "admin_test",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert "access_token" in res["data"]
    assert res["data"]["user"]["username"] == "admin_test"


def test_user_login_failure(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "admin_test",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_get_current_user_me(client, admin_headers):
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    res = response.json()
    assert res["data"]["username"] == "admin_test"
    assert res["data"]["role"] == "Admin"


def test_change_password(client, admin_headers):
    response = client.post(
        "/api/auth/change-password",
        headers=admin_headers,
        json={
            "old_password": "password123",
            "new_password": "brandnewpassword456"
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
