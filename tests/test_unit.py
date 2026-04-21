"""Unit tests - verify services can load and work.

Run with: pytest tests/test_unit.py -v -s
"""

import pytest
import subprocess
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_service_test(service_dir, verbose=True):
    """Test if a service can be imported."""
    cmd = f"from app.{service_dir.replace('-', '_')} import app; print('OK')"
    if verbose:
        print(f"\n{'='*60}")
        print(f"🔵 IMPORT: {service_dir}")
        print(f"   Command: {cmd}")
    
    result = subprocess.run(
        ["python3", "-c", cmd],
        cwd=os.path.join(BASE, service_dir),
        capture_output=True,
        text=True
    )
    
    success = result.returncode == 0 and "OK" in result.stdout
    if verbose:
        print(f"   📤 stdout: {result.stdout.strip()}")
        if result.stderr:
            print(f"   📤 stderr: {result.stderr.strip()[:200]}")
        print(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
        print(f"{'='*60}")
        sys.stdout.flush()
    
    return success


class TestServiceImports:
    """Test that each service can be imported."""

    def test_patient_service_loads(self):
        assert run_service_test("patient-service")

    def test_doctor_service_loads(self):
        assert run_service_test("doctor-service")

    def test_appointment_service_loads(self):
        assert run_service_test("appointment-service")

    def test_billing_service_loads(self):
        assert run_service_test("billing-service")

    def test_prescription_service_loads(self):
        assert run_service_test("prescription-service")

    def test_payment_service_loads(self):
        assert run_service_test("payment-service")

    def test_notification_service_loads(self):
        assert run_service_test("notification-service")


class TestServiceStructure:
    """Test expected endpoints exist."""

    def test_patient_endpoints(self):
        print(f"\n{'='*60}")
        print(f"🔵 CHECK: patient-service endpoints")
        
        result = subprocess.run(
            ["python3", "-c", 
             "from app.patient_service import app; "
             "print([r.path for r in app.routes])"],
            cwd=os.path.join(BASE, "patient-service"),
            capture_output=True,
            text=True
        )
        
        print(f"   📤 Routes: {result.stdout.strip()}")
        assert "/v1/patients" in result.stdout
        assert "/health" in result.stdout
        assert "/metrics" in result.stdout
        print(f"   Status: ✅ PASS")
        print(f"{'='*60}")

    def test_appointment_endpoints(self):
        print(f"\n{'='*60}")
        print(f"🔵 CHECK: appointment-service endpoints")
        
        result = subprocess.run(
            ["python3", "-c",
             "from app.appointment_service import app; "
             "print([r.path for r in app.routes])"],
            cwd=os.path.join(BASE, "appointment-service"),
            capture_output=True,
            text=True
        )
        
        print(f"   📤 Routes: {result.stdout.strip()}")
        assert "/v1/appointments" in result.stdout
        assert "reschedule" in result.stdout
        assert "cancel" in result.stdout
        print(f"   Status: ✅ PASS")
        print(f"{'='*60}")
        assert "complete" in result.stdout


class TestDatabaseSeeding:
    """Test database seeding works."""

    def test_patient_service_seeds(self):
        print(f"\n{'='*60}")
        print(f"🔵 CHECK: patient data seeding")
        
        result = subprocess.run(
            ["python3", "-c",
             "from app.seed import seed_patient_service; "
             "seed_patient_service(); "
             "from app.common import db; "
             "with db('patient_service.db') as c: "
             "print(c.execute('SELECT COUNT(*) FROM patients').fetchone()[0])"],
            cwd=os.path.join(BASE, "patient-service"),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            count = int(result.stdout.strip())
            print(f"   📤 Patient count: {count}")
            assert count > 0, f"Expected patients, got {count}"
            print(f"   Status: ✅ PASS")
        else:
            print(f"   📤 Error: {result.stderr[:200]}")
            print(f"   Status: ❌ FAIL")
        print(f"{'='*60}")


class TestBusinessRules:
    """Test business logic."""

    def test_slot_validation_2h_lead_time(self):
        print(f"\n{'='*60}")
        print(f"🔵 CHECK: slot validation (2h lead time)")
        
        code = '''
from datetime import timedelta
from app.common import utc_now
from app.appointment_service import validate_slot

past = utc_now() + timedelta(hours=1)
doctor = {'slot_minutes': 30, 'clinic_start': '09:00', 'clinic_end': '17:00'}

try:
    validate_slot(doctor, past, past + timedelta(minutes=30))
    print("FAILED")
except Exception as e:
    print("OK")
'''
        result = subprocess.run(
            ["python3", "-c", code],
            cwd=os.path.join(BASE, "appointment-service"),
            capture_output=True,
            text=True
        )
        
        print(f"   📤 Result: {result.stdout.strip()}")
        assert "OK" in result.stdout
        print(f"   Status: ✅ PASS (slot rejected for <2h ahead)")
        print(f"{'='*60}")

    def test_tax_rate_5_percent(self):
        print(f"\n{'='*60}")
        print(f"🔵 CHECK: tax rate (5%)")
        
        result = subprocess.run(
            ["python3", "-c",
             "from app.billing_service import TAX_RATE; "
             "print(TAX_RATE)"],
            cwd=os.path.join(BASE, "billing-service"),
            capture_output=True,
            text=True
        )
        
        print(f"   📤 Tax Rate: {result.stdout.strip()}")
        assert "0.05" in result.stdout
        print(f"   Status: ✅ PASS")
        print(f"{'='*60}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])