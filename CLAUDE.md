# CLAUDE.md — MindWise API

## Project Overview

FastAPI backend for student psychological assessment. Students take exam questionnaires; answers are scored per psychological indicator (raw score), then Z-score standardized across all students in the same exam.

## Commands

```bash
# Run dev server
uvicorn app.main:app --reload --port 8000

# Install dependencies
pip install -r requirements.txt

# Seed database
python tools/initial_db_tool/init_db_with_seeding_data.py
```

## Architecture

- **Entry point**: `app/main.py` — registers routers, creates DB tables on startup
- **Routers**: `app/api/v1/endpoints/` — one file per domain (auth, health, students, classes, exams, answers, indicators, score, reports, surveys, teachers)
- **Models**: `app/models/` — SQLAlchemy ORM (student, class\_, exam, question, answer, indicator, indicator\_question, score\_student, report, report\_indicator)
- **Schemas**: `app/schemas/` — Pydantic v2 models for request/response
- **DB session**: `app/db/session.py` — `get_db()` dependency
- **SQL loader**: `app/db/sql_loader.py` — loads `.sql` files from `app/sql/`
- **Raw SQL**: `app/sql/` — `score_raw_avg.sql`, `indicator_stats_release.sql`
- **Config**: `app/core/database.py` — reads `DATABASE_URL` from env, defaults to `mindwise.db` at project root

## Auth & RBAC

- **Dependencies**: `app/api/v1/deps.py` — `get_current_teacher` validates JWT and injects the teacher; `require_admin_or_above` enforces role
- **Roles** (stored in JWT payload):
  - `super_admin` — full access including teacher management
  - `admin_teacher` — all student data + report generation
  - `class_teacher` — own class only (filtered by `class_id` in token)
- **Env vars required**: `SECRET_KEY` (JWT signing), `QWEN_API_KEY` (report generation), `ACCESS_TOKEN_EXPIRE_MINUTES` (default 1440)

## Key Conventions

- **Database**: SQLite by default; set `DATABASE_URL` in `.env` to switch (e.g., PostgreSQL)
- **SQL files**: Complex queries live in `app/sql/*.sql` and are loaded via `load_text_query(name)`
- **Idempotent scoring**: `POST /api/v1/scores/compute` deletes then re-inserts scores for the given `exam_id` inside a nested transaction
- **Error handling**: HTTP exceptions bubble up; unexpected exceptions are caught and returned as `500` with detail
- **Router prefixes**: All routers are mounted under `/api/v1`; each router also defines its own sub-prefix (e.g., `/scores`, `/students`)

## Data Flow — Score Computation

```
POST /scores/compute {exam_id}
  → _compute_score_raw_avg()       # SQL: score_raw_avg.sql
  → _compute_indicator_stats()     # SQL: indicator_stats_release.sql
  → _apply_standardization()       # Z-score in Python
  → _upsert_scores()               # DELETE + INSERT in nested transaction
  → _build_response()              # Return ScoreComputeResponse
```

## Tools

- `tools/initial_db_tool/` — seeds DB with JSON fixtures (indicators, questions, answers, indicator-question mappings)
- `tools/question_insertion_tool/` — bulk-inserts questions into an existing DB
