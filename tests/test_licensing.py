"""Testes unitários — licensing."""
from datetime import datetime, timedelta, timezone

import pytest

from app.licensing import (
    LICENSE_KEY_LEN,
    PERIOD_3Y,
    PERIOD_DAYS,
    PRODUCT_VDE,
    compute_effective_status,
    generate_license_key,
    is_valid_license_key_format,
    normalize_license_key,
    product_matches_license,
)


def test_generate_license_key_length():
    key = generate_license_key()
    assert len(key) == LICENSE_KEY_LEN


def test_is_valid_license_key_format():
    key = generate_license_key()
    assert is_valid_license_key_format(key)
    assert not is_valid_license_key_format("SHORT")
    assert not is_valid_license_key_format("INVALID-CHARS-HERE!!!!")


def test_normalize_license_key():
    raw = "abcd-1234 efgh-5678 ijkl-9012 m"
    normalized = normalize_license_key(raw)
    assert len(normalized) == LICENSE_KEY_LEN
    assert normalized.isalnum()


def test_period_3y_exists():
    assert PERIOD_3Y in PERIOD_DAYS
    assert PERIOD_DAYS[PERIOD_3Y] == 1095


def test_product_independent_licenses():
    assert product_matches_license("cloud", "cloud")
    assert product_matches_license("lab", "lab")
    assert product_matches_license("vde", "vde")
    assert not product_matches_license("cloud", "lab")
    assert not product_matches_license("lab", "cloud")
    assert not product_matches_license("cloud", "cloud_lab")
    assert not product_matches_license("lab", "cloud_lab")


def test_product_vde_matching():
    assert product_matches_license("vde", PRODUCT_VDE)
    assert not product_matches_license("lab", PRODUCT_VDE)


def test_compute_effective_status_separates_validity_and_payment():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ends = (now + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    payment = (now + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")

    eff = compute_effective_status(
        manual_status="active",
        ends_at=ends,
        payment_due_at=payment,
        block_after_days=30,
        cancel_after_days=45,
        now=now,
    )
    assert eff["daysRemaining"] == 10
    assert eff["licenseExpired"] is False
    assert eff["paymentPhase"] == "active"


def test_license_expired_after_ends_at():
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    ends = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    eff = compute_effective_status(
        manual_status="active",
        ends_at=ends,
        payment_due_at=ends,
        now=now,
    )
    assert eff["licenseExpired"] is True
    assert eff["daysRemaining"] == 0
    assert eff["validForSoftware"] is False


def test_api_v1_imports():
    from app.api_v1 import router

    assert router.prefix == "/api/v1/licenses"
