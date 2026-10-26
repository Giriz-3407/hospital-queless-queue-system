# Architecture Specification

## Queueless Smart Hospital Queue Management System

### 1. High-Level System Architecture

The Queueless Smart Hospital system is built following a modular, clean, three-tier architecture that decouples the frontend client, backend application logic, and database persistence layer.

```
┌─────────────────────────────────────────────────────────────┐
│                       Client Layer                          │
│  React 18 + TypeScript + Vite + Tailwind CSS + Lucide       │
│  (Patient Queue Tracking, Staff Consultation Management)   │
└──────────────────────────────┬──────────────────────────────┘
                               │  REST API (JSON / HTTP)
                               │  JWT Bearer Authentication
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Application Layer                │
│                   Flask (Python 3.10+ / 3.14)               │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ Routes & Blueprints (/api/v1/auth, queues, etc.)    │   │
│   └──────────────────────────┬──────────────────────────┘   │
│                              │                              │
│   ┌──────────────────────────▼──────────────────────────┐   │
│   │ Middleware (JWT Verification, Role-Based Access)    │   │
│   └──────────────────────────┬──────────────────────────┘   │
│                              │                              │
│   ┌──────────────────────────▼──────────────────────────┐   │
│   │ Validation Layer (Pydantic Schemas)                 │   │
│   └──────────────────────────┬──────────────────────────┘   │
│                              │                              │
│   ┌──────────────────────────▼──────────────────────────┐   │
│   │ Service Layer (Business Logic & Queue Engine)       │   │
│   └──────────────────────────┬──────────────────────────┘   │
│                              │                              │
│   ┌──────────────────────────▼──────────────────────────┐   │
│   │ Repository Layer (Data Access & Projections)        │   │
│   └──────────────────────────┬──────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────┘
                               │  PyMongo Driver
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Database Layer                        │
│         MongoDB (Local Standalone or MongoDB Atlas)         │
│  Collections: users, departments, queues (Indexed)          │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. Separation of Concerns & Layer Responsibilities

1. **Routes Layer (`backend/app/routes/`)**
   - Implements modular Flask Blueprints registered with `/api/v1`.
   - Responsible strictly for HTTP protocol concerns: extracting route parameters, request payloads, query strings, and generating HTTP responses using standardized JSON response envelopes.

2. **Middleware & Security Layer (`backend/app/middleware/`)**
   - `@jwt_required`: Decodes and validates cryptographic signatures and expiration of JWT tokens. Attaches claims to `request.current_user`.
   - `@roles_required(*roles)`: Enforces role-based permissions (`patient`, `doctor`, `staff`, `admin`).
   - `register_error_handlers`: Intercepts validation errors, database timeouts, and HTTP errors to produce clean, safe JSON error payloads without leaking stack traces or credentials.

3. **Validation Layer (`backend/app/schemas/`)**
   - Uses Pydantic v2 schemas (`UserRegisterSchema`, `JoinQueueSchema`, `QueueStatusUpdateSchema`, etc.) to enforce strict typing, sanitize string inputs, validate email formats, and verify valid MongoDB ObjectId hex representations before passing data to the service layer.

4. **Service Layer (`backend/app/services/`)**
   - Encapsulates hospital business logic and domain workflows.
   - Computes dynamic queue positions, estimates waiting times, coordinates user sessions, and verifies patient ownership rules.
   - Prevents patients from holding multiple concurrent active tickets in the same clinic.

5. **Repository Layer (`backend/app/repositories/`)**
   - Handles low-level MongoDB queries using PyMongo.
   - Manages document conversion, timestamps (`created_at`, `updated_at`), sequential ticket generation (`CARD-001`, `GEN-002`), and collection aggregations.

6. **Database Connection Manager (`backend/app/database/connection.py`)**
   - Lazy connection pool with health ping capabilities and automatic reconnection handling.
   - Gracefully handles disconnected database states without terminating the web application, enabling the health check endpoint to report service degradation.

---

### 3. Virtual Queue State Machine

Each patient queue ticket transitions through deterministic states:

```
                  ┌──────────────┐
                  │    Join      │
                  │ Virtual Queue│
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐      Patient / Staff
                  │   WAITING    ├───────────────────────► CANCELLED
                  └──────┬───────┘
                         │
           Doctor calls  │
           patient next  ▼
                  ┌──────────────┐      Patient fails
                  │      IN      ├──────to show up───────► NO_SHOW
                  │ CONSULTATION │
                  └──────┬───────┘
                         │
     Doctor finishes     │
       consultation      ▼
                  ┌──────────────┐
                  │  COMPLETED   │
                  └──────────────┘
