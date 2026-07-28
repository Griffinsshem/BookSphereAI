"""
Full HTTP request/response tests for the auth endpoints, via Flask's
test client. These are the tests that actually exercise routing,
schema validation, status codes, and cookie behavior end-to-end.
"""
from __future__ import annotations


class TestRegisterEndpoint:
    def test_register_returns_201_and_user(self, client, db_session):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "correct-horse-battery-staple-1",
                "full_name": "New User",
                "organization_name": "New Org",
            },
        )

        assert response.status_code == 201
        body = response.get_json()
        assert body["user"]["email"] == "newuser@example.com"
        assert "access_token" in body
        # Critical negative assertion: the refresh token must NEVER
        # appear in the JSON body — only in the httpOnly cookie.
        assert "refresh_token" not in body
        assert "password_hash" not in body["user"]

    def test_register_sets_httponly_refresh_cookie(self, client, db_session):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "cookietest@example.com",
                "password": "correct-horse-battery-staple-1",
                "full_name": "Cookie Test",
                "organization_name": "Cookie Org",
            },
        )

        set_cookie_headers = response.headers.get_all("Set-Cookie")
        refresh_cookie = next(
            h for h in set_cookie_headers if "bs_refresh_token" in h
        )
        assert "HttpOnly" in refresh_cookie

        csrf_cookie = next(h for h in set_cookie_headers if "bs_csrf_token" in h)
        # CSRF cookie must NOT be httpOnly — frontend JS needs to read
        # it to echo it back in the X-CSRF-Token header.
        assert "HttpOnly" not in csrf_cookie

    def test_register_rejects_weak_password(self, client, db_session):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "short1",
                "full_name": "Weak Password",
                "organization_name": "Weak Org",
            },
        )

        assert response.status_code == 422

    def test_register_rejects_duplicate_email(self, client, db_session):
        payload = {
            "email": "dupe@example.com",
            "password": "correct-horse-battery-staple-1",
            "full_name": "First",
            "organization_name": "First Org",
        }
        client.post("/api/v1/auth/register", json=payload)

        payload["organization_name"] = "Second Org"
        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 409


class TestLoginEndpoint:
    def test_login_succeeds_with_correct_credentials(self, client, db_session):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "loginflow@example.com",
                "password": "correct-horse-battery-staple-1",
                "full_name": "Login Flow",
                "organization_name": "Login Org",
            },
        )

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "loginflow@example.com",
                "password": "correct-horse-battery-staple-1",
            },
        )

        assert response.status_code == 200
        assert "access_token" in response.get_json()

    def test_login_rejects_wrong_password_with_generic_message(
        self, client, db_session
    ):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpwflow@example.com",
                "password": "correct-horse-battery-staple-1",
                "full_name": "Test",
                "organization_name": "Test Org",
            },
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpwflow@example.com", "password": "totally-wrong"},
        )

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "INVALID_CREDENTIALS"


class TestMeEndpoint:
    def test_me_requires_authentication(self, client, db_session):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_me_returns_user_and_memberships_when_authenticated(
        self, client, db_session
    ):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "meflow@example.com",
                "password": "correct-horse-battery-staple-1",
                "full_name": "Me Flow",
                "organization_name": "Me Org",
            },
        )
        access_token = register_response.get_json()["access_token"]

        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        body = response.get_json()
        assert body["user"]["email"] == "meflow@example.com"
        assert len(body["memberships"]) == 1
        assert body["memberships"][0]["role"] == "owner"
        assert body["memberships"][0]["organization"]["slug"] == "me-org"
