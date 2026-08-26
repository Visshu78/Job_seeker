# AI Career Agent — Personalized Job Discovery & Application Platform

Personalized AI SaaS platform for students, fresh graduates, and early-career professionals to discover opportunities across top platforms, understand match fit, analyze skill gaps, manage student academic credentials, and apply with human-in-the-loop safety.

Built in strict accordance with the complete [PRD.txt](./PRD.txt) requirements.

---

## 🌟 Architecture Overview

```mermaid
graph TD
    A[Job Sources Engine] -->|Ingests from 8 Platforms| B[Canonical Normalizer & Deduplicator]
    B --> C[(SQLite / MySQL Database)]
    D[Candidate Resume & Profile] --> E[Resume Parser & Intelligence]
    E --> C
    C --> F[Multi-Factor AI Matching Engine]
    F -->|Scores & Transferable Skills| G[Resume Gap Analyzer]
    G --> H[Match Explorer & Detail Modal]
    H --> I[Human-In-The-Loop Application Studio]
    I -->|Explicit User Authorization Gate| J[Application Tracking Pipeline]
    K[Google OAuth 2.0 / Auth Service] -->|Secures & Bootstraps| C
```

---

## 🌐 1. Multi-Source Ingestion Engine (`backend/app/services/job_sources`)

The platform continuously ingests, normalizes, and deduplicates opportunities from **8 distinct platforms, direct ATS integrations, and ecosystem maps**:

| Source | Category | Ecosystem / Coverage | Live Adapter |
|---|---|---|---|
| **LinkedIn Jobs** | Professional Network | Live engineering & AI roles across India & Remote | [`linkedin_source.py`](./backend/app/services/job_sources/linkedin_source.py) |
| **Delhi NCR Startup Map** (`delhistartupmap.com`) | Verified Startup Map | 464+ verified startups across Gurugram, Noida, Delhi (*Addverb, Spyne.ai, Devtron, Atlan*) | [`delhi_startup_map_source.py`](./backend/app/services/job_sources/delhi_startup_map_source.py) |
| **Indian Startup Map** (`indianstartupmap.com`) | DPIIT Startup Register | 453,000+ DPIIT-recognized startups across 712 districts (*Qure.ai, Agnikul, Observe.ai, Yellow.ai*) | [`indian_startup_map_source.py`](./backend/app/services/job_sources/indian_startup_map_source.py) |
| **Bangalore Startups Hub** (`blrstartup.com`) | Ecosystem Startup Hub | Top startups in Koramangala, HSR Layout, Indiranagar (*Sarvam AI, Krutrim AI, Blinkit*) | [`bangalore_startups_source.py`](./backend/app/services/job_sources/bangalore_startups_source.py) |
| **Greenhouse ATS** | Direct Company ATS | Direct enterprise company boards (*Figma, Stripe, Databricks, Scale AI*) | [`greenhouse_source.py`](./backend/app/services/job_sources/greenhouse_source.py) |
| **Lever ATS** | Direct Company ATS | Public company-level engineering career boards | [`lever_source.py`](./backend/app/services/job_sources/lever_source.py) |
| **RemoteOK API** | Global Tech Board | Live global remote tech & AI engineering postings | [`remoteok_source.py`](./backend/app/services/job_sources/remoteok_source.py) |
| **AI Career Ingestion Hub** | Targeted Seed Feed | Curated Indian tech & GenAI roles for student & early-career personas | [`seed_feed.py`](./backend/app/services/job_sources/seed_feed.py) |

* **Cross-Platform Deduplication** ([`deduplicator.py`](./backend/app/services/deduplicator.py)): Uses exact canonical fingerprinting + fuzzy textual Jaccard overlap to merge identical postings across multiple boards.

---

## 🗄️ 2. Database & Student Profile Schema

### Database Architecture
* **Default Engine**: SQLAlchemy with **SQLite** (`backend/app/jobagent.db`).
* **MySQL Support**: Zero code changes needed to run on MySQL. Simply configure `backend/.env`:
  ```env
  DATABASE_URL=mysql+pymysql://username:password@localhost:3306/jobagent
  ```
* **Auto Migration Engine**: `sync_database_schema()` in [`database.py`](./backend/app/database.py) dynamically synchronizes missing columns upon server startup without dropping tables or losing data.

### Schema Attributes

#### `User` Model (`users` table)
* `id` (Integer, Primary Key)
* `email` (String, Unique, Indexed)
* `hashed_password` (String, Salted PBKDF2/SHA256 hash; OAuth token placeholder for Google logins)
* `full_name` (String)
* `phone_number` (String)
* `avatar_url` (String, Google profile picture or Dicebear avatar)
* `auth_provider` (String: `'google'` or `'local'`)
* `google_id` (String, Google OAuth identifier)
* `is_active` (Boolean, default `True`)
* `is_verified` (Boolean, default `True` for OAuth)

#### `CandidateProfile` Model (`candidate_profiles` table)
* **Higher Education & Academic Records**:
  * `college_name` (String, e.g. *IIT Delhi, BITS Pilani, NIT Trichy*)
  * `degree` (String, e.g. *B.Tech in Computer Science & Engineering*)
  * `cgpa` (String, e.g. *8.8/10* or *9.2/10*)
  * `graduation_year` (Integer, e.g. *2025*)
* **Schooling Records (`schooling` JSON)**:
  * `class_12th`: `{ school: "Delhi Public School", board: "CBSE", percentage: "94%" }`
  * `class_10th`: `{ school: "Delhi Public School", board: "CBSE", percentage: "95%" }`
