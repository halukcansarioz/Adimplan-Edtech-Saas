# 🚀 Adimplan — EdTech Coaching SaaS (v2.0.0)

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
[![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white)](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://img.shields.io/badge/License-MIT-green.svg)

---

Multi-tenant EdTech coaching and student tracking SaaS (**v1.0**) featuring **27 coaching & institutional modules**, **5 Supabase PostgreSQL Row-Level Security (RLS) migrations (`001`–`005`)**, a **rate-limited & SHA-256 cached FastAPI** analytics backend, an **Optical CSV Parser**, **PWA offline support (`sw.js`)**, and **Playwright desktop + 390px mobile E2E CI tests**.

> 🚀 **Live Demo:** **[https://adimplan.vercel.app/](https://adimplan.vercel.app/)**

---

# 📝 Table of Contents
- [Live Pages](#-live-pages)
- [About the Project](#-about-the-project)
- [v1.0 Feature Summary](#-v10-feature-summary)
- [Tech Stack](#-tech-stack)
- [Installation & Usage](#-installation--usage)
- [Project Structure](#-project-structure)
- [License](#-license)

---

# 🌐 Live Pages

| Page | Path | Description |
| :--- | :--- | :--- |
| **Landing Page** | `/` | Product overview, pricing/value proposition, and live entry point |
| **Login & Onboarding** | `/login.html` | Role-based authentication & demo access |
| **Coaching Workspace** | `/app.html` | Main 27-module student, coach, and parent coaching workspace |
| **Admin Console** | `/admin.html` | Multi-tenant institutional management, coach handover, and analytics |
| **Super Admin / CMS Console** | `/super-admin.html` | Super admin / CMS console (Süper yönetici / CMS konsolu) | 
| **Weekly Program** | `/program.html` | Weekly study program & schedule (Haftalık Program) |
| **Coach Panel** | `/coach-panel.html` | Coach management & student tracking panel (Koç Paneli) |
| **Student Panel** | `/student.html` | Student dashboard & progress tracking (Öğrenci Paneli) |
| **Pricing** | `/pricing.html` | Subscription plans & pricing (Fiyatlandırma) |
| **Parent Report** | `/parent-report.html` | Shareable weekly parent report (Paylaşılabilir Haftalık Veli Raporu) |
| **Optical Reader** | `/optical-reader.html` | Interactive optical reader & scoring (Etkileşimli Optik Okuyucu & Puanlama) |
---

# 📌 About the Project

**İvme Akademi EdTech SaaS (v1.0)** is a full-stack educational coaching platform designed for multi-tenant institutions, coaches, students, and parents. It combines strict database-level tenant isolation via 5 Supabase PostgreSQL RLS migrations (`001`–`005`), high-performance rate-limited and SHA-256 cached REST endpoints in FastAPI (`backend/main.py`), automated optical exam CSV ingestion (`backend/optical_parser.py`), and a 27-module responsive PWA frontend (`frontend/`).

---

# ✨ v1.0 Feature Summary

- **27 Koçluk / Kurumsal Modül:** Öğrenci, koç, veli ve kurum yöneticisi iş akışlarını kapsayan 27 uçtan uca koçluk ve kurumsal yönetim modülü.
- **6 Chart.js Etkileşimli Grafik + 2 SVG İlerleme Halkası:** Deneme neti trendleri, ders dağılımları, hedef takibi ve anlık ilerleme göstergeleri.
- **Senkronize Gece / Gündüz Modu:** Tüm canlı sayfalarda (`/`, `/login.html`, `/app.html`, `/admin.html`) eşzamanlı tema senkronizasyonu.
- **3 Adımlı İlk Kurulum Sihirbazı:** Yeni kurum/koç/öğrenci başlangıcı için rehberli 3 adımlı kurulum akışı.
- **PWA Çevrimdışı Desteği (`sw.js`):** Service Worker (`sw.js`) ile çevrimdışı önbellekleme ve yüklenebilir PWA deneyimi.
- **8 Sınav Türü Konu Ağacı:** 8 farklı sınav türü için yapılandırılmış müfredat ve konu ilerleme ağacı.
- **Hata Kök Nedeni Analizi:** Yanlış ve boş soruların konu/beceri bazlı kök neden analizi.
- **Koç Devir Aracı:** Öğrencilerin ve koçluk geçmişinin kurum içi başka bir koça güvenli devri.
- **5 Supabase RLS Migrasyonu (`001`–`005`):**
  - `supabase/migrations/001_initial_schema_rls.sql`
  - `supabase/migrations/002_full_27_modules_rls.sql`
  - `supabase/migrations/003_workspace_snapshots.sql`
  - `supabase/migrations/004_security_hardening.sql`
  - `supabase/migrations/005_role_based_access.sql`
- **FastAPI Rate-Limited & SHA-256 Önbellekli Backend:** Hız sınırlamalı (rate-limited), SHA-256 önbellekli API uç noktaları ve Optik CSV ayrıştırıcı (`backend/optical_parser.py`).
- **Playwright Masaüstü + 390px Mobil E2E & Backend CI Testleri:** GitHub Actions üzerinde hem `test` (pytest) hem `frontend-e2e` (masaüstü ve 390px mobil viewport Playwright) test doğrulaması.

---

# 🛠 Tech Stack

* **Frontend:** Vanilla HTML5, CSS3, JavaScript (27 Modules, Chart.js, SVG Progress Rings, PWA `sw.js`, Dark/Light Theme Sync)
* **Backend:** Python 3.11, FastAPI, Uvicorn (Rate Limiting & SHA-256 Response Caching)
* **Database & Auth:** Supabase (PostgreSQL with Row-Level Security — Migrations `001`–`005`)
* **Testing & CI:** `pytest`, Playwright E2E (Desktop + 390px Mobile), GitHub Actions (`test` & `frontend-e2e`)
* **Deployment:** Vercel (Frontend) & Render (Backend)

---

# 🚀 Installation & Usage

### 1. Clone the repository
```bash
git clone https://github.com/halukcansarioz/Adimplan-Edtech-Saas
cd Adimplan-Edtech-Saas
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Fill in your SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY
```

### 3. Apply Database Migrations
Run all 5 SQL migrations in order (`001` → `005`) in your Supabase SQL Editor (`004` is required for cloud backup/restore, `005` limits what students can access):
1. `supabase/migrations/001_initial_schema_rls.sql`
2. `supabase/migrations/002_full_27_modules_rls.sql`
3. `supabase/migrations/003_workspace_snapshots.sql`
4. `supabase/migrations/004_security_hardening.sql`
5. `supabase/migrations/005_role_based_access.sql`
6. `supabase/migrations/006_full_panels_rls.sql`

**API authentication:** set `SUPABASE_URL` and `SUPABASE_ANON_KEY` on the API server. The parent e-mail and optical CSV import endpoints then require a signed-in Supabase user with an `owner` or `coach` row in `public.memberships`. Create the first tenant and its owner membership in the SQL Editor. Without these variables the API runs in demo mode and refuses to send real e-mail.

### 4. Run the Backend Locally
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Or run locally with Docker Compose:
```bash
docker compose up --build
```

### 5. Run Tests
```bash
# Backend unit & API tests
pytest backend/tests

# Frontend E2E tests (Desktop + 390px Mobile, Python Playwright)
pip install playwright && playwright install chromium
pytest tests/test_frontend_e2e.py
```

### 6. API Endpoints (`/api/v1`)
Versioned v1.7+ and v1.8+ backend routes are served under `/api/v1` (via `v17_routes.py`), providing read and capabilities endpoints for the coach and student panels.

---

# 📂 Project Structure

```text
Adimplan-Edtech-Saas/
├── .github/workflows/
│   └── ci.yml                       # GitHub Actions CI (test + frontend-e2e)
├── backend/
│   ├── main.py                      # FastAPI app (rate-limited & SHA-256 cached)
│   ├── optical_parser.py            # Optical exam CSV parser
│   └── requirements.txt
├── frontend/
│   ├── index.html                   # Landing page (/)
│   ├── login.html                   # Auth page (/login.html)
│   ├── app.html                     # 27-module coaching workspace (/app.html)
│   ├── admin.html                   # Admin & coach handover console (/admin.html)
│   └── sw.js                        # PWA offline Service Worker
├── supabase/migrations/
│   ├── 001_initial_schema_rls.sql   # Initial multi-tenant RLS schema
│   ├── 002_full_27_modules_rls.sql  # 27-module tables & RLS policies
│   ├── 003_workspace_snapshots.sql  # Workspace snapshots migration
│   ├── 004_security_hardening.sql   # RLS and cloud sync security fixes
│   └── 005_role_based_access.sql    # Role-based access (owner/coach/student)
├── tests/                           # pytest & Playwright E2E test suites
├── .env.example
├── render.yaml
├── vercel.json
└── README.md
```

---

# 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
