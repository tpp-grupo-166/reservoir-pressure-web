"""Tests for user authentication endpoints.

Correr con: cd api && pytest tests/test_users.py -q

Cada test construye su propia app FastAPI con un InMemoryUserRepository
fresco, eliminando cualquier estado compartido entre tests.
"""
from __future__ import annotations

import pytest

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from tests.helpers.in_memory_user_repository import InMemoryUserRepository

from auth.security import Security
from domain.system import System

from routes.dependencies import get_system
from routes.users import router as users_router


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_app() -> FastAPI:
    """Return a FastAPI app wired with a fresh in-memory store.

    Each call produces an isolated app — no state leaks between tests.
    """
    app = FastAPI()
    system = System(
        user_repository=InMemoryUserRepository(),
        security=Security(),
    )
    app.dependency_overrides[get_system] = lambda: system
    app.include_router(users_router)
    return app


async def _register(ac: AsyncClient, email: str, password: str = "password123"):
    """Shortcut to register a user and return the response."""
    return await ac.post("/api/users", json={"email": email, "password": password})


async def _login(ac: AsyncClient, email: str, password: str = "password123"):
    """Shortcut to log in and return the response."""
    return await ac.post("/api/auth/token", json={"email": email, "password": password})


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── Register ──────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_register_user():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _register(ac, "test@example.com")

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.anyio
async def test_register_duplicate_user():
    # Arrange
    async with _client(_build_app()) as ac:
        await _register(ac, "duplicate@example.com")

        # Act
        response = await _register(ac, "duplicate@example.com")

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "El email ya está en uso"


@pytest.mark.anyio
async def test_register_invalid_email_format():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _register(ac, "invalidemail")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


@pytest.mark.anyio
async def test_register_invalid_email_no_at():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _register(ac, "usermail.com")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


@pytest.mark.anyio
async def test_register_invalid_email_no_domain():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _register(ac, "user@")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


@pytest.mark.anyio
async def test_register_password_too_short():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _register(ac, "short@example.com", password="abc")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "La contraseña debe tener al menos 8 caracteres e incluir letras y números"


@pytest.mark.anyio
async def test_register_password_no_letters():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _register(ac, "nocomplex@example.com", password="12345678")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "La contraseña debe tener al menos 8 caracteres e incluir letras y números"


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_login_valid_credentials():
    # Arrange
    async with _client(_build_app()) as ac:
        await _register(ac, "login@example.com")

        # Act
        response = await _login(ac, "login@example.com")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_invalid_email_format():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _login(ac, "invalidemail")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


@pytest.mark.anyio
async def test_login_empty_email():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _login(ac, "")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "El formato del email no es válido"


@pytest.mark.anyio
async def test_login_nonexistent_email():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _login(ac, "nonexistent@example.com")

    # Assert
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


@pytest.mark.anyio
async def test_login_wrong_password():
    # Arrange
    async with _client(_build_app()) as ac:
        await _register(ac, "wrongpass@example.com")

        # Act
        response = await _login(ac, "wrongpass@example.com", password="wrongpassword1")

    # Assert
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


@pytest.mark.anyio
async def test_login_invalid_credentials_error_message():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await _login(ac, "nonexistent@example.com", password="wrongpassword1")

    # Assert
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


# ── /users/me ─────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_current_user_with_valid_token():
    # Arrange
    async with _client(_build_app()) as ac:
        await _register(ac, "current@example.com")
        token = (await _login(ac, "current@example.com")).json()["access_token"]

        # Act
        response = await ac.get("/api/users/me", headers=_auth_header(token))

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "current@example.com"
    assert "id" in data


@pytest.mark.anyio
async def test_get_current_user_without_token():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await ac.get("/api/users/me")

    # Assert
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_current_user_with_invalid_token():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await ac.get("/api/users/me", headers=_auth_header("invalid_token"))

    # Assert
    assert response.status_code == 401


# ── /users ────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_all_users_returns_list_with_correct_shape():
    # Arrange
    async with _client(_build_app()) as ac:
        await _register(ac, "user1@example.com")
        await _register(ac, "user2@example.com")

        # Act
        response = await ac.get("/api/users")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    for user in data:
        assert "id" in user
        assert "email" in user


@pytest.mark.anyio
async def test_get_all_users_contains_registered_emails():
    # Arrange
    async with _client(_build_app()) as ac:
        await _register(ac, "alpha@example.com")
        await _register(ac, "beta@example.com")

        # Act
        response = await ac.get("/api/users")
    emails = [u["email"] for u in response.json()]

    # Assert
    assert "alpha@example.com" in emails
    assert "beta@example.com" in emails


@pytest.mark.anyio
async def test_get_all_users_empty_when_none_registered():
    # Arrange
    async with _client(_build_app()) as ac:

        # Act
        response = await ac.get("/api/users")

    # Assert
    assert response.status_code == 200
    assert response.json() == []