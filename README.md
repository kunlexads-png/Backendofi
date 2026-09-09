# OFI Cocoa Warehouse AI Assistant - Backend

A complete, production-ready backend built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Google Gemini API** for managing cocoa warehouse arrivals, finished goods, by-products, centralized inventory stock movements, spreadsheet/PDF uploads, executive dashboards, and an AI Warehouse Assistant.

---

## Table of Contents

1. [Requirements](#1-requirements)
2. [Folder Structure](#2-folder-structure)
3. [Environment Variables](#3-environment-variables)
4. [PostgreSQL Setup](#4-postgresql-setup)
5. [Local Installation](#5-local-installation)
6. [Database Migrations (Alembic)](#6-database-migrations-alembic)
7. [Running Locally](#7-running-locally)
8. [Running with Docker & Docker Compose](#8-running-with-docker--docker-compose)
9. [API Documentation (Swagger & ReDoc)](#9-api-documentation)
10. [Authentication & Role-Based Access Control](#10-authentication--role-based-access-control)
11. [Warehouse Modules & Endpoints](#11-warehouse-modules--endpoints)
12. [File Upload System & Data Review](#12-file-upload-system--data-review)
13. [Google Gemini AI Assistant & Security](#13-google-gemini-ai-assistant--security)
14. [Reporting & Exports](#14-reporting--exports)
15. [Automated Testing](#15-automated-testing)
16. [Connecting to React + Vite Frontend](#16-connecting-to-react--vite-frontend)
17. [Production Deployment](#17-production-deployment)

---

## 1. Requirements

* **Python 3.12+** (or Python 3.10+)
* **PostgreSQL 14+**
* **Docker & Docker Compose** (optional, recommended for containerized deployment)
* **Google Gemini API Key** (for natural language assistant capabilities)

---

## 2. Folder Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point & centralized error handlers
│   ├── config.py                # Environment configuration using Pydantic Settings
│   ├── database.py              # SQLAlchemy engine, session maker, and Base model
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py              # User and UserRole (Admin, Manager, Supervisor, Officer, Viewer)
│   │   ├── arrival.py           # Cocoa arrival records, bags, moisture, status
│   │   ├── finished_goods.py    # Finished goods (Butter, Liquor, Powder, Cake)
│   │   ├── byproduct.py         # Dust, Nibs, Cluster, Shaft, FM, Disposed Material
│   │   ├── stock_movement.py    # Centralized stock movements ledger (IN, OUT, DISPOSAL, etc.)
│   │   └── uploaded_file.py     # Uploaded file metadata and parsing status
│   │
│   ├── schemas/                 # Pydantic validation and serialization schemas
│   │   ├── __init__.py
│   │   ├── common.py            # Standard JSON envelopes and paginated responses
│   │   ├── user.py              # Auth, registration, token, password reset schemas
│   │   ├── arrival.py           # Arrival create, update, and response schemas
│   │   ├── finished_goods.py    # Finished goods and dispatch schemas
│   │   ├── byproduct.py         # Byproduct create, adjust, and disposal schemas
│   │   └── stock.py             # Stock movements, balances, and adjustment schemas
│   │
│   ├── routes/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py              # Login, register, me, password change, reset
│   │   ├── users.py             # User management (Admin only)
│   │   ├── arrival.py           # Cocoa arrival CRUD and stock logging
│   │   ├── finished_goods.py    # Finished goods management & dispatch
│   │   ├── byproduct.py         # By-product management, disposal & balance
│   │   ├── stock.py             # Centralized stock movements & adjustments
│   │   ├── uploads.py           # File upload, spreadsheet parser, review & commit
│   │   ├── dashboard.py         # Summary metrics, arrival trends, stock overview
│   │   ├── ai_assistant.py      # POST /api/ai/ask (Ground-truth verified AI)
│   │   └── reports.py           # Daily, weekly, monthly reports (CSV, Excel, PDF)
│   │
│   ├── services/                # Business logic services
│   │   ├── ai_service.py        # Database-first query retrieval + Gemini synthesis
│   │   ├── file_service.py      # Secure file storage, CSV, Excel, PDF parsers
│   │   ├── stock_service.py     # Centralized balance calculation & non-negative guard
│   │   └── report_service.py    # Report query generators & file export formatters
│   │
│   ├── auth/                    # Security utilities
│   │   ├── security.py          # Password hashing (bcrypt) & JWT token handling
│   │   └── dependencies.py      # OAuth2 bearer token extractor & RBAC dependencies
│   │
│   └── utils/
│       ├── validators.py        # File size, extensions, gross/tare weights, moisture
│       └── helpers.py           # Unique ID generators, date bounds, JSON wrappers
│
├── uploads/                     # Storage directory for uploaded files (.gitkeep)
├── tests/                       # Comprehensive pytest suite
│   ├── __init__.py
│   ├── conftest.py              # TestClient, SQLite in-memory DB, role fixtures
│   ├── test_auth.py
│   ├── test_arrivals.py
│   ├── test_finished_goods.py
│   ├── test_byproducts.py
│   ├── test_stock.py
│   ├── test_dashboard_and_ai.py
│   └── test_uploads.py
│
├── alembic/                     # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── README.md
```

---

## 3. Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configuration parameters:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/ofi_cocoa_warehouse` |
| `JWT_SECRET` | Secret key used to sign JWT tokens | *(Required in production)* |
| `JWT_ALGORITHM` | Hashing algorithm for JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token validity lifetime | `60` |
| `GEMINI_API_KEY` | Google Gemini API key | `""` |
| `FRONTEND_URL` | React + Vite client URL for CORS | `http://localhost:5173` |
| `UPLOAD_DIR` | Secure disk storage path for files | `uploads` |

---

## 4. PostgreSQL Setup

Ensure PostgreSQL is running, then create the database:

```bash
# Connect to PostgreSQL shell
psql -U postgres

# Create the warehouse database
CREATE DATABASE ofi_cocoa_warehouse;

# Verify creation
\l

# Exit
\q
```

---

## 5. Local Installation

Create a virtual environment and install dependencies:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux / macOS:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

## 6. Database Migrations (Alembic)

Apply database migrations to generate tables, indexes, and constraints:

```bash
# Run migrations up to the latest revision
alembic upgrade head

# To create a new revision in the future
alembic revision -m "add_custom_field"

# To rollback by one revision
alembic downgrade -1
```

---

## 7. Running Locally

Start the backend server using Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will now be accessible at:
* **Base API:** `http://localhost:8000/api`
* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`
* **Health Check:** `http://localhost:8000/api/health`

---

## 8. Running with Docker & Docker Compose

Launch the complete stack (FastAPI Backend + PostgreSQL Database) in a single command:

```bash
cd backend

# Build and start services in the background
docker compose up --build -d

# View real-time logs
docker compose logs -f

# Check container health status
docker compose ps

# Stop containers
docker compose down
```

The Docker setup automatically runs migrations upon container startup and maps the backend to `http://localhost:8000`.

---

## 9. API Documentation

FastAPI auto-generates interactive OpenAPI documentation:

* **Interactive Swagger UI:** Visit `http://localhost:8000/docs` to test endpoints, authenticate with tokens, and view schema definitions.
* **ReDoc Alternative:** Visit `http://localhost:8000/redoc` for clean, searchable reference documentation.

---

## 10. Authentication & Role-Based Access Control

The backend implements secure JWT authentication. Passwords are encrypted using `bcrypt`.

### User Roles & Permissions

| Role | Permissions |
| :--- | :--- |
| **Admin** | Full access to all endpoints, user management, negative stock adjustments. |
| **Warehouse Manager** | View and manage warehouse records, stock, reports, and dashboards. |
| **Supervisor** | Add and update warehouse records, perform dispatch/disposals, view reports. |
| **Warehouse Officer** | Record arrivals, add finished goods and by-products, upload spreadsheets. |
| **Viewer** | Read-only access to records and dashboards. |

### Authentication Endpoints

* `POST /api/auth/register`: Create user account.
* `POST /api/auth/login`: Authenticate and receive JWT bearer token.
* `GET /api/auth/me`: Retrieve current logged-in user profile.
* `POST /api/auth/change-password`: Change password.
* `POST /api/auth/forgot-password`: Request password reset token.
* `POST /api/auth/reset-password`: Confirm password reset.

---

## 11. Warehouse Modules & Endpoints

### 1. Cocoa Arrivals (`/api/arrivals`)
* `POST /api/arrivals`: Record cocoa arrival (validates bags, gross/tare weights, moisture). Automatically logs Stock IN when status is `Completed`.
* `GET /api/arrivals`: Search & filter by `date`, `supplier`, `customer`, `batch`, `truck`, `status` with pagination.
* `GET /api/arrivals/{id}`: Get single arrival details.
* `PUT /api/arrivals/{id}`: Update arrival status (e.g. mark `Completed`).
* `DELETE /api/arrivals/{id}`: Admin deletion.

### 2. Finished Goods (`/api/finished-goods`)
* `POST /api/finished-goods`: Record Cocoa Butter, Liquor, Powder, Cake.
* `GET /api/finished-goods`: Filter by `product`, `date`, `batch`, `status`.
* `POST /api/finished-goods/{id}/dispatch`: Dispatch goods to customer, recording Stock OUT.
* `PUT /api/finished-goods/{id}`: Update record details.
* `DELETE /api/finished-goods/{id}`: Admin deletion.

### 3. By-Product Warehouse (`/api/byproducts`)
* Supports: **Cluster**, **Cluster Beans**, **Dust**, **Nibs**, **Shaft**, **FM**, **Disposed Material**.
* `POST /api/byproducts`: Add by-product stock (records Stock IN).
* `GET /api/byproducts`: Filter by product, batch, status, source.
* `GET /api/byproducts/balance`: Current verified balances for all by-products.
* `POST /api/byproducts/{id}/dispose`: Record disposal of damaged/scrap material.
* `POST /api/byproducts/{id}/adjust`: Audit adjustment.

### 4. Centralized Stock Management (`/api/stock`)
* `GET /api/stock/summary`: Aggregate stock totals (Cocoa, Finished Goods, By-products) and product balances.
* `GET /api/stock/movements`: Complete transaction ledger (`IN`, `OUT`, `TRANSFER`, `ADJUSTMENT`, `DISPOSAL`).
* `POST /api/stock/adjust`: Manual inventory adjustments.
* **Negative Stock Protection**: Stock balance is prevented from falling below zero unless an Admin provides explicit authorization.

---

## 12. File Upload System & Data Review

* Endpoint: `POST /api/uploads`
* Supported formats: **CSV**, **XLSX**, **XLS**, **PDF**, **JPG**, **PNG**.
* **Safety Protocol**:
  1. Validates file extension and size (15MB maximum).
  2. Extracts data into structured tabular rows.
  3. Returns a preview summary with valid/invalid counts.
  4. Allows human operators to review records before calling `POST /api/uploads/{id}/import?target_module=arrival` to commit them into the database.

---

## 13. Google Gemini AI Assistant & Security

* Endpoint: `POST /api/ai/ask`
* Request payload: `{"question": "How much Dust do we have?"}`

### Security & Integrity Principles
1. **Ground-Truth First**: Numerical queries retrieve facts from PostgreSQL first. The AI never invents or hallucinates warehouse figures.
2. **SQL Injection Defense**: The AI does not run raw user-supplied SQL. It calls predefined, parameterized backend functions.
3. **Strict Scope Control**: Unrelated inquiries (non-warehouse questions) are safely declined.
4. **Zero Credential Exposure**: System prompts strictly forbid leaking API keys, JWT secrets, or user passwords.

---

## 14. Reporting & Exports

* Endpoint: `GET /api/reports/{report_type}?format={csv|excel|pdf}&period={daily|weekly|monthly}`
* Report Types:
  * `arrivals` (daily, weekly, monthly)
  * `finished_goods`
  * `byproducts`
  * `stock_movements`
  * `disposals`

---

## 15. Automated Testing

The backend includes a comprehensive `pytest` test suite covering authentication, role permissions, arrival calculations, finished goods dispatch, by-product disposals, stock limits, file uploads, and AI assistant security:

```bash
# Run tests
pytest

# Run tests with verbose output
pytest -v

# Run with test coverage report
pytest --cov=app tests/
```

---

## 16. Connecting to React + Vite Frontend

To connect your React + Vite frontend to this backend:

1. In your frontend directory, create or update `.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```
2. In your API client (e.g. Axios or Fetch wrapper), attach the Bearer token:
   ```typescript
   // Example Axios setup
   import axios from 'axios';

   export const api = axios.create({
     baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
   });

   api.interceptors.request.use((config) => {
     const token = localStorage.getItem('token');
     if (token) {
       config.headers.Authorization = `Bearer ${token}`;
     }
     return config;
   });
   ```
3. All API responses follow the standardized React-friendly JSON format:
   ```json
   {
     "success": true,
     "message": "Operation successful",
     "data": {},
     "error": null
   }
   ```

---

## 17. Production Deployment

For production deployments:

1. Set a strong, randomly generated `JWT_SECRET`:
   ```bash
   openssl rand -hex 32
   ```
2. Update `ALLOWED_ORIGINS` in `.env` to match your deployed frontend domain.
3. Deploy via Docker Compose or Kubernetes using the provided `Dockerfile`.
4. Configure an HTTPS reverse proxy (Nginx, Traefik, or Cloud Run) in front of Uvicorn.
