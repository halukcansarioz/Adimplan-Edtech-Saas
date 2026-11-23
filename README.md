# AdımPlan — Multi-Tenant EdTech Coaching SaaS

[![CI](https://github.com/halukcansarioz/adimplan-edtech-saas/actions/workflows/ci.yml/badge.svg)](https://github.com/halukcansarioz/adimplan-edtech-saas/actions/workflows/ci.yml)

Multi-tenant EdTech coaching & student tracking SaaS starter featuring PostgreSQL/Supabase Row-Level Security (RLS), a FastAPI analytics backend, an optical exam CSV parser, and an interactive 6-module MVP.

## Live Demo

Try the free live 6-module MVP demo: **[https://halukcansarioz.github.io/adimplan](https://halukcansarioz.github.io/adimplan)**
## Features

1. **Weekly Schedule & PDF** — Interactive weekly study planner with structured time blocks and printable PDF export.
2. **Mock Exam Trend & Heatmap** — Subject-level net score progression charts and topic mastery heatmaps.
3. **Leitner Mistake Vault** — Spaced-repetition mistake tracking system to organize and review missed exam questions.
4. **Pomodoro & RSVP Speed Reading** — Built-in Pomodoro focus timer paired with a Rapid Serial Visual Presentation (RSVP) speed-reading trainer.
5. **Parent Report & Messages** — Automated student progress reports and direct coach-parent communication.
6. **Institutional Panel & Optical CSV Import** — Multi-tenant institutional management dashboard with bulk optical reader CSV exam ingestion.

## Architecture

- **Supabase PostgreSQL RLS** — Multi-tenant relational schema with Row-Level Security policies for strict tenant, coach, student, and parent data isolation (`supabase/migrations/001_initial_schema_rls.sql`).
- **FastAPI** — High-performance Python API (`backend/main.py`) powering analytics and exam workflows.
- **Optical CSV Parser** — Dedicated parser (`backend/optical_parser.py`) for normalizing and validating optical exam sheet CSV exports.
- **pytest CI** — Automated test suite (`backend/tests/`) executed on every push and pull request via GitHub Actions (`.github/workflows/ci.yml`).
## Setup

### 1. Database Migration (Supabase / PostgreSQL)
Run the initial schema and Row-Level Security migration in your Supabase SQL editor or PostgreSQL instance:

```bash
psql "$DATABASE_URL" -f supabase/migrations/001_initial_schema_rls.sql
```

### 2. Backend Server (FastAPI + Uvicorn)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Run Tests (pytest)
```bash
cd backend
pytest -v
```
