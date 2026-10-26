# Development Setup & Installation Guide

## Queueless Smart Hospital Queue Management System

This guide walks you through setting up, configuring, seeding, testing, and running the Queueless Smart Hospital application on your local machine.

---

## 1. Prerequisites

Ensure the following tools are installed on your workstation:
- **Node.js**: v18.0.0 or higher (v24.x tested and confirmed)
- **npm**: v9.0.0 or higher (v11.x tested and confirmed)
- **Python**: v3.10 to v3.14 (v3.14.6 tested and confirmed)
- **Git**: v2.30 or higher
- **MongoDB**: A running local MongoDB Community Server instance (`mongodb://127.0.0.1:27017/`) or a free MongoDB Atlas cluster connection string.

---

## 2. Database Configuration

### Option A: Local MongoDB (Default & Recommended)
Verify that your local MongoDB server is active:
```powershell
# Windows PowerShell
Get-Service -Name *mongo*

# Linux / macOS
sudo systemctl status mongod
```
The default backend `.env` is configured to connect to:
```env
MONGODB_URI=mongodb://127.0.0.1:27017/
MONGODB_DATABASE=queueless_hospital
```

### Option B: MongoDB Atlas (Cloud)
1. Create a free M0 cluster on [cloud.mongodb.com](https://cloud.mongodb.com).
2. Under **Network Access**, whitelist your IP address.
3. Under **Database Access**, create a database user.
4. Set `MONGODB_URI` in `backend/.env`:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DATABASE=queueless_hospital
   ```

---

## 3. Environment Variables Configuration

### Backend Configuration (`backend/.env`)
Copy `backend/.env.example` to `backend/.env`:
```powershell
cp backend/.env.example backend/.env
```

| Variable | Description | Default / Example |
|---|---|---|
| `MONGODB_URI` | MongoDB connection URI (local or Atlas) | `mongodb://127.0.0.1:27017/` |
| `MONGODB_DATABASE` | Target database name | `queueless_hospital` |
| `SECRET_KEY` | Flask session cryptographic secret | `dev-secret-key-queueless-2026` |
| `JWT_SECRET_KEY` | Key used to sign HMAC-SHA256 JWT tokens | `dev-jwt-secret-key-queueless-2026` |
| `ACCESS_TOKEN_EXPIRES_MINUTES` | Token expiration duration | `60` |
| `FRONTEND_ORIGIN` | Allowed CORS origin | `http://localhost:5173` |
| `FLASK_HOST` | Host IP for Flask server | `127.0.0.1` |
| `FLASK_PORT` | Port for Flask server | `5000` |
| `FLASK_DEBUG` | Enable debug mode | `true` |

### Frontend Configuration (`frontend/.env`)
Copy `frontend/.env.example` to `frontend/.env`:
```powershell
cp frontend/.env.example frontend/.env
```

| Variable | Description | Default / Example |
|---|---|---|
| `VITE_API_BASE_URL` | Base endpoint for Flask backend | `http://localhost:5000/api/v1` |

---

## 4. Backend Setup, Testing & Seeding

1. Navigate to the `backend/` directory:
   ```powershell
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   # Windows PowerShell
   py -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```powershell
   pip install -r requirements.txt
   ```

4. Run the automated test suite (27 unit and integration tests):
   ```powershell
   pytest -v
   ```

5. **Provision Administrator Account (Secure CLI)**:
   The application prevents public registration of administrators. Seed the first administrator securely:
   ```powershell
   python seed.py --admin --email admin@hospital.org --password AdminPass123! --name "Hospital Administrator"
   # Or omit password to be prompted interactively with hidden input
   ```

6. **Seed Demonstration Data (Optional Development Seed)**:
   Populate sample clinical departments, synthetic doctors, patients, and queue tickets:
   ```powershell
   python seed.py --demo
   ```

7. Start the Flask API server:
   ```powershell
   python run.py
   ```
   Server starts at `http://127.0.0.1:5000`. Health check: `http://127.0.0.1:5000/health` or `http://127.0.0.1:5000/api/v1/health`.

---

## 5. Frontend Setup & Verification

1. In a separate terminal, navigate to `frontend/`:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Run TypeScript type checks and build verification:
   ```powershell
   npm run build
   ```

4. Start Vite development server:
   ```powershell
   npm run dev
   ```
   Open your browser at `http://localhost:5173`.

---

## 6. Pre-Configured Demo Credentials

| Role | Email | Password | Landing Portal |
|---|---|---|---|
| **Administrator** | `admin@hospital.org` | `AdminPass123!` | `/admin/dashboard` |
| **Doctor** | `dr.smith@hospital.org` | `DoctorPass123!` | `/doctor/dashboard` |
| **Doctor** | `dr.vance@hospital.org` | `DoctorPass123!` | `/doctor/dashboard` |
| **Patient** | `alice@example.com` | `PatientPass123!` | `/patient/dashboard` |
| **Patient** | Self-register on `/register` | (min 8 chars) | `/patient/dashboard` |

---

## 7. Known Limitations & Production Readiness

1. **Demonstration Medical Platform**: Synthetic patient and doctor identities are used for demonstration; this system is not a certified HIPAA/HL7/FHIR medical device.
2. **Real-Time Transport**: Live updates in this baseline use visibility-aware client polling (every 10 seconds while tab is active, paused when hidden). WebSocket or Server-Sent Events (SSE) can be added as a transport layer on top of the existing REST endpoints.
3. **Atomic Daily Numbering**: Daily token allocation uses MongoDB atomic `find_one_and_update` on a `counters` collection, avoiding race conditions on standalone and replica set deployments.
