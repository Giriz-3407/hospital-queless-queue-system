# API Documentation

## Queueless Smart Hospital Queue Management System

All API endpoints are versioned with the prefix:
```
/api/v1
```

All responses conform to standard JSON envelopes:

### Standard Success Envelope:
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "timestamp": "2026-10-27T00:00:00.000000+00:00"
}
```

### Standard Error Envelope:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of error",
    "details": null
  },
  "timestamp": "2026-10-27T00:00:00.000000+00:00"
}
```

---

## 1. System Health & Diagnostics

### `GET /api/v1/health`
Checks backend application availability and live MongoDB connectivity. Does not expose credentials or connection URIs.

- **Authentication**: None
- **Response**: `200 OK` (healthy) or `503 Service Unavailable` (degraded)
- **Response Example**:
```json
{
  "success": true,
  "message": "Service is healthy",
  "data": {
    "status": "healthy",
    "service": "Queueless Smart Hospital API",
    "version": "1.0.0",
    "uptime_seconds": 124,
    "database": {
      "status": "connected",
      "name": "queueless_hospital"
    },
    "server_time": "2026-10-27T00:15:00.000000+00:00"
  },
  "timestamp": "2026-10-27T00:15:00.000000+00:00"
}
```

---

## 2. Authentication & User Identity

### `POST /api/v1/auth/register`
Register a new patient, doctor, or staff account.

- **Authentication**: None
- **Request Body**:
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "password": "Password123!",
  "phone": "+1-555-0123",
  "role": "patient"
}
```
- **Response**: `201 Created`
```json
{
  "success": true,
  "message": "User registered successfully.",
  "data": {
    "user": {
      "id": "6adfa2be74b41371b1f4396e",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "role": "patient",
      "phone": "+1-555-0123",
      "created_at": "2026-10-27T00:20:00+00:00"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### `POST /api/v1/auth/login`
Authenticate existing credentials and retrieve JWT bearer token.

- **Authentication**: None
- **Request Body**:
```json
{
  "email": "john.doe@example.com",
  "password": "Password123!"
}
```
- **Response**: `200 OK`
```json
{
  "success": true,
  "message": "Authentication successful.",
  "data": {
    "user": {
      "id": "6adfa2be74b41371b1f4396e",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "role": "patient"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### `GET /api/v1/auth/me`
Retrieve currently authenticated user profile.

- **Authentication**: Required (`Bearer <token>`)
- **Response**: `200 OK`
```json
{
  "success": true,
  "message": "Profile retrieved successfully.",
  "data": {
    "id": "6adfa2be74b41371b1f4396e",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "role": "patient",
    "phone": "+1-555-0123"
  }
}
```

---

## 3. Hospital Departments

### `GET /api/v1/departments`
Lists all active hospital clinical departments along with live waiting count and estimated wait times.

- **Authentication**: None
- **Response**: `200 OK`
```json
{
  "success": true,
  "message": "Departments retrieved successfully.",
  "data": [
    {
      "id": "6adfa2be74b41371b1f4396f",
      "name": "General Medicine",
      "code": "GEN",
      "description": "Routine check-ups, acute minor illnesses, and primary health consultations.",
      "avg_consultation_time": 10,
      "is_active": true,
      "current_waiting": 3,
      "estimated_wait_minutes": 30
    },
    {
      "id": "6adfa2be74b41371b1f43970",
      "name": "Cardiology",
      "code": "CARD",
      "description": "Specialized heart evaluations, ECG reviews, and cardiovascular consultations.",
      "avg_consultation_time": 20,
      "is_active": true,
      "current_waiting": 1,
      "estimated_wait_minutes": 20
    }
  ]
}
```

### `POST /api/v1/departments`
Create a new clinical department.

- **Authentication**: Required (Roles: `admin`, `staff`, `doctor`)
- **Request Body**:
```json
{
  "name": "Neurology",
  "code": "NEURO",
  "description": "Brain, nerve, and spine consultations.",
  "avg_consultation_time": 25
}
```
- **Response**: `201 Created`

---

## 4. Virtual Queues & Patient Tickets

### `POST /api/v1/queues/join`
Allows an authenticated patient to join a virtual queue for a clinic.

- **Authentication**: Required (`Bearer <token>`)
- **Request Body**:
```json
{
  "department_id": "6adfa2be74b41371b1f43970",
  "reason": "Chest discomfort following mild exertion"
}
```
- **Response**: `201 Created`
```json
{
  "success": true,
  "message": "Joined virtual queue successfully.",
  "data": {
    "id": "6adfa2be74b41371b1f43981",
    "department_id": "6adfa2be74b41371b1f43970",
    "department_name": "Cardiology",
    "department_code": "CARD",
    "patient_id": "6adfa2be74b41371b1f4396e",
    "patient_name": "John Doe",
    "ticket_number": "CARD-001",
    "position": 1,
    "live_position": 1,
    "estimated_wait_minutes": 20,
    "live_estimated_wait_minutes": 20,
    "status": "waiting",
    "currently_serving_ticket": "None",
    "created_at": "2026-10-27T00:25:00+00:00"
  }
}
```

### `GET /api/v1/queues/my`
Retrieves all tickets belonging to the authenticated patient, with real-time recalculation of queue position and remaining wait time.

- **Authentication**: Required (`Bearer <token>`)
- **Response**: `200 OK`

### `GET /api/v1/queues/<queue_id>`
Retrieves a specific ticket.
- **Authorization Rule**: Patients can ONLY retrieve their own ticket. Doctors, staff, and admins can view any ticket. Attempts by other patients return `403 Forbidden`.
- **Response**: `200 OK`

### `POST /api/v1/queues/<queue_id>/cancel`
Cancels a waiting virtual queue ticket.
- **Authorization Rule**: Patients can ONLY cancel their own tickets. Tickets already completed or in consultation cannot be cancelled.
- **Response**: `200 OK`

### `GET /api/v1/queues`
Lists queues for staff management with optional filtering.
- **Authentication**: Required (Roles: `doctor`, `staff`, `admin`)
- **Query Parameters**:
  - `department_id`: Filter by department ObjectId
  - `status`: Filter by status (`waiting`, `in_consultation`, `completed`, `cancelled`, `no_show`)
- **Response**: `200 OK`

### `PATCH /api/v1/queues/<queue_id>/status`
Updates patient consultation status.
- **Authentication**: Required (Roles: `doctor`, `staff`, `admin`)
- **Request Body**:
```json
{
  "status": "in_consultation",
  "notes": "Patient called into Room 2B"
}
```
- **Response**: `200 OK`

---

## 5. Patient Profile & Overview

### `GET /api/v1/patients/me`
Retrieves patient profile, count of active tickets, past consultation summary, and recent tickets.

- **Authentication**: Required (`Bearer <token>`)
- **Response**: `200 OK`
```json
{
  "success": true,
  "message": "Patient information retrieved successfully.",
  "data": {
    "profile": { ... },
    "summary": {
      "active_tickets_count": 1,
      "past_visits_count": 3
    },
    "active_queues": [ ... ],
    "recent_queues": [ ... ]
  }
}
```
