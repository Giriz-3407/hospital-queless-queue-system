# Development Setup & Installation Guide

## Queueless Smart Hospital Queue Management System

This guide walks you through setting up and running the Queueless Smart Hospital application on your local machine.

---

## 1. Prerequisites

Ensure the following tools are installed on your workstation:
- **Node.js**: v18.0.0 or higher (v24.18.0 confirmed compatible)
- **npm**: v9.0.0 or higher (v11.16.0 confirmed compatible)
- **Python**: v3.10 to v3.14 (v3.14.6 confirmed compatible)
- **Git**: v2.30 or higher
- **MongoDB**: Either a local MongoDB instance running on port 27017 or a free MongoDB Atlas cluster connection string.

---

## 2. Database Configuration

### Option A: Local MongoDB (Default)
If you have MongoDB Community Server installed locally:
1. Ensure the MongoDB service is running:
   ```powershell
   Get-Service -Name *mongo*
   ```
2. The default connection URI in `.env.example` points to:
   ```env
   MONGODB_URI=mongodb://127.0.0.1:27017/
   MONGODB_DATABASE=queueless_hospital
   ```

### Option B: MongoDB Atlas (Cloud)
1. Create a free cluster on [cloud.mongodb.com](https://cloud.mongodb.com).
2. Under **Network Access**, whitelist your IP address (or `0.0.0.0/0` for development).
3. Under **Database Access**, create a user with read and write privileges.
4. Copy your connection string into `backend/.env`:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DATABASE=queueless_hospital
   ```

---

## 3. Environment Variables Configuration

### Backend Configuration
Copy `backend/.env.example` to `backend/.env`:
```powershell
cp backend/.env.example backend/.env
```

| Variable | Description | Default / Example |
|---|---|---|
| `MONGODB_URI` | MongoDB connection URI (local or Atlas) | `mongodb://127.0.0.1:27017/` |
| `MONGODB_DATABASE` | Target database name | `queueless_hospital` |
| `SECRET_KEY` | Flask session cryptographic secret | `replace-with-a-secure-random-secret` |
| `JWT_SECRET_KEY` | Key used to sign HMAC-SHA256 JWT tokens | `replace-with-a-separate-secure-random-secret` |
| `ACCESS_TOKEN_EXPIRES_MINUTES` | Token expiration duration | `60` |
| `FRONTEND_ORIGIN` | Allowed CORS origin | `http://localhost:5173` |
| `FLASK_HOST` | Host IP for Flask server | `127.0.0.1` |
| `FLASK_PORT` | Port for Flask server | `5000` |
| `FLASK_DEBUG` | Enable debug mode | `true` |

### Frontend Configuration
Copy `frontend/.env.example` to `frontend/.env`:
```powershell
cp frontend/.env.example frontend/.env
```

| Variable | Description | Default / Example |
|---|---|---|
| `VITE_API_BASE_URL` | Base endpoint for Flask backend | `http://localhost:5000/api/v1` |

---

## 4. Backend Setup & Verification

1. Navigate to `backend/`:
   ```powershell
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```powershell
   # Windows PowerShell
   py -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Run automated test suite:
   ```powershell
   pytest
   ```
5. Start the backend development server:
   ```powershell
   python run.py
   # or on Windows launcher:
   py run.py
   ```
   Verify at: `http://127.0.0.1:5000/api/v1/health`

---

## 5. Frontend Setup & Verification

1. In a separate terminal, navigate to `frontend/`:
   ```powershell
   cd frontend
   ```
2. Install frontend packages:
   ```powershell
   npm install
   ```
3. Verify production build:
   ```powershell
   npm run build
   ```
4. Start the Vite development server:
   ```powershell
   npm run dev
   ```
   Open your browser at: `http://localhost:5173`

---

## 6. Running Concurrently (Root)

From the project root directory, you can install and start both applications simultaneously:

```powershell
# Install root orchestrator dependencies
npm install

# Run both backend and frontend concurrently
npm run dev
```

---

## 7. Pre-Seeded Clinical Departments

Upon application startup, if the database has not yet been seeded, the system automatically configures the following default clinical departments:
1. **General Medicine (`GEN`)** - 10 mins average consultation
2. **Cardiology (`CARD`)** - 20 mins average consultation
3. **Pediatrics (`PED`)** - 15 mins average consultation
4. **Orthopedics (`ORTHO`)** - 15 mins average consultation
5. **Dermatology (`DERM`)** - 12 mins average consultation
