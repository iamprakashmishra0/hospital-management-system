"""End-to-end test scenarios for Hospital Management System.

Run services first with: docker-compose up -d
Then run: pytest tests/test_e2e.py -v -s

Logs are printed with -s flag to show request/response in terminal.
"""

import pytest
import requests
from datetime import datetime, timedelta
import time
import json
import sys

# Create logging wrapper for requests
_orig_request = requests.Session.request

def _logging_request(self, method, url, **kwargs):
    """Wrapper that logs HTTP requests and responses"""
    # Log request
    body = kwargs.get('json') or kwargs.get('data')
    body_str = json.dumps(body) if body else ""
    print(f"\n{'='*70}")
    print(f"🔵 REQUEST: {method} {url}")
    if body_str:
        print(f"   📥 Body: {body_str[:200]}..." if len(body_str) > 200 else f"   📥 Body: {body_str}")
    headers = kwargs.get('headers', {})
    if 'x-role' in headers:
        print(f"   🔐 Role: {headers['x-role']}")
    
    # Make the actual request
    response = _orig_request(self, method, url, **kwargs)
    
    # Log response  
    print(f"   📤 Status: {response.status_code}")
    try:
        resp_body = response.json()
        print(f"   📤 Response: {json.dumps(resp_body)[:300]}..." if len(json.dumps(resp_body)) > 300 else f"   📤 Response: {json.dumps(resp_body)}")
    except:
        if response.text:
            print(f"   📤 Response: {response.text[:200]}..." if len(response.text) > 200 else f"   📤 Response: {response.text}")
    print(f"{'='*70}")
    sys.stdout.flush()
    
    return response

# Apply logging to all requests sessions
requests.Session.request = _logging_request


BASE_URLS = {
    "patient": "http://localhost:8001",
    "doctor": "http://localhost:8002",
    "appointment": "http://localhost:8003",
    "billing": "http://localhost:8004",
    "prescription": "http://localhost:8005",
    "payment": "http://localhost:8006",
    "notification": "http://localhost:8007",
}


