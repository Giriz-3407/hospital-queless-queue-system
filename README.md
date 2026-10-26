# Queueless Smart Hospital Queue Management System

A production-ready MVP web application designed to eliminate crowded hospital waiting rooms. Patients join virtual queues from their personal devices, track their live queue position, and view dynamic estimated waiting times. Doctors manage consultations directly from their department console, and hospital administrators manage departments, medical providers, and system-wide queues with a complete audit trail.

---

## Architecture & Technology Stack

### Frontend
- **React 18** with **TypeScript** (Strict Mode)
- **Vite** for rapid bundling and development
- **Tailwind CSS** for healthcare UI design system
- **React Router v6** for role-protected client-side routing
- **Axios** with Bearer token injection and error normalization
- **Lucide React** for clinical iconography

### Backend
- **Python 3.10+ / 3.14** with **Flask**
- **Flask Blueprints** for versioned endpoints under `/api/v1` and `/health`
- **PyMongo** for MongoDB integration with connection pooling and timeouts
- **Pydantic v2** for request payload validation and sanitization
- **Werkzeug Security** for password hashing (`scrypt`)
- **PyJWT** for cryptographically signed HMAC-SHA256 authentication tokens
- **Pytest** for automated unit, integration, and security tests (27 passing tests)

### Database
- **MongoDB 6+** with compound indexes on email, departments, doctor assignments, daily tokens, and audit logs.

---

## Application Roles & Capabilities

### 1. Patient
- Public registration (`role: patient` enforced server-side; cannot elevate privileges).
- View available hospital departments with consultation averages and medical staff on duty.
- Join a department's virtual queue and receive an atomic sequential daily token (e.g. `GEN-001`, `CARD-002`).
- Track live queue position, number of patients ahead, and dynamic estimated wait time.
- Automated updates using visibility-aware polling (every 10s while tab is active, paused when hidden).
- Cancel active waiting tickets.
- View personal queue history (completed, cancelled, no-show).
- Strict data isolation: Patients cannot view, modify, or cancel tickets belonging to other patients.

### 2. Doctor
- Secure login to the **Doctor Consultation Console** (`/doctor/dashboard`).
- View assigned clinical department and real-time waiting queue.
- Call the next eligible waiting patient (atomic FIFO transition: `WAITING` -> `CALLED`).
- Start consultation (atomic transition: `CALLED` -> `IN_CONSULTATION`).
- Complete consultation with clinical notes (atomic transition: `IN_CONSULTATION` -> `COMPLETED`).
- Mark patient as `NO_SHOW`.
- Department isolation: Doctors cannot operate on queues outside their assigned department.

### 3. Hospital Administrator
- Secure login to the **Administrator Dashboard** (`/admin/dashboard`).
- View system metrics: active queues, departments, registered patients, and providers.
- Department Management: Create departments, edit parameters, and activate/deactivate clinical clinics.
- Doctor Management: Provision doctor credentials and assign to clinical departments; toggle availability.
- Hospital Queues Monitor: Inspect all queues across departments with status filters.
- Audit Trail: View timestamped security and workflow logs (patient registrations, queue joins, calls, consultations).

---

## State Transitions & Concurrency Safety

```
[ WAITING ] ────────► [ CALLED ] ────────► [ IN_CONSULTATION ] ────────► [ COMPLETED ]
     │                      │
     ├────────► [ CANCELLED ] (by patient)
     │                      │
     └────────► [ NO_SHOW ] ◄┘ (by doctor)
```

- **Token Allocation**: Driven by MongoDB atomic `$inc` operations in a `counters` collection keyed by `{dept_id}_{YYYY-MM-DD}` to guarantee zero duplicate tokens under concurrent load.
- **Queue State Changes**: Atomic conditional queries (e.g. `{"_id": id, "status": "WAITING"}`) ensure two simultaneous doctor requests cannot call the same patient or cause conflicting states.
- **Wait Time Estimation**:
  $$\text{estimated\_wait\_minutes} = \left\lceil \frac{\text{patients\_ahead} \times \text{avg\_consultation\_time}}{\text{effective\_available\_doctors}} \right\rceil$$
  When no doctors are currently available on duty, the system returns `null` ("Estimate unavailable") rather than presenting a misleading zero-minute wait.

---

## Quick Start & Verification

### 1. Prerequisites
- Node.js v18+ & npm
- Python 3.10+ (Python 3.14 compatible)
- Running MongoDB instance (`mongodb://127.0.0.1:27017/`)

### 2. Backend Setup & Test Suite
```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run full test suite (27 passing tests)
pytest -v

# Provision the first administrator securely (CLI)
python seed.py --admin --email admin@hospital.org --password AdminPass123! --name "Hospital Chief Admin"

# Seed sample demonstration data (departments, doctors, patients, queues)
python seed.py --demo

# Start the Flask API server
python run.py
```
Backend API will start at `http://127.0.0.1:5000` with health checks at `/health` and `/api/v1/health`.

