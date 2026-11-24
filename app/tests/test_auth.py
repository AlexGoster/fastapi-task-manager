"""Tests for auth routes."""

from httpx import AsyncClient


async def test_register(client: AsyncClient, token_for):
    resp = await client.post(
        "/auth/register", json={"username": "tuser", "email": "t@t.com", "password": "password123"}
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == "tuser"


async def test_register_duplicate_email(client: AsyncClient, token_for):
    await client.post(
        "/auth/register", json={"username": "user1", "email": "d@d.com", "password": "password123"}
    )
    resp = await client.post(
        "/auth/register", json={"username": "user2", "email": "d@d.com", "password": "password123"}
    )
    assert resp.status_code == 409


async def test_login(client: AsyncClient, token_for):
    await client.post(
        "/auth/register", json={"username": "luser", "email": "l@l.com", "password": "password123"}
    )
    resp = await client.post("/auth/login", data={"username": "luser", "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient, token_for):
    await client.post(
        "/auth/register",
        json={"username": "wronguser", "email": "w@w.com", "password": "password123"},
    )
    resp = await client.post("/auth/login", data={"username": "wronguser", "password": "wrong"})
    assert resp.status_code == 401


async def test_register_duplicate_username(client: AsyncClient, token_for):
    await client.post(
        "/auth/register", json={"username": "dup", "email": "d1@x.com", "password": "password123"}
    )
    resp = await client.post(
        "/auth/register", json={"username": "dup", "email": "d2@x.com", "password": "password123"}
    )
    assert resp.status_code == 409
