"""Testes de integração E2E — fluxo cadastro → licença → validação."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("LOCAL_DATABASE_URL", "sqlite:///./data/test_gerador.db")
os.environ.setdefault("PRODUCT_API_KEY", "test-api-key-e2e")
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "Test@Admin2026!")
os.environ.setdefault("SYNC_REMOTE_ENABLED", "false")

from app.auth import hash_password
from app.licensing import generate_license_key, is_valid_license_key_format
from app.models import Base, Operator
from app.main import app


@pytest.fixture()
def client():
    from app.config import settings
    from app import models

    engine = create_engine(settings.local_database_url, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    models.engine = engine
    models.SessionLocal = TestSession

    db = TestSession()
    db.add(Operator(username="admin", password_hash=hash_password("Test@Admin2026!"), nome="Admin"))
    db.commit()
    db.close()

    with TestClient(app) as c:
        yield c


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_public_landing(client: TestClient):
    r = client.get("/")
    assert r.status_code == 200
    assert "Inova TI" in r.text


def test_e2e_client_license_validate(client: TestClient):
    client.post(
        "/login",
        data={"username": "admin", "password": "Test@Admin2026!"},
        follow_redirects=False,
    )

    r = client.post(
        "/clients",
        data={
            "nome": "Clínica Teste E2E",
            "document_type": "cnpj",
            "email": "teste@example.com",
            "clinica_id_erp": "1",
            "clinica_id_lab": "1",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303

    from app.models import SessionLocal, Client, LicenseRecord

    db = SessionLocal()
    c = db.query(Client).filter(Client.nome == "Clínica Teste E2E").first()
    assert c is not None

    client.post(
        f"/clients/{c.id}/licenses",
        data={"produto": "lab", "periodo": "trial", "payment_plan": "monthly"},
        follow_redirects=False,
    )
    lic = db.query(LicenseRecord).filter(LicenseRecord.client_id == c.id).first()
    assert lic is not None
    assert is_valid_license_key_format(lic.license_key)
    db.close()

    vr = client.post(
        "/api/v1/licenses/validate",
        json={
            "license_key": lic.license_key,
            "clinica_id": 1,
            "product": "lab",
        },
        headers={"X-License-Api-Key": "test-api-key-e2e"},
    )
    assert vr.status_code == 200
    body = vr.json()
    assert body["valid"] is True
    assert "daysRemaining" in body
    assert body["daysRemaining"] >= 0


def test_revoke_license(client: TestClient):
    from app.models import SessionLocal, Client, LicenseRecord
    from app.services import create_client, issue_license, revoke_license

    db = SessionLocal()
    c = create_client(db, operator="admin", nome="Revoke Test", clinica_id_erp=99, clinica_id_lab=99)
    lic = issue_license(db, operator="admin", client_id=c.id, produto="vde", periodo="1y")
    revoke_license(db, operator="admin", license_id=lic.id, reason="test")
    db.refresh(lic)
    assert lic.manual_status == "revoked"
    db.close()

    vr = client.post(
        "/api/v1/licenses/validate",
        json={"license_key": lic.license_key, "clinica_id": 99, "product": "vde"},
        headers={"X-License-Api-Key": "test-api-key-e2e"},
    )
    assert vr.status_code == 200
    assert vr.json()["valid"] is False
