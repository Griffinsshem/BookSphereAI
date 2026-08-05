"""
Tests for /refresh and /logout — the cookie-rotation and
CSRF-protected endpoints. These are the highest-security-risk
endpoints in the auth feature, so they're tested explicitly rather
than only incidentally via other tests.
"""
from __future__ import annotations
import re


def _register(client, email="refreshflow@example.com", org="Refresh Org"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correct-horse-battery-staple-1",
            "full_name": "Refresh Flow",
            "organization_name": org,
        },
    )


def _extract_csrf_token(response) -> str:
    """Pull the CSRF cookie's value out of a response's Set-Cookie
    headers. The test client's cookie jar handles resending the
    cookie automatically on subsequent requests, but does NOT
    automatically populate our custom X-CSRF-Token header — that's
    the frontend's job in real usage, so we replicate it manually
    here."""
    set_cookie_headers = response.headers.get_all("Set-Cookie")
    csrf_header = next(h for h in set_cookie_headers if "bs_csrf_token" in h)
    match = re.search(r"bs_csrf_token=([^;]+)", csrf_header)
    assert match is not None
    return match.group(1)


class TestRefreshEndpoint:
    def test_options_preflight_is_never_csrf_blocked(self, client, db_session):
        """Regression test: CORS preflight (OPTIONS) requests must
        never be rejected by CSRF checks, since preflight requests
        never carry cookies or custom headers by browser design. A
        403 here would make the browser block the real request
        entirely -- discovered via manual browser testing, since the
        Flask test client's normal request cycle doesn't simulate
        real preflight behavior."""
        response = client.options("/api/v1/auth/refresh")
        assert response.status_code != 403

    def test_refresh_succeeds_with_valid_cookie_and_csrf(self, client, db_session):
        register_response = _register(client)
        csrf_token = _extract_csrf_token(register_response)

        # The test client's cookie jar automatically resends the
        # refresh-token cookie set during registration — we only need
        # to supply the CSRF header manually.
        response = client.post(
            "/api/v1/auth/refresh", headers={"X-CSRF-Token": csrf_token}
        )

        assert response.status_code == 200
        assert "access_token" in response.get_json()

    def test_refresh_rejected_without_csrf_header(self, client, db_session):
        _register(client)

        response = client.post("/api/v1/auth/refresh")  # no X-CSRF-Token header

        assert response.status_code == 403

    def test_refresh_rejected_with_mismatched_csrf(self, client, db_session):
        _register(client)

        response = client.post(
            "/api/v1/auth/refresh",
            headers={"X-CSRF-Token": "not-the-real-token"},
        )

        assert response.status_code == 403

    def test_refresh_rotation_invalidates_old_token(self, client, db_session):
        """Proves the security property we designed for: once a
        refresh token has been used, it cannot be used again."""
        register_response = _register(client, email="rotation@example.com")
        csrf_token = _extract_csrf_token(register_response)

        first_refresh = client.post(
            "/api/v1/auth/refresh", headers={"X-CSRF-Token": csrf_token}
        )
        assert first_refresh.status_code == 200

        # /refresh rotates BOTH the refresh token and the CSRF token
        # on every call (see _set_auth_cookies). The second request
        # must use the freshly rotated CSRF token, or it fails CSRF
        # validation before ever reaching the refresh-token check —
        # which would test the wrong thing.
        rotated_csrf_token = _extract_csrf_token(first_refresh)

        # The cookie jar now holds the NEW rotated refresh token
        # automatically. Manually replay the OLD cookie value to
        # simulate a stolen/reused token.
        old_refresh_cookie = None
        for header in register_response.headers.get_all("Set-Cookie"):
            if "bs_refresh_token" in header:
                old_refresh_cookie = header.split(";")[0].split("=", 1)[1]

        assert old_refresh_cookie is not None

        client.set_cookie("bs_refresh_token", old_refresh_cookie, path="/api/v1/auth")
        second_attempt = client.post(
            "/api/v1/auth/refresh", headers={"X-CSRF-Token": rotated_csrf_token}
        )

        assert second_attempt.status_code == 401


class TestLogoutEndpoint:
    def test_logout_succeeds_and_revokes_token(self, client, db_session):
        register_response = _register(client, email="logoutflow@example.com")
        csrf_token = _extract_csrf_token(register_response)

        # Capture the (soon to be revoked) refresh token cookie value
        # before logout clears it from the jar.
        revoked_refresh_cookie = None
        for header in register_response.headers.get_all("Set-Cookie"):
            if "bs_refresh_token" in header:
                revoked_refresh_cookie = header.split(";")[0].split("=", 1)[1]
        assert revoked_refresh_cookie is not None

        logout_response = client.post(
            "/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_token}
        )
        assert logout_response.status_code == 200

        # Logout intentionally clears the CSRF cookie too (no session
        # artifacts should survive logout) — so to isolate testing
        # "the refresh token itself was revoked" specifically, rather
        # than incidentally re-testing CSRF enforcement, we supply a
        # fresh, self-consistent CSRF cookie/header pair and manually
        # restore the revoked refresh-token cookie.
        client.set_cookie("bs_csrf_token", "manual-test-csrf-token")
        client.set_cookie(
            "bs_refresh_token", revoked_refresh_cookie, path="/api/v1/auth"
        )

        refresh_attempt = client.post(
            "/api/v1/auth/refresh",
            headers={"X-CSRF-Token": "manual-test-csrf-token"},
        )
        assert refresh_attempt.status_code == 401

    def test_logout_rejected_without_csrf(self, client, db_session):
        _register(client, email="logoutnocsrf@example.com")

        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 403