```

#### Real-Time Position & Wait Calculation Algorithm:
- When a patient checks their ticket:
  1. The system counts how many tickets in the same department are in status `"waiting"` with a creation timestamp prior to the current ticket (`count_waiting_before`).
  2. `live_position = count_waiting_before + 1`.
  3. `live_estimated_wait_minutes = live_position * department.avg_consultation_time`.
  4. The system identifies the ticket currently marked `"in_consultation"` for that department and surfaces its ticket number (`currently_serving_ticket`).

---

### 4. Data Security & Access Control

1. **Password Hashing**: Passwords are never stored in plaintext. They are hashed using `werkzeug.security.generate_password_hash` utilizing modern algorithms (`scrypt` / `pbkdf2:sha256`) with unique per-password salts.
2. **JWT Authentication**: Tokens are signed using HMAC-SHA256 with a dedicated `JWT_SECRET_KEY` and enforce expiration timestamps (`exp`).
3. **Queue Data Isolation**:
   - Patients can only view or cancel queue tickets associated with their authenticated `user_id` (`sub` claim).
   - Any attempt by Patient A to query or cancel Patient B's ticket ID triggers a `403 Forbidden` response and an audit log event.
   - Doctors, hospital staff, and administrators are permitted to view and manage queues across all departments.
4. **CORS Restrictions**: Flask-CORS is strictly configured to only accept cross-origin requests from the designated frontend host (`FRONTEND_ORIGIN`).

---

### 5. MongoDB Database Schema & Index Strategy

#### Collections:

1. **`users`**
   - `_id`: ObjectId
   - `email`: String (Unique, Indexed)
   - `password_hash`: String
   - `name`: String
   - `role`: String (`patient`, `doctor`, `staff`, `admin`) (Indexed)
   - `phone`: String (Optional)
   - `created_at`: Date
   - `updated_at`: Date

2. **`departments`**
   - `_id`: ObjectId
   - `name`: String
   - `code`: String (Unique, Indexed, e.g. `CARD`, `GEN`)
   - `description`: String
   - `avg_consultation_time`: Integer (minutes, default 15)
   - `is_active`: Boolean (Indexed)
   - `created_at`: Date

3. **`queues`**
   - `_id`: ObjectId
   - `department_id`: ObjectId (Indexed compound with `status`)
   - `department_name`: String
   - `department_code`: String
   - `patient_id`: ObjectId (Indexed compound with `status`)
   - `patient_name`: String
   - `ticket_number`: String (Indexed, e.g. `CARD-001`)
   - `position`: Integer
   - `estimated_wait_minutes`: Integer
   - `status`: String (`waiting`, `in_consultation`, `completed`, `cancelled`, `no_show`)
   - `reason`: String (Optional)
   - `called_at`: Date (Optional)
   - `completed_at`: Date (Optional)
   - `created_at`: Date (Indexed descending for FIFO ordering)
   - `updated_at`: Date

#### Created Indexes:
- `users`:
  - `idx_users_email_unique`: `{ email: 1 }` (unique)
  - `idx_users_role`: `{ role: 1 }`
- `departments`:
  - `idx_departments_code_unique`: `{ code: 1 }` (unique)
  - `idx_departments_is_active`: `{ is_active: 1 }`
- `queues`:
  - `idx_queues_department_status`: `{ department_id: 1, status: 1 }`
  - `idx_queues_patient_status`: `{ patient_id: 1, status: 1 }`
  - `idx_queues_ticket_number`: `{ ticket_number: 1 }`
  - `idx_queues_created_at`: `{ created_at: -1 }`