### 3. Frontend Setup & Production Build
In a separate terminal:
```powershell
cd frontend
npm install

# Run TypeScript checks and production build
npm run build

# Start Vite development server
npm run dev
```
Frontend web application will run at `http://localhost:5173`.

---

## Pre-Seeded Demonstration Accounts

| Role | Email | Password | Console URL |
|---|---|---|---|
| **Hospital Administrator** | `admin@hospital.org` | `AdminPass123!` | `http://localhost:5173/admin/dashboard` |
| **Attending Doctor (Cardiology)** | `dr.vance@hospital.org` | `DoctorPass123!` | `http://localhost:5173/doctor/dashboard` |
| **Attending Doctor (Gen Medicine)**| `dr.smith@hospital.org` | `DoctorPass123!` | `http://localhost:5173/doctor/dashboard` |
| **Patient (Seeded)** | `alice@example.com` | `PatientPass123!` | `http://localhost:5173/patient/dashboard` |
| **Patient (Self-Register)** | Any valid email | (min 8 chars) | `http://localhost:5173/register` |

---

## API Endpoints Overview

| Category | Method | Endpoint | Access | Purpose |
|---|---|---|---|---|
| **Health** | `GET` | `/health` | Public | Service health & MongoDB ping |
| | `GET` | `/api/v1/health` | Public | Versioned health check |
| **Auth** | `POST` | `/api/v1/auth/register` | Public | Patient registration (role restricted) |
| | `POST` | `/api/v1/auth/login` | Public | Authenticate & issue JWT |
| | `GET` | `/api/v1/auth/me` | Authenticated | Current user profile |
| **Departments** | `GET` | `/api/v1/departments` | Public | Active departments with doctors & wait times |
| | `GET` | `/api/v1/departments/<id>` | Public | Single department with assigned doctors |
| | `POST` | `/api/v1/departments` | Admin | Create department |
| | `PATCH` | `/api/v1/departments/<id>` | Admin | Update department details / active status |
| | `GET` | `/api/v1/departments/<id>/queue` | Public | View active queue for department |
| **Patients** | `GET` | `/api/v1/patients/me` | Patient | Patient active queue & summary stats |
| | `GET` | `/api/v1/patients/me/queues` | Patient | Patient queue ticket history |
| **Queues** | `POST` | `/api/v1/queues/join` | Patient | Join virtual queue & generate daily token |
| | `GET` | `/api/v1/queues/my` | Patient | Retrieve patient active & past tickets |
| | `GET` | `/api/v1/queues/<id>` | Patient/Doctor | View ticket (isolated to owner if patient) |
| | `POST` | `/api/v1/queues/<id>/cancel` | Patient | Cancel pending waiting ticket |
| **Doctor** | `GET` | `/api/v1/doctor/queue` | Doctor | Active queue, current called, & clinic stats |
| | `POST` | `/api/v1/doctor/queue/next` | Doctor | Call next patient (WAITING -> CALLED) |
| | `POST` | `/api/v1/doctor/queue/<id>/start` | Doctor | Start consultation (CALLED -> IN_CONSULTATION) |
| | `POST` | `/api/v1/doctor/queue/<id>/complete`| Doctor | Complete consultation (IN_CONSULTATION -> COMPLETED) |
| | `POST` | `/api/v1/doctor/queue/<id>/no-show` | Doctor | Mark patient as NO_SHOW |
| **Admin** | `GET` | `/api/v1/admin/dashboard` | Admin | Hospital system statistics |
| | `GET` | `/api/v1/admin/users` | Admin | List users with role filter & pagination |
| | `GET` | `/api/v1/admin/doctors` | Admin | List doctors with department assignments |
| | `POST` | `/api/v1/admin/doctors` | Admin | Provision doctor user & department profile |
| | `PATCH` | `/api/v1/admin/doctors/<id>` | Admin | Update doctor availability & assignment |
| | `POST` | `/api/v1/admin/departments` | Admin | Create new clinical department |
| | `PATCH` | `/api/v1/admin/departments/<id>`| Admin | Update / activate / deactivate department |
| | `GET` | `/api/v1/admin/queues` | Admin | All hospital queue tickets with filters |
| | `GET` | `/api/v1/admin/audit-logs` | Admin | Audit activity logs with pagination |

---

## Automated Verification Suite

Run all tests in `backend/`:
```powershell
pytest -v
```

Tests cover:
- Registration, validation, duplicate prevention, and privilege escalation prevention.
- Secure password hashing and authentication token issuance.
- Role-based access control (patient, doctor, administrator).
- Sequential atomic daily token allocation.
- Dynamic queue position and patients ahead calculation.
- Waiting time estimation with doctor availability adjustments.
- Patient data isolation and cross-patient access rejection.
- Complete doctor workflow: call next -> start consultation -> complete consultation.
- Doctor department isolation (cannot operate on tickets outside assigned clinic).
- Administrator operations: department management, doctor provisioning, queues monitor, audit trail.

---

## Documentation Links
- Detailed Setup: [`docs/setup.md`](docs/setup.md)
- REST API Specification: [`docs/api.md`](docs/api.md)
- System Architecture: [`docs/architecture.md`](docs/architecture.md)