* **Contact & Candidate Information**:
  * `full_name`, `email`, `phone_number`, `location`, `headline`
  * `skills` (JSON array: technical skills taxonomy, e.g., `["Python", "PyTorch", "Docker", "SQL"]`)
  * `roles` (Target job titles)
  * `experience_level` (*Fresher*, *0-1 years*, *1-2 years*, *Mid-Level*)
  * `experience`, `projects`, `certifications` (Structured JSON arrays)

---

## 🔐 3. Authentication & Google OAuth 2.0

* **Google OAuth Sign-In**: `POST /api/v1/auth/google` handles token authorization, creates the user account, and auto-seeds the candidate profile with college, CGPA, and contact details.
* **Salted Password Hashing**: PBKDF2 with SHA-256 and salt ensures passwords are never stored in plaintext.
* **JWT Access Control**: Issues RFC 7519 JSON Web Tokens for stateless API authorization.

---

## 🎯 4. Multi-Factor AI Matching Engine (`backend/app/services/matching_engine.py`)

### 1. Hard Filtering
Enforces hard constraints before scoring:
* Minimum stipend/salary threshold
* Location preferences (with remote-only toggle)
* Excluded company filters

### 2. Indian City Synonym Resolution
Automatically maps Indian city synonyms so regional listings match candidate preferences without false negatives:
$$\text{"Bengaluru"} \longleftrightarrow \text{"Bangalore"} \quad\quad \text{"Gurugram"} \longleftrightarrow \text{"Gurgaon"} \quad\quad \text{"Delhi NCR"} \longleftrightarrow \text{"Delhi"} / \text{"Noida"}$$

### 3. PRD Matching Formula
$$\text{Score} = 30\% \cdot \text{Skill} + 25\% \cdot \text{Semantic} + 15\% \cdot \text{Experience} + 15\% \cdot \text{Preference} + 10\% \cdot \text{Role} + 5\% \cdot \text{Education}$$

### 4. Transferable Skill Reasoning Graph
Awards transferability credits instead of penalizing candidates:
* **Deep Learning**: PyTorch $\longleftrightarrow$ TensorFlow $\longleftrightarrow$ Keras $\longleftrightarrow$ JAX
* **Web Frontend**: React $\longleftrightarrow$ Vue $\longleftrightarrow$ Next.js $\longleftrightarrow$ Svelte
* **Backend**: FastAPI $\longleftrightarrow$ Flask $\longleftrightarrow$ Django $\longleftrightarrow$ Express
* **Databases**: PostgreSQL $\longleftrightarrow$ MySQL $\longleftrightarrow$ SQLite $\longleftrightarrow$ MongoDB
* **Cloud & DevOps**: AWS $\longleftrightarrow$ GCP $\longleftrightarrow$ Azure $\longleftrightarrow$ Docker

---

## 🛡️ 5. Human-In-The-Loop Safety Gate & Applications

* **Automated Tailoring**: Generates role-grounded cover letters and screening question answers.
* **Explicit User Authorization Gate**: Applications **cannot** be submitted autonomously. Users must review the draft and verify two explicit safety checkboxes:
  1. `[x] I have reviewed this tailored application`
  2. `[x] I authorize the AI Career Agent to record submission`
* **Lifecycle Pipeline**: `Discovered` $\to$ `Saved` $\to$ `Approved` $\to$ `Submitted` $\to$ `Under Review` $\to$ `Interview` $\to$ `Offer`.

---

## 📡 6. Complete REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/google` | Google OAuth 2.0 sign-in / registration |
| `POST` | `/api/v1/auth/register` | Register new user with hashed password |
| `POST` | `/api/v1/auth/login` | Email + password login |
| `GET` | `/api/v1/auth/me` | Current authenticated user profile |
| `GET` | `/api/v1/profile` | Fetch candidate profile & academic records |
| `PUT` | `/api/v1/profile` | Update profile (College, CGPA, Schooling, Skills) |
| `POST` | `/api/v1/resumes/upload` | Upload & parse resume document (PDF/DOCX/TXT) |
| `GET` | `/api/v1/jobs` | Paginated job list with keyword/location filters |
| `POST` | `/api/v1/jobs/sync` | Run live multi-source ingestion across all 8 platforms |
| `GET` | `/api/v1/matches` | Get evaluated job matches with PRD fit scores |
| `POST` | `/api/v1/matches/recalculate` | Re-run matching engine against updated candidate profile |
| `GET` | `/api/v1/matches/{job_id}/gap-analysis` | Detailed skill gap report and resume suggestions |
| `POST` | `/api/v1/applications/prepare` | Generate tailored cover letter and screening Q&A |
| `POST` | `/api/v1/applications/submit` | Record submitted application (requires user safety gate) |
| `GET` | `/api/v1/dashboard/stats` | Pipeline metrics, source counts, and average fit score |
| `GET` | `/api/v1/notifications` | Real-time in-app match alerts |

---

## 🚀 7. Quick Start Guide

### Prerequisites
* Python 3.10+
* Node.js 18+ and npm

### 1. Backend Setup & Run (FastAPI)
```bash
cd backend

# Create & activate Python virtual environment
python -m venv venv
.\venv\Scripts\activate      # Windows (or 'source venv/bin/activate' on Linux/macOS)

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend server
uvicorn app.main:app --reload --port 8000
```
* **API Server**: `http://localhost:8000`
* **Interactive Swagger UI Docs**: `http://localhost:8000/docs`

### 2. Frontend Setup & Run (React + Vite + Tailwind CSS)
```bash
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
* **Web UI Application**: `http://localhost:3000`

---

## 🧪 8. Testing & Verification

Run the full automated pytest suite inside the virtual environment:
```bash
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_backend.py
```

```text
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0
collected 6 items

tests\test_backend.py ......                                             [100%]
======================= 6 passed in 5.57s ========================
```