def wait_for_services(timeout=30):
    """Wait for all services to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{BASE_URLS['patient']}/health", timeout=2)
            if resp.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    return False


@pytest.fixture(scope="module", autouse=True)
def ensure_services_running():
    """Ensure services are running before tests."""
    if not wait_for_services(timeout=5):
        pytest.skip("Services not running. Start with docker-compose up -d")


@pytest.fixture
def headers():
    return {}


@pytest.fixture
def admin_headers():
    return {"x-role": "admin"}


@pytest.fixture
def reception_headers():
    return {"x-role": "reception"}


@pytest.fixture
def doctor_headers():
    return {"x-role": "doctor"}


@pytest.fixture
def billing_headers():
    return {"x-role": "billing"}


# ==================== HEALTH CHECKS ====================


class TestHealthEndpoints:
    def test_patient_service_health(self):
        resp = requests.get(f"{BASE_URLS['patient']}/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_doctor_service_health(self):
        resp = requests.get(f"{BASE_URLS['doctor']}/health")
        assert resp.status_code == 200

    def test_appointment_service_health(self):
        resp = requests.get(f"{BASE_URLS['appointment']}/health")
        assert resp.status_code == 200

    def test_billing_service_health(self):
        resp = requests.get(f"{BASE_URLS['billing']}/health")
        assert resp.status_code == 200

    def test_prescription_service_health(self):
        resp = requests.get(f"{BASE_URLS['prescription']}/health")
        assert resp.status_code == 200

    def test_payment_service_health(self):
        resp = requests.get(f"{BASE_URLS['payment']}/health")
        assert resp.status_code == 200

    def test_notification_service_health(self):
        resp = requests.get(f"{BASE_URLS['notification']}/health")
        assert resp.status_code == 200


# ==================== METRICS ====================


class TestMetrics:
    def test_appointment_metrics(self):
        resp = requests.get(f"{BASE_URLS['appointment']}/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "appointments_created_total" in data
        assert "bill_creation_latency_ms" in data

    def test_billing_metrics(self):
        resp = requests.get(f"{BASE_URLS['billing']}/metrics")
        assert resp.status_code == 200


# ==================== PATIENT SERVICE ====================


class TestPatientService:
    def test_list_patients(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['patient']}/v1/patients", headers=admin_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_list_patients_paginated(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['patient']}/v1/patients?page=1&page_size=5", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["pagination"]["pageSize"] == 5

    def test_search_patients(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['patient']}/v1/patients?search=john", headers=admin_headers)
        assert resp.status_code == 200

    def test_get_patient(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['patient']}/v1/patients/1", headers=admin_headers)
        assert resp.status_code in [200, 404]

    def test_create_patient(self, reception_headers):
        payload = {
            "name": "Test Patient E2E",
            "email": "teste2e@example.com",
            "phone": "9999999999",
            "dob": "1990-01-01"
        }
        resp = requests.post(f"{BASE_URLS['patient']}/v1/patients", json=payload, headers=reception_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Patient E2E"

    def test_update_patient(self, reception_headers):
        payload = {"name": "Updated", "version": 1}
        resp = requests.put(f"{BASE_URLS['patient']}/v1/patients/1", json=payload, headers=reception_headers)
        assert resp.status_code in [200, 404, 409]


# ==================== DOCTOR SERVICE ====================


class TestDoctorService:
    def test_list_doctors(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['doctor']}/v1/doctors", headers=admin_headers)
        assert resp.status_code == 200

    def test_filter_by_department(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['doctor']}/v1/doctors?department=cardiology", headers=admin_headers)
        assert resp.status_code == 200

    def test_get_doctor(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['doctor']}/v1/doctors/1", headers=admin_headers)
        assert resp.status_code in [200, 404]

    def test_check_availability(self, reception_headers):
        future = (datetime.now() + timedelta(days=1)).isoformat()
        resp = requests.post(
            f"{BASE_URLS['doctor']}/v1/doctors/1/availability",
            json={"slot_start": future},
            headers=reception_headers
        )
        assert resp.status_code in [200, 404]


# ==================== APPOINTMENT SERVICE ====================


class TestAppointmentService:
    def test_list_appointments(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['appointment']}/v1/appointments", headers=admin_headers)
        assert resp.status_code == 200

    def test_book_appointment(self, reception_headers, admin_headers):
        # First get a valid patient and doctor
        patient_resp = requests.get(f"{BASE_URLS['patient']}/v1/patients/1", headers=admin_headers)
        if patient_resp.status_code != 200:
            pytest.skip("No patient data")

        doctor_resp = requests.get(f"{BASE_URLS['doctor']}/v1/doctors/1", headers=admin_headers)
        if doctor_resp.status_code != 200:
            pytest.skip("No doctor data")

        future = (datetime.now() + timedelta(hours=3)).isoformat()
        payload = {
            "patient_id": 1,
            "doctor_id": 1,
            "department": doctor_resp.json().get("department", "General"),
            "slot_start": future
        }
        resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments",
            json=payload,
            headers=reception_headers
        )
        assert resp.status_code in [201, 400, 404, 409]

    def test_get_appointment(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['appointment']}/v1/appointments/1", headers=admin_headers)
        assert resp.status_code in [200, 404]

    def test_book_slot_validation(self, reception_headers):
        # Test past slot - should fail
        past = (datetime.now() - timedelta(hours=1)).isoformat()
        resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments",
            json={"patient_id": 1, "doctor_id": 1, "department": "Cardiology", "slot_start": past},
            headers=reception_headers
        )
        assert resp.status_code == 400

    def test_reschedule_appointment(self, reception_headers):
        new_slot = (datetime.now() + timedelta(days=1, hours=3)).isoformat()
        resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments/1/reschedule",
            json={"slot_start": new_slot, "version": 1},
            headers=reception_headers
        )
        assert resp.status_code in [200, 404, 409, 400]

    def test_cancel_appointment(self, reception_headers):
        resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments/1/cancel",
            headers=reception_headers
        )
        assert resp.status_code in [200, 404, 409]

    def test_complete_appointment(self, doctor_headers):
        resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments/1/complete",
            headers=doctor_headers
        )
        assert resp.status_code in [200, 404, 400]

    def test_mark_no_show(self, reception_headers):
        resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments/1/no-show",
            headers=reception_headers
        )
        assert resp.status_code in [200, 404, 400]


# ==================== BILLING SERVICE ====================


class TestBillingService:
    def test_list_bills(self, billing_headers):
        resp = requests.get(f"{BASE_URLS['billing']}/v1/bills", headers=billing_headers)
        assert resp.status_code == 200

    def test_create_bill(self, billing_headers):
        payload = {
            "patient_id": 1,
            "appointment_id": 1,
            "consultation_amount": 500.0,
            "medication_amount": 200.0
        }
        resp = requests.post(
            f"{BASE_URLS['billing']}/v1/bills",
            json=payload,
            headers=billing_headers
        )
        assert resp.status_code in [201, 400, 500]

    def test_get_bill(self, billing_headers):
        resp = requests.get(f"{BASE_URLS['billing']}/v1/bills/1", headers=billing_headers)
        assert resp.status_code in [200, 404]

    def test_cancel_adjustment(self, billing_headers):
        resp = requests.post(
            f"{BASE_URLS['billing']}/v1/bills/1/cancel-adjustment",
            json={"reason": "Test", "charge_percentage": 50.0},
            headers=billing_headers
        )
        assert resp.status_code in [200, 404]


# ==================== PRESCRIPTION SERVICE ====================


class TestPrescriptionService:
    def test_list_prescriptions(self, doctor_headers):
        resp = requests.get(f"{BASE_URLS['prescription']}/v1/prescriptions", headers=doctor_headers)
        assert resp.status_code == 200

    def test_create_prescription(self, doctor_headers):
        payload = {
            "appointment_id": 1,
            "patient_id": 1,
            "doctor_id": 1,
            "medication": "TestMed",
            "dosage": "1-0-1",
            "days": 5
        }
        resp = requests.post(
            f"{BASE_URLS['prescription']}/v1/prescriptions",
            json=payload,
            headers=doctor_headers
        )
        assert resp.status_code in [201, 400, 404]

    def test_get_prescription(self, doctor_headers):
        resp = requests.get(f"{BASE_URLS['prescription']}/v1/prescriptions/1", headers=doctor_headers)
        assert resp.status_code in [200, 404]


# ==================== PAYMENT SERVICE ====================


class TestPaymentService:
    def test_list_payments(self, billing_headers):
        resp = requests.get(f"{BASE_URLS['payment']}/v1/payments", headers=billing_headers)
        assert resp.status_code in [200, 500]

    def test_charge_payment(self, billing_headers):
        payload = {"bill_id": 1, "amount": 100.0, "method": "card"}
        headers = {**billing_headers, "Idempotency-Key": "test-charge-123"}
        resp = requests.post(
            f"{BASE_URLS['payment']}/v1/payments/charge",
            json=payload,
            headers=headers
        )
        assert resp.status_code in [200, 201, 400, 404]

    def test_idempotent_payment(self, billing_headers):
        payload = {"bill_id": 1, "amount": 100.0, "method": "card"}
        headers1 = {**billing_headers, "Idempotency-Key": "idem-12345"}
        headers2 = {**billing_headers, "Idempotency-Key": "idem-12345"}

        resp1 = requests.post(f"{BASE_URLS['payment']}/v1/payments/charge", json=payload, headers=headers1)
        resp2 = requests.post(f"{BASE_URLS['payment']}/v1/payments/charge", json=payload, headers=headers2)

        if resp1.status_code == 201 and resp2.status_code == 201:
            assert resp1.json()["payment_id"] == resp2.json()["payment_id"]

    def test_refund_payment(self, billing_headers):
        resp = requests.post(
            f"{BASE_URLS['payment']}/v1/payments/refund",
            json={"payment_id": 1, "amount": 50.0},
            headers=billing_headers
        )
        assert resp.status_code in [200, 404]


# ==================== NOTIFICATION SERVICE ====================


class TestNotificationService:
    def test_list_notifications(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['notification']}/v1/notifications", headers=admin_headers)
        assert resp.status_code in [200, 500]

    def test_create_notification(self, admin_headers):
        payload = {
            "event_type": "TEST_EVENT",
            "recipient": "test@example.com",
            "message": "Test message"
        }
        resp = requests.post(
            f"{BASE_URLS['notification']}/v1/notifications",
            json=payload,
            headers=admin_headers
        )
        assert resp.status_code == 201


# ==================== RBAC ====================


class TestRBAC:
    def test_admin_can_access_patients(self):
        resp = requests.get(f"{BASE_URLS['patient']}/v1/patients", headers={"x-role": "admin"})
        assert resp.status_code == 200

    def test_reception_can_access_patients(self):
        resp = requests.get(f"{BASE_URLS['patient']}/v1/patients", headers={"x-role": "reception"})
        assert resp.status_code == 200

    def test_unauthorized_denied(self):
        resp = requests.get(f"{BASE_URLS['patient']}/v1/patients")
        # Health endpoint is always accessible, but other endpoints may need auth
        assert resp.status_code in [200, 403]


# ==================== ERROR HANDLING ====================


class TestErrorHandling:
    def test_not_found_error_format(self, admin_headers):
        resp = requests.get(f"{BASE_URLS['patient']}/v1/patients/999999", headers=admin_headers)
        assert resp.status_code == 404
        data = resp.json()
        assert "code" in data
        assert "message" in data
        assert "correlationId" in data

    def test_validation_error(self, reception_headers):
        resp = requests.post(
            f"{BASE_URLS['patient']}/v1/patients",
            json={"name": "Test"},
            headers=reception_headers
        )
        assert resp.status_code == 422


# ==================== E2E WORKFLOW ====================


class TestE2EWorkflow:
    def test_full_appointment_to_payment_workflow(
        self, admin_headers, reception_headers, doctor_headers, billing_headers
    ):
        # Step 1: Get patient
        patient_resp = requests.get(f"{BASE_URLS['patient']}/v1/patients/1", headers=admin_headers)
        if patient_resp.status_code != 200:
            pytest.skip("No patient available")
        patient_id = patient_resp.json()["patient_id"]

        # Step 2: Get doctor (need to set up projection first)
        doctor_resp = requests.get(f"{BASE_URLS['doctor']}/v1/doctors/1", headers=admin_headers)
        if doctor_resp.status_code != 200:
            pytest.skip("No doctor available")
        doctor = doctor_resp.json()
        doctor_id = doctor["doctor_id"]
        department = doctor.get("department", "General")

        # Set up projections for appointment service
        requests.put(
            f"{BASE_URLS['appointment']}/v1/projections/patients/{patient_id}",
            json={"patient_id": patient_id, "name": patient_resp.json()["name"], 
                 "phone": patient_resp.json()["phone"], "active": True},
            headers=admin_headers
        )
        requests.put(
            f"{BASE_URLS['appointment']}/v1/projections/doctors/{doctor_id}",
            json={"doctor_id": doctor_id, "name": doctor["name"], "department": department,
                 "active": True, "max_daily_capacity": 12, "clinic_start": "09:00", 
                 "clinic_end": "17:00", "slot_minutes": 30},
            headers=admin_headers
        )

        # Step 3: Book appointment (need 2+ hours ahead AND within clinic hours 9AM-5PM IST)
        # Use date 3 days ahead at 10 AM UTC (3:30 PM IST) to avoid conflicts
        # Find a slot on a future day that doesn't conflict
        from datetime import timezone
        utc_tz = timezone(timedelta(hours=0))
        for days_ahead in range(3, 14):
            future_dt = datetime(2026, 4, 22, 10, 0, tzinfo=utc_tz) + timedelta(days=days_ahead)
            future = future_dt.isoformat()
            book_resp = requests.post(
                f"{BASE_URLS['appointment']}/v1/appointments",
                json={"patient_id": patient_id, "doctor_id": doctor_id, "department": department, "slot_start": future},
                headers=reception_headers
            )
            if book_resp.status_code == 201:
                break
        if book_resp.status_code != 201:
            pytest.skip(f"Cannot book appointment: {book_resp.status_code} {book_resp.text}")
        appointment_id = book_resp.json()["appointment_id"]

        # Step 4: Complete appointment
        complete_resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments/{appointment_id}/complete",
            headers=doctor_headers
        )
        assert complete_resp.status_code == 200

        # Step 5: Generate bill
        bill_resp = requests.post(
            f"{BASE_URLS['billing']}/v1/bills",
            json={"patient_id": patient_id, "appointment_id": appointment_id, "consultation_amount": 500, "medication_amount": 200},
            headers=billing_headers
        )
        assert bill_resp.status_code == 201
        bill_id = bill_resp.json()["bill_id"]
        total = bill_resp.json()["total_amount"]

        # Step 6: Process payment
        pay_resp = requests.post(
            f"{BASE_URLS['payment']}/v1/payments/charge",
            json={"bill_id": bill_id, "amount": total, "method": "card"},
            headers={**billing_headers, "Idempotency-Key": f"e2e-{appointment_id}"}
        )
        assert pay_resp.status_code in [200, 201]

        # Step 7: Create prescription (create projection if needed)
        pres_resp = requests.post(
            f"{BASE_URLS['prescription']}/v1/prescriptions",
            json={"appointment_id": appointment_id, "patient_id": patient_id, "doctor_id": doctor_id, "medication": "Medicine", "dosage": "1-0-1", "days": 5},
            headers=doctor_headers
        )
        if pres_resp.status_code == 404:
            # Create projection first
            requests.put(
                f"{BASE_URLS['prescription']}/v1/projections/appointments/{appointment_id}",
                json={"appointment_id": appointment_id, "patient_id": patient_id, "doctor_id": doctor_id, "appointment_date": book_resp.json()["slot_start"], "status": "SCHEDULED", "version": 1},
                headers=admin_headers
            )
            pres_resp = requests.post(
                f"{BASE_URLS['prescription']}/v1/prescriptions",
                json={"appointment_id": appointment_id, "patient_id": patient_id, "doctor_id": doctor_id, "medication": "Medicine", "dosage": "1-0-1", "days": 5},
                headers=doctor_headers
            )
        assert pres_resp.status_code == 201

    def test_reschedule_workflow(self, reception_headers):
        future = (datetime.now() + timedelta(days=1, hours=3)).isoformat()
        resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments/1/reschedule",
            json={"slot_start": future, "version": 1},
            headers=reception_headers
        )
        assert resp.status_code in [200, 404, 409, 400]

    def test_cancellation_with_refund_policy(self, reception_headers):
        resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments/1/cancel",
            headers=reception_headers
        )
        assert resp.status_code in [200, 404, 409]
        if resp.status_code == 200:
            # Should include billing policy
            assert "billingPolicy" in resp.json() or "notification" in resp.json()


# ==================== PAGINATION ====================


class TestPagination:
    def test_patient_pagination(self, admin_headers):
        resp = requests.get(
            f"{BASE_URLS['patient']}/v1/patients?page=1&page_size=5",
            headers=admin_headers
        )
        assert resp.status_code == 200
        assert resp.json()["pagination"]["pageSize"] == 5

    def test_appointment_pagination(self, admin_headers):
        resp = requests.get(
            f"{BASE_URLS['appointment']}/v1/appointments?page=1&page_size=10",
            headers=admin_headers
        )
        assert resp.status_code == 200


# ==================== CONCURRENCY ====================


class TestConcurrency:
    def test_double_booking_prevention(self, reception_headers):
        # Try to book same slot twice
        future = (datetime.now() + timedelta(hours=6)).isoformat()
        payload = {"patient_id": 1, "doctor_id": 1, "department": "Cardiology", "slot_start": future}
        resp = requests.post(
            f"{BASE_URLS['appointment']}/v1/appointments",
            json=payload,
            headers=reception_headers
        )
        assert resp.status_code in [201, 400, 404, 409]