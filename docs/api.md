# REST API Specification

## Queueless Smart Hospital Queue Management System

All endpoints conform to standardized JSON response envelopes.
Base URL prefix: `/api/v1` (with root `/health` also available).

---

## 1. Diagnostics & Health

### `GET /health` or `GET /api/v1/health`
Checks application status and active MongoDB connectivity.
- **Access**: Public
- **Response**: `200 OK` (healthy) or `503 Service Unavailable` (degraded)

---

## 2. Authentication

### `POST /api/v1/auth/register`
Registers a new patient account. Role is strictly restricted to `patient`.
- **Access**: Public
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "password": "Password123!",
    "phone": "+1-555-0199"
  }
  ```
- **Response**: `201 Created` with sanitized user object and JWT access token.

### `POST /api/v1/auth/login`
Authenticates existing user credentials and returns signed JWT access token.
- **Access**: Public
- **Request Body**:
  ```json
  {
    "email": "jane.doe@example.com",
    "password": "Password123!"
  }
  ```
- **Response**: `200 OK` with user profile and token.

### `GET /api/v1/auth/me`
Retrieves authenticated profile of the current user.
- **Access**: Bearer Token required
- **Response**: `200 OK` with sanitized user document (and doctor profile if applicable).

---

## 3. Departments

### `GET /api/v1/departments`
Lists hospital clinical departments with live queue stats, assigned doctors, and estimated wait times.
- **Access**: Public
- **Query Params**: `all=true` to include inactive departments.

### `GET /api/v1/departments/<department_id>`
Retrieves single department details including medical providers and active stats.
- **Access**: Public

### `POST /api/v1/departments`
Creates a new clinical department.
- **Access**: Admin (or Doctor)
- **Request Body**:
  ```json
  {
    "name": "Neurology",
    "code": "NEURO",
    "description": "Brain and nerve diagnostic care",
    "avg_consultation_time": 20,
    "is_active": true
  }
  ```

### `PATCH /api/v1/departments/<department_id>`
Updates department information or toggles active status.
- **Access**: Admin
- **Request Body**: Partial department fields.

### `GET /api/v1/departments/<department_id>/queue`
Lists active waiting tickets for a specific department.
- **Access**: Public

---

## 4. Patient Operations

### `GET /api/v1/patients/me`
Summary of authenticated patient's active queue visits, past visits count, and profile.
- **Access**: Patient

### `GET /api/v1/patients/me/queues`
Full historical list of tickets belonging to the patient.
- **Access**: Patient

---

## 5. Queue Management

### `POST /api/v1/queues/join`
Allows patient to join a virtual queue. Generates an atomic sequential daily ticket.
- **Access**: Patient
- **Request Body**:
  ```json
  {
    "department_id": "6adfa899d2bf211a297e0fcf",
    "reason": "Persistent migraine"
  }
  ```
- **Response**: `201 Created` with ticket number, position, and live estimated wait time.

### `GET /api/v1/queues/my`
Retrieves all tickets belonging to the authenticated patient with real-time recalculations.
- **Access**: Patient

### `GET /api/v1/queues/<queue_id>`
Retrieves single queue ticket. Strictly enforced patient ownership (patients cannot view others).
- **Access**: Patient (owner) or Doctor/Admin

### `POST /api/v1/queues/<queue_id>/cancel`
Cancels a pending queue ticket (only if status is `WAITING`).
- **Access**: Patient (owner) or Admin

---

## 6. Doctor Workflow

### `GET /api/v1/doctor/queue`
Retrieves doctor's assigned clinic queue, currently called patient, in consultation patient, and waiting queue.
- **Access**: Doctor (assigned to department)

### `POST /api/v1/doctor/queue/next`
Atomically calls the next eligible patient (`WAITING` -> `CALLED`).
- **Access**: Doctor

### `POST /api/v1/doctor/queue/<queue_id>/start`
Marks called patient as in consultation (`CALLED` -> `IN_CONSULTATION`).
- **Access**: Doctor (department validated)

### `POST /api/v1/doctor/queue/<queue_id>/complete`
Marks consultation as completed (`IN_CONSULTATION` -> `COMPLETED`).
- **Access**: Doctor (department validated)
- **Request Body**: `{"notes": "Patient advised rest"}` (optional)

### `POST /api/v1/doctor/queue/<queue_id>/no-show`
Marks patient as no-show (`CALLED` or `WAITING` -> `NO_SHOW`).
- **Access**: Doctor (department validated)
- **Request Body**: `{"notes": "Unresponsive"}` (optional)

---

## 7. Administrator Operations

### `GET /api/v1/admin/dashboard`
Returns system statistics: total users, patients, doctors, departments, active tickets, and completions.
- **Access**: Admin

### `GET /api/v1/admin/users`
Lists user accounts with optional `role` filtering and pagination (`limit`, `skip`).
- **Access**: Admin

### `GET /api/v1/admin/doctors`
Lists doctor accounts with department assignments and availability.
- **Access**: Admin

### `POST /api/v1/admin/doctors`
Provisions a doctor user account and links them to a clinical department.
- **Access**: Admin
- **Request Body**:
  ```json
  {
    "name": "Dr. Sarah Smith",
    "email": "dr.smith@hospital.org",
    "password": "DoctorPassword123!",
    "department_id": "6adfa899d2bf211a297e0fcf",
    "specialty": "Internal Medicine",
    "phone": "+1-555-0100"
  }
  ```

### `PATCH /api/v1/admin/doctors/<doctor_id>`
Updates doctor department assignment, specialty, or availability status (`is_available: true/false`).
- **Access**: Admin

### `POST /api/v1/admin/departments`
Admin creates a new clinical department.
- **Access**: Admin

### `PATCH /api/v1/admin/departments/<department_id>`
Admin activates, deactivates, or modifies department settings.
- **Access**: Admin

### `GET /api/v1/admin/queues`
System-wide queue viewer across all departments with `department_id` and `status` filters and pagination.
- **Access**: Admin

### `GET /api/v1/admin/audit-logs`
Security and operational audit trail with pagination and filters (`action`, `entity_type`).
- **Access**: Admin
