"""Tests for user authentication endpoints. Correr con: cd api && pytest -q"""
from __future__ import annotations

import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_register_user():
    """Test registering a new user."""
    response = client.post(
        "/api/users",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_register_duplicate_user():
    """Test registering a user that already exists."""
    # First registration
    client.post(
        "/api/users",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    
    # Second registration with same email should fail with 409
    response = client.post(
        "/api/users",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "El email ya está en uso"


def test_login_valid_credentials():
    """Test login with valid credentials."""
    # First register a user
    client.post(
        "/api/users",
        json={"email": "login@example.com", "password": "password123"}
    )
    
    # Then login
    response = client.post(
        "/api/auth/token",
        json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_email():
    """Test login with non-existent email."""
    response = client.post(
        "/api/auth/token",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


def test_login_invalid_password():
    """Test login with wrong password."""
    # First register a user
    client.post(
        "/api/users",
        json={"email": "wrongpass@example.com", "password": "password123"}
    )
    
    # Try login with wrong password
    response = client.post(
        "/api/auth/token",
        json={"email": "wrongpass@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


def test_get_all_users():
    """Test getting all users."""
    # Register a couple of users
    client.post(
        "/api/users",
        json={"email": "user1@example.com", "password": "password123"}
    )
    client.post(
        "/api/users",
        json={"email": "user2@example.com", "password": "password123"}
    )
    
    response = client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    # Check that each user has id and email
    for user in data:
        assert "id" in user
        assert "email" in user


def test_get_current_user_with_token():
    """Test getting current user with valid token."""
    # Register and login
    client.post(
        "/api/users",
        json={"email": "current@example.com", "password": "password123"}
    )
    login_response = client.post(
        "/api/auth/token",
        json={"email": "current@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "current@example.com"
    assert "id" in data


def test_get_current_user_without_token():
    """Test getting current user without token should fail."""
    response = client.get("/api/users/me")
    assert response.status_code == 401


def test_get_current_user_with_invalid_token():
    """Test getting current user with invalid token should fail."""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_register_invalid_email_format():
    """Test registering with invalid email format."""
    response = client.post(
        "/api/users",
        json={"email": "invalidemail", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


def test_register_invalid_email_no_at():
    """Test registering with email without @."""
    response = client.post(
        "/api/users",
        json={"email": "usermail.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


def test_register_invalid_email_no_domain():
    """Test registering with email without domain."""
    response = client.post(
        "/api/users",
        json={"email": "user@", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


def test_register_password_too_short():
    """Test registering with password shorter than 8 characters."""
    response = client.post(
        "/api/users",
        json={"email": "short@example.com", "password": "abc"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "La contraseña debe tener al menos 8 caracteres e incluir letras y números"


def test_register_password_no_complexity():
    """Test registering with password without letters and numbers."""
    response = client.post(
        "/api/users",
        json={"email": "nocomplex@example.com", "password": "12345678"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "La contraseña debe tener al menos 8 caracteres e incluir letras y números"


def test_login_invalid_email_format():
    """Test login with invalid email format."""
    response = client.post(
        "/api/auth/token",
        json={"email": "invalidemail", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


def test_login_empty_email():
    """Test login with empty email."""
    response = client.post(
        "/api/auth/token",
        json={"email": "", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


def test_login_invalid_credentials_error_message():
    """Test that invalid credentials returns correct error message."""
    response = client.post(
        "/api/auth/token",
        json={"email": "nonexistent@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"

