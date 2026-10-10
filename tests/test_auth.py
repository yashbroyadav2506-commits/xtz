from app.models import User


def test_register_creates_account_and_signs_in(client, app):
    response = client.post(
        "/auth/register",
        data={"name": "Test Reader", "email": "reader@example.com", "password": "Password123!"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Your account is ready" in response.data
    with app.app_context():
        user = User.query.filter_by(email="reader@example.com").first()
        assert user is not None
        assert user.check_password("Password123!")
        assert user.password_hash != "Password123!"


def test_login_rejects_incorrect_password(client, users):
    response = client.post(
        "/auth/login",
        data={"email": "owner@example.com", "password": "wrong-password"},
        follow_redirects=True,
    )
    assert b"Email or password is incorrect" in response.data


def test_logout_requires_post_and_clears_session(client):
    response = client.post("/auth/logout", follow_redirects=True)
    assert response.status_code == 200


def test_csrf_blocks_post_without_token(client, app):
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post("/auth/login", data={"email": "owner@example.com", "password": "Password123!"})
    assert response.status_code == 400
