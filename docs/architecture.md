# System Architecture Specification

## Queueless Smart Hospital Queue Management System

### 1. High-Level Architecture Overview

The Queueless Smart Hospital system is built as a three-tier, decoupled architecture comprising a TypeScript React client, an authenticated Python Flask REST API backend, and a high-performance indexed MongoDB persistence layer.

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Layer                           │
│        React 18 + TypeScript + Vite + Tailwind CSS + Lucide     │
│   (Patient Dashboard, Doctor Console, Admin Control Portal)     │
└────────────────────────────────┬────────────────────────────────┘
                                 │  REST API (JSON / HTTP)
                                 │  JWT Bearer Authentication
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Application Layer                    │
│                   Flask (Python 3.10+ / 3.14)                   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Routes & Blueprints (/api/v1/auth, queues, doctor, admin)│   │
│   └────────────────────────────┬────────────────────────────┘   │
│                                │                                │
│   ┌────────────────────────────▼────────────────────────────┐   │
│   │ Middleware (JWT Verification, Role-Based Access Decs)   │   │
│   └────────────────────────────┬────────────────────────────┘   │
│                                │                                │
│   ┌────────────────────────────▼────────────────────────────┐   │
│   │ Validation Layer (Pydantic v2 Models)                   │   │
│   └────────────────────────────┬────────────────────────────┘   │
│                                │                                │
│   ┌────────────────────────────▼────────────────────────────┐   │
│   │ Service Layer (Queue Engine, FIFO ordering, Wait Est)   │   │
│   └────────────────────────────┬────────────────────────────┘   │
│                                │                                │
│   ┌────────────────────────────▼────────────────────────────┐   │
│   │ Repository Layer (Atomic Operations & Data Access)      │   │
│   └────────────────────────────┬────────────────────────────┘   │
└────────────────────────────────┼────────────────────────────────┘
                                 │  PyMongo Driver
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Database Layer                          │
│          MongoDB (Local Standalone or MongoDB Atlas M0)         │
│  Collections: users, departments, doctors, queues, counters,    │
│               audit_logs (Compound & Unique Indexes)           │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2. Virtual Queue State Machine

Queue entries transition through well-defined, server-validated states:

```
                  ┌──────────────┐
                  │    Join      │
                  │ Virtual Queue│
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐      Patient cancels
                  │   WAITING    ├───────────────────────► [ CANCELLED ]
                  └──────┬───────┘
                         │
           Doctor calls  │
           patient next  ▼
                  ┌──────────────┐      Patient fails
                  │    CALLED    ├──────to show up───────► [ NO_SHOW ]
                  └──────┬───────┘
                         │
     Doctor starts       │
     consultation        ▼
                  ┌──────────────┐
                  │      IN      │
                  │ CONSULTATION │
                  └──────┬───────┘
                         │
     Doctor completes    │
     consultation        ▼
                  ┌──────────────┐
                  │  COMPLETED   │
                  └──────────────┘
```

#### State Transition Constraints:
1. `WAITING` -> `CALLED`: Triggered only by a doctor assigned to the ticket's department.
2. `WAITING` -> `CANCELLED`: Triggered by the owning patient or administrator.
3. `CALLED` -> `IN_CONSULTATION`: Triggered when the called patient arrives in the consultation room.
4. `CALLED` -> `NO_SHOW`: Triggered when patient fails to present after being summoned.
5. `IN_CONSULTATION` -> `COMPLETED`: Triggered upon consultation conclusion with optional diagnosis notes.
6. Terminal states (`COMPLETED`, `CANCELLED`, `NO_SHOW`) are immutable and excluded from active queues.

---

### 3. Queue Calculations & Concurrency Protection

#### A. Concurrency-Safe Daily Token Allocation
- Daily tokens reset every UTC calendar day per department (e.g. `CARD-001`, `GEN-001`).
- Atomic allocation is implemented using MongoDB `find_one_and_update` on a `counters` collection with `$inc`:
  ```python
  counter_doc = db.counters.find_one_and_update(
      {"_id": f"{dept_id}_{queue_date}"},
      {"$inc": {"seq": 1}},
      upsert=True,
      return_document=ReturnDocument.AFTER
  )
  ```
  This eliminates duplicate token allocation even under heavy concurrent traffic.

#### B. Queue Position Semantics
- For a waiting ticket:
  - `patients_ahead` = count of active `WAITING` tickets in the department joined prior to current ticket on current date.
  - `live_position` = `patients_ahead + 1` (position 1 = next eligible patient).
- For `CALLED` and `IN_CONSULTATION` tickets:
  - `live_position` = 0, `patients_ahead` = 0.

#### C. Waiting-Time Estimation Formula
$$\text{estimated\_wait\_minutes} = \left\lceil \frac{\text{patients\_ahead} \times \text{avg\_consultation\_time}}{\text{effective\_available\_doctors}} \right\rceil$$

- `effective_available_doctors` is dynamically queried from the `doctors` collection (`is_available: true`).
- If no doctors are currently available on duty, the backend returns `null` ("Estimate unavailable") rather than presenting a misleading 0-minute wait.

---

### 4. Database Schema & Index Definitions

#### Collections:
1. **`users`**: Authentication credentials, roles (`patient`, `doctor`, `admin`), active status.
2. **`departments`**: Name, code, description, average consultation duration, active status.
3. **`doctors`**: Link between `user_id` and `department_id`, display name, availability toggle.
4. **`queues`**: Token number, queue date, status, joined/called/completed timestamps, estimated wait time.
5. **`counters`**: Atomic sequence counters for daily department token generation.
6. **`audit_logs`**: Timestamped immutable security and activity log (actor, action, entity, metadata).

#### Indexes:
- `users`: `{ email: 1 }` (unique), `{ role: 1 }`
- `departments`: `{ code: 1 }` (unique), `{ name: 1 }` (unique), `{ is_active: 1 }`
- `doctors`: `{ user_id: 1 }` (unique), `{ department_id: 1 }`, `{ is_available: 1 }`
- `queues`:
  - `{ department_id: 1, queue_date: 1 }`
  - `{ department_id: 1, status: 1, joined_at: 1 }`
  - `{ patient_id: 1, status: 1 }`
  - `{ patient_id: 1, created_at: -1 }`
  - `{ token_number: 1 }`
- `audit_logs`: `{ timestamp: -1 }`, `{ action: 1 }`, `{ entity_type: 1, entity_id: 1 }`
