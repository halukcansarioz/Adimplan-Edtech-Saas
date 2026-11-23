# 🎓 AdımPlan EdTech SaaS

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

Multi-tenant EdTech coaching and student tracking SaaS starter featuring **Supabase PostgreSQL Row-Level Security (RLS)**, a **FastAPI** analytics backend, an **Optical CSV Parser**, and an interactive 6-module MVP.

> 🚀 **Live Demo:** **[https://halukcansarioz.github.io/adimplan/](https://halukcansarioz.github.io/adimplan/)**

---

# 📝 Table of Contents
- [About the Project](#-about-the-project)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation & Usage](#-installation--usage)
- [Project Structure](#-project-structure)
- [License](#-license)

---

# 📌 About the Project

**AdımPlan EdTech SaaS** is a full-stack educational coaching platform designed for multi-tenant institutions, coaches, students, and parents. It combines strict database-level tenant isolation via Supabase PostgreSQL RLS (`supabase/migrations/001_initial_schema_rls.sql`), high-performance REST endpoints in FastAPI (`backend/main.py`), automated optical exam CSV ingestion (`backend/optical_parser.py`), and a 6-module interactive frontend MVP.

---

# ✨ Features

- ✅ **1. Weekly Schedule & PDF** — Interactive weekly study planner with structured time blocks and printable PDF export.
- ✅ **2. Mock Exam Trend & Heatmap** — Subject-level net score progression charts and topic mastery heatmaps.
- ✅ **3. Leitner Mistake Vault** — Spaced-repetition mistake tracking system to organize and review missed exam questions.
- ✅ **4. Pomodoro & RSVP Speed Reading** — Built-in Pomodoro focus timer paired with a Rapid Serial Visual Presentation (RSVP) speed-reading trainer.
- ✅ **5. Parent Report & Messages** — Automated student progress reports and direct coach-parent communication.
- ✅ **6. Institutional Panel & Optical CSV Import** — Multi-tenant institutional management dashboard with bulk optical reader CSV exam ingestion via `backend/optical_parser.py`.

---

# 🛠 Tech Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend API** | FastAPI | Analytics, optical CSV parsing & multi-tenant endpoints (`backend/main.py`) |
| **Database & Auth** | Supabase (PostgreSQL RLS) | Multi-tenant relational schema with Row-Level Security policies |
| **Optical Ingestion** | Python CSV Parser | Bulk optical exam form parsing (`backend/optical_parser.py`) |
| **Testing** | pytest | Automated backend & parser unit tests (`backend/tests/`) |
| **Deployment** | Render & GitHub Pages | Backend Blueprint (`render.yaml`) & static 6-module MVP demo |
| **CI/CD** | GitHub Actions | Automated `pytest` CI pipeline (`.github/workflows/ci.yml`) |

---

# ⚙️ Installation & Usage

### 1. Clone the Repository

```bash
git clone git@github.com:halukcansarioz/adimplan-edtech-saas.git
cd adimplan-edtech-saas
cp .env.example .env
```

### 2. Database Migration (Supabase PostgreSQL RLS)

```bash
psql "$DATABASE_URL" -f supabase/migrations/001_initial_schema_rls.sql
```

### 3. Backend Server (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. Running Tests

```bash
cd backend
pytest
```

---

# 📁 Project Structure

```text
adimplan-edtech-saas/
├── .github/
│   └── workflows/
│       └── ci.yml                              # GitHub Actions pytest CI
├── backend/
│   ├── main.py                                 # FastAPI application
│   ├── optical_parser.py                       # Optical exam CSV parser
│   ├── requirements.txt                        # Python dependencies
│   └── tests/                                  # pytest test suite
├── supabase/
│   └── migrations/
│       └── 001_initial_schema_rls.sql          # Multi-tenant PostgreSQL RLS schema
├── .env.example                                # Environment variable template
├── LICENSE                                     # Project license
├── README.md                                   # Project documentation
└── render.yaml                                 # Render deployment blueprint
```

---

# 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
