# Queueless Smart Hospital Queue Management System

A modern, web-based hospital queue management system designed to eliminate crowded waiting rooms. Patients can join virtual queues from their devices, track live queue positions, and view dynamic estimated waiting times without waiting physically in clinic waiting areas. Medical personnel and hospital staff manage consultations through an authenticated dashboard.

---

## Key Features

- **Virtual Queue Joining**: Patients select a hospital department and join the queue with automated ticket generation (e.g. `CARD-001`, `GEN-002`).
- **Real-Time Position Tracking**: Dynamic queue position calculation and wait time estimation based on patients ahead.
- **Fair FIFO Queueing**: First-in, first-out sequencing per clinical specialty.
- **Patient Isolation**: Patients are strictly restricted to their own tickets; cross-patient data access is denied.
- **Hospital Staff Dashboard**: Doctors and staff can view queues, call the next patient, complete consultations, or mark no-shows.
- **MongoDB Database**: Indexed for fast lookups by department, patient, ticket number, and status; compatible with local MongoDB and MongoDB Atlas.
- **Clean Architecture**: Decoupled routes, services, repositories, schemas, models, and middleware.

---

## Technology Stack

### Frontend
- **React 18** with **TypeScript**
- **Vite** for fast builds and hot module replacement
- **Tailwind CSS** for responsive medical UI design
- **React Router v6** for client-side routing and protected routes
- **Axios** with Bearer token interceptor and unified error handling
- **Lucide React** for modern clinical iconography

### Backend
- **Python 3.10+ / 3.14** with **Flask**
- **Flask Blueprints** for modular `/api/v1` routing
- **Flask-CORS** restricted to frontend origin
- **PyMongo** for MongoDB persistence and ObjectId management
- **Pydantic v2** for input validation and normalization
- **Werkzeug Security** for password hashing (`scrypt`/`pbkdf2`)
- **PyJWT** for token-based authentication and role-based access control (RBAC)
- **Pytest** for automated unit and integration tests

### Database
- **MongoDB 6+** (Supports local instances and MongoDB Atlas clusters)

---

## Project Structure

```
queueless-smart-hospital/
│
├── frontend/                     # React + TypeScript + Vite + Tailwind frontend
│   ├── public/                   # Static assets & favicon
│   ├── src/
│   │   ├── assets/               # Branding assets
│   │   ├── components/
│   │   │   ├── common/           # Navbar, Footer, ProtectedRoute, StatusBadge
│   │   │   ├── layout/           # MainLayout, DashboardLayout
│   │   │   └── ui/               # Button, Card, Input, Select, Modal, Alert
│   │   ├── pages/
│   │   │   ├── public/           # HomePage, LoginPage, RegisterPage, NotFoundPage
│   │   │   ├── patient/          # PatientDashboardPage, JoinQueuePage, MyQueuePage
│   │   │   └── staff/            # StaffDashboardPage
│   │   ├── routes/               # AppRoutes (declarative route registry)
│   │   ├── services/             # Axios API client, auth, queue, department services
│   │   ├── hooks/                # useAuth, useQueue polling hook
│   │   ├── contexts/             # AuthContext (state, tokens, session hydration)
│   │   ├── types/                # TypeScript interfaces (Auth, Queue, Api)
│   │   ├── utils/                # Date/wait formatters, localStorage helpers
│   │   ├── App.tsx               # Root component
│   │   ├── main.tsx              # Application entry point
│   │   └── index.css             # Tailwind base & custom utility styles
│   ├── .env.example              # Frontend environment template
│   ├── package.json              # Frontend dependencies
│   ├── tsconfig.json             # TypeScript compiler configuration
│   └── vite.config.ts            # Vite bundler configuration
│
├── backend/                      # Python Flask modular backend
│   ├── app/
│   │   ├── __init__.py           # Application factory (create_app)
│   │   ├── config.py             # Class-based environment configuration
│   │   ├── extensions.py         # CORS and MongoDB extensions
│   │   ├── database/             # MongoDB connection manager and index definitions
│   │   │   ├── connection.py     # Connection lifecycle and ObjectId serializers
│   │   │   └── indexes.py        # Unique and compound index creation
│   │   ├── models/               # User, Department, QueueTicket data models
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── repositories/         # MongoDB CRUD repositories
│   │   ├── services/             # Business logic layer (queue position, wait time)
│   │   ├── routes/               # Modular Flask Blueprints (/api/v1)
│   │   │   ├── health.py         # Health check and DB ping
│   │   │   ├── auth.py           # Register, login, profile (/auth/me)
│   │   │   ├── departments.py    # Department listing and management
│   │   │   ├── queues.py         # Queue join, my queues, status updates
│   │   │   └── patients.py       # Patient summary and history
│   │   ├── middleware/           # JWT verification, RBAC, error handlers
│   │   └── utils/                # Security hashing, tokens, API response envelopes
│   ├── tests/                    # Pytest unit and integration test suite
│   ├── run.py                    # Server startup script
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Backend environment template
│   └── pytest.ini                # Pytest configuration
│
├── docs/                         # Technical documentation
│   ├── architecture.md           # System architecture, state machine, data isolation
│   ├── api.md                    # Complete REST API specification
│   └── setup.md                  # Detailed environment setup guide
│
├── .gitignore                    # Git ignore rules for venv, node_modules, secrets
├── README.md                     # Project overview and instructions
└── package.json                  # Root development orchestrator
```

