"""Pytest configuration and shared fixtures."""

import pytest
import sys
import os

# Add all service paths to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SERVICES = [
    "patient-service",
    "doctor-service",
    "appointment-service",
    "billing-service",
    "prescription-service",
    "payment-service",
    "notification-service",
]

for service in SERVICES:
    service_path = os.path.join(BASE_DIR, service, "app")
    if service_path not in sys.path:
        sys.path.insert(0, service_path)


@pytest.fixture(scope="session")
def base_dir():
    """Return the base directory of the project."""
    return BASE_DIR


@pytest.fixture
def role_headers():
    """Factory fixture for role headers."""
    def _make_headers(role: str):
        return {"x-role": role}
    return _make_headers


@pytest.fixture
def admin_headers(role_headers):
    return role_headers("admin")


@pytest.fixture
def reception_headers(role_headers):
    return role_headers("reception")


@pytest.fixture
def doctor_headers(role_headers):
    return role_headers("doctor")


@pytest.fixture
def billing_headers(role_headers):
    return role_headers("billing")


@pytest.fixture
def patient_role_headers(role_headers):
    return role_headers("patient")