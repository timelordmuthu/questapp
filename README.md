# ⚔️ Quest App

A magical dark-themed friend-group challenge web app. Form Guilds, propose quests, earn XP and Points, track streaks, trade points, and compete on leaderboards. Maintain a private personal space — your Sanctum.

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 15 + Redis
- **Frontend**: React 18 + Vite + TypeScript + Tailwind CSS + Framer Motion
- **Hosting**: Render (API + Static Site + Cron Jobs)
- **Storage**: Cloudinary (avatars)
- **Email**: Resend (password reset)

## Quick Start (Local Dev)

```bash
git clone <repo-url> && cd questapp

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in your values

# Start local Postgres + Redis
docker compose up -d

# Apply DB schema
alembic upgrade head

# Run API
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd ../frontend
npm install
cp .env.example .env.local  # set VITE_API_URL=http://localhost:8000
npm run dev                  # http://localhost:5173
```

## Project Structure

```
questapp/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   ├── database.py      # Async SQLAlchemy engine + session
│   │   ├── redis_client.py  # Redis connection
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic
│   │   ├── routers/         # FastAPI route handlers
│   │   ├── jobs/            # Cron job scripts
│   │   └── utils/           # Helpers (XP, timezone, sigil, etc.)
│   ├── migrations/          # Alembic migration files
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Typed API client
│   │   ├── store/           # Zustand stores
│   │   ├── pages/           # Route-level page components
│   │   ├── components/      # Shared UI components
│   │   ├── hooks/           # Custom React hooks
│   │   └── styles/          # Global CSS + Tailwind config
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── docker-compose.yml       # Local dev only
├── render.yaml              # Render IaC
└── README.md
```

## Architecture Decisions

See `architecture_decisions.md` for full rationale on:
- Server-side session tokens in Redis (not JWTs)
- Incremental seasonal_points leaderboard cache
- Quest instance architecture (one row per time window)
- Append-only audit ledger (`balance_after` pattern)
- Timezone handling (all UTC in DB, convert per-user in app)

## Deployment

See `TECH_STACK.md` Section 6 for the full Render deployment checklist.