---

## Quick Start Guide

### 1. Configure Environment Files

Create `.env` from the provided `.env.example` templates:

```powershell
# In backend/
cp backend/.env.example backend/.env

# In frontend/
cp frontend/.env.example frontend/.env
```

### 2. Backend Setup

```powershell
cd backend

# Create virtual environment
py -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# (macOS/Linux: source venv/bin/activate)

# Install dependencies
pip install -r requirements.txt

# Run backend tests
pytest

# Start the Flask API server
python run.py
```
Backend API will start at `http://127.0.0.1:5000` with health check at `http://127.0.0.1:5000/api/v1/health`.

### 3. Frontend Setup

In a new terminal:
```powershell
cd frontend

# Install dependencies
npm install

# Build check
npm run build

# Start development server
npm run dev
```
Frontend web application will run at `http://localhost:5173`.

### 4. Running Concurrently (Root)

From the project root:
```powershell
npm install
npm run dev
```

---

## Verification & Test Results

| Component | Status | Details |
|---|---|---|
| **Backend Dependencies** | Verified | Installed in `backend/venv` with Python 3.14 compatible wheels |
| **Backend Test Suite** | Passed (12/12) | Auth, registration, password hashing, JWT, queue lifecycle, patient isolation |
| **MongoDB Connectivity** | Verified | Connected to `mongodb://127.0.0.1:27017/` database `queueless_hospital` |
| **MongoDB Indexes** | Verified | Indexes created for `users`, `departments`, `queues` |
| **Health Check Endpoint** | 200 OK | Verified `/api/v1/health` reports status `healthy` with database `connected` |
| **Frontend Dependencies** | Verified | Installed cleanly via `npm install` |
| **Frontend TypeScript Build**| Passed | Built cleanly in 2.29s with zero errors (`npm run build`) |
| **Git Repository** | Initialized | Ignored paths verified (.venv, node_modules, .env, dist, caches) |

---

## API Summary

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/health` | Public | Service health & database connectivity |
| `POST` | `/api/v1/auth/register` | Public | Register new patient or staff |
| `POST` | `/api/v1/auth/login` | Public | Authenticate and obtain JWT |
| `GET` | `/api/v1/auth/me` | Authenticated | Retrieve current user profile |
| `GET` | `/api/v1/departments` | Public | List active departments & live wait times |
| `POST` | `/api/v1/departments` | Staff/Admin | Create new clinical department |
| `POST` | `/api/v1/queues/join` | Patient | Join virtual queue & get ticket |
| `GET` | `/api/v1/queues/my` | Patient | Get patient's live active & past tickets |
| `GET` | `/api/v1/queues/<id>` | Patient/Staff | Retrieve ticket (isolated by patient ownership) |
| `POST` | `/api/v1/queues/<id>/cancel` | Patient/Staff | Cancel waiting ticket |
| `GET` | `/api/v1/queues` | Staff/Doctor | List all queues with filtering |
| `PATCH` | `/api/v1/queues/<id>/status` | Staff/Doctor | Update consultation status |
| `GET` | `/api/v1/patients/me` | Patient | Get patient summary and visit history |

See [`docs/api.md`](docs/api.md) for full request/response schemas.
See [`docs/architecture.md`](docs/architecture.md) for architecture details.
See [`docs/setup.md`](docs/setup.md) for setup guide.
