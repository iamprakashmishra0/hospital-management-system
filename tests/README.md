# HMS Test Suite

## Unit Tests (No Services Required)

Run without starting services - tests import and basic logic:

```bash
cd /home/prakash/Assignment_ScalableServices/repos
python3 -m pytest tests/test_unit.py -v
```

Tests:
- Service imports (7 services)
- Endpoint structure verification
- Database seeding
- Business rules (2h lead time, 5% tax)

## End-to-End Tests (Services Must Be Running)

Start services first:

```bash
docker-compose up -d
```

Then run E2E tests:

```bash
python3 -m pytest tests/test_e2e.py -v
```

### Test Categories:

**Health & Metrics**
- All 7 services health check
- Metrics endpoint verification

**Patient Service**
- CRUD operations
- Search by name/phone
- Pagination

**Doctor Service**  
- List with department filter
- Availability check

**Appointment Service**
- Book with slot validation (2h lead time, clinic hours)
- Reschedule (max 2, not within 1hr)
- Cancel with refund policy
- Complete
- No-show handling

**Billing Service**
- Bill generation with 5% tax
- Cancellation adjustments

**Prescription Service**
- Create linked to valid appointments

**Payment Service**
- Idempotent charges
- Refunds

**E2E Workflows**
- Full appointment → complete → bill → payment → prescription
- Reschedule workflow
- Cancellation with refund

**RBAC & Error Handling**
- Role-based access control
- Error response format

### Run Specific Test Class:

```bash
python3 -m pytest tests/test_e2e.py::TestHealthEndpoints -v
python3 -m pytest tests/test_e2e.py::TestE2EWorkflow -v
python3 -m pytest tests/test_e2e.py::TestRBAC -v
```

### Manual API Testing:

```bash
# Health check
curl http://localhost:8001/health

# List patients
curl -H "x-role: admin" http://localhost:8001/v1/patients

# Create patient
curl -X POST -H "x-role: reception" -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","phone":"9999999999","dob":"1990-01-01"}' \
  http://localhost:8001/v1/patients
```