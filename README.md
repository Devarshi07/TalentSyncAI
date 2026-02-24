# Job Assistant AI

A production-grade AI-powered job search platform with resume tailoring, interview preparation, and career guidance.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![React](https://img.shields.io/badge/React-18-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)

## Features

- **Multi-Agent Chat** — Supervisor agent classifies intent and routes to specialized agents
- **Resume Tailoring** — Paste a job description, get a tailored LaTeX resume (one-page, dynamically balanced)
- **Interview Prep** — AI-generated behavioral + technical questions with STAR-format answers from your profile
- **PDF Resume Import** — Upload a PDF resume to auto-populate your profile
- **Google OAuth + JWT Auth** — Secure authentication with refresh token rotation
- **Chat History** — Persistent threads with rename, delete, and per-user storage limits (3MB)
- **Responsive UI** — Material UI dark theme, mobile-friendly collapsible sidebar

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        Frontend (React + MUI)                  │
│  Auth Page │ Chat Page │ Profile Page │ Resumes Page           │
└──────────────────────────┬─────────────────────────────────────┘
                           │ REST API (axios + JWT)
┌──────────────────────────▼─────────────────────────────────────┐
│                     FastAPI Backend                             │
│                                                                │
│  ┌─────────┐  ┌──────────────────────────────────────────┐     │
│  │  Auth   │  │           Chat Router                    │     │
│  │ Router  │  │  User msg → Supervisor Agent (Gemini)    │     │
│  └─────────┘  │         │                                │     │
│  ┌─────────┐  │    ┌────┴────┬──────────┬──────────┐     │     │
│  │ Profile │  │    ▼         ▼          ▼          ▼     │     │
│  │ Router  │  │ Resume    Interview   General    Profile │     │
│  └─────────┘  │ Tailor    Prep       Agent      Redirect│     │
│  ┌─────────┐  │ Agent     Agent                          │     │
│  │ Threads │  └──────────────────────────────────────────┘     │
│  │ Router  │                                                   │
│  └─────────┘  ┌──────────────────────┐  ┌──────────────────┐  │
│               │  Gemini Client       │  │  Rate Limiter    │  │
│               │  (retry + backoff)   │  │  (slowapi)       │  │
│               └──────────────────────┘  └──────────────────┘  │
└──────────────────────────┬─────────────────────────────────────┘
                           │ SQLAlchemy
┌──────────────────────────▼─────────────────────────────────────┐
│                     PostgreSQL 16                               │
│  users │ refresh_tokens │ profiles │ chat_threads │ chat_msgs  │
└────────────────────────────────────────────────────────────────┘
```

### Multi-Agent Flow

```
User: "Tailor my resume for ML Engineer at Google"
  │
  ▼
Supervisor Agent (Gemini) → classifies as "resume_tailor"
  │
  ▼
Resume Tailor Agent
  ├── Loads user profile from DB
  ├── Calculates one-page bullet budget (dynamic based on content)
  ├── Sends profile + JD to Gemini → gets tailored bullets
  ├── Fills LaTeX template (template never modified)
  └── Returns .tex file as attachment
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Material UI 6 |
| Backend | FastAPI, SQLAlchemy, Pydantic v2 |
| AI | Google Gemini (multi-agent with retry + backoff) |
| Database | PostgreSQL 16 (Alembic migrations) |
| Auth | JWT (access + refresh rotation), Google OAuth 2.0, bcrypt |
| DevOps | Docker, docker-compose, GitHub Actions CI/CD, nginx |
| Testing | pytest, FastAPI TestClient, SQLite for test isolation |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js 20+
- A [Gemini API key](https://aistudio.google.com/apikey) (free)

### 1. Clone & configure
```bash
git clone <repo-url>
cd Job-Assistant
cp backend/.env.example backend/.env
# Edit backend/.env — add your GEMINI_API_KEY
```

### 2. Start the database
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Run the backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app:app --reload --port 5001
```

### 4. Run the frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

### Full stack with Docker (production)
```bash
# Make sure backend/.env is configured
docker-compose up --build
```
Open **http://localhost** (port 80)

## Project Structure

```
Job-Assistant/
├── backend/
│   ├── alembic/              # Database migrations
│   │   └── versions/         # Migration files
│   ├── core/                 # Cross-cutting concerns
│   │   ├── deps.py           # FastAPI dependencies (auth)
│   │   ├── errors.py         # Exception handlers
│   │   ├── limiter.py        # Rate limiting (slowapi)
│   │   ├── logging.py        # Structured logging
│   │   └── middleware.py     # Request ID, timing
│   ├── db/                   # Data layer
│   │   ├── database.py       # Engine, session factory
│   │   └── models.py         # SQLAlchemy models (5 tables)
│   ├── routers/              # API endpoints
│   │   ├── auth.py           # Signup, login, OAuth, refresh, logout
│   │   ├── chat.py           # Multi-agent chat orchestration
│   │   ├── profile.py        # Profile CRUD + PDF import
│   │   └── threads.py        # Chat history management
│   ├── schemas/              # Pydantic models
│   │   ├── auth.py           # Auth request/response
│   │   ├── chat.py           # Chat request/response
│   │   └── profile.py        # Profile with all resume sections
│   ├── services/             # Business logic
│   │   ├── auth.py           # Password hashing, JWT, refresh tokens
│   │   ├── gemini_client.py  # Gemini wrapper (retry + backoff)
│   │   ├── general_agent.py  # Career advice, catch-all
│   │   ├── interview_prep.py # Interview question generation
│   │   ├── resume_parser.py  # PDF → structured profile
│   │   ├── resume_tailor.py  # Profile + JD → tailored LaTeX
│   │   └── supervisor.py     # Intent classification
│   ├── templates/
│   │   └── resume_base.tex   # LaTeX template (never modified)
│   ├── tests/                # Integration tests
│   ├── Dockerfile            # Production image (gunicorn + uvicorn)
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Sidebar (responsive), TopBar
│   │   ├── context/          # AuthContext (login, signup, OAuth, refresh)
│   │   ├── pages/            # Auth, Chat, Profile, Resumes, Dashboard
│   │   ├── services/         # Axios client (interceptors, auto-refresh)
│   │   └── theme/            # MUI dark theme customization
│   ├── Dockerfile            # Multi-stage (node build → nginx)
│   ├── nginx.conf            # Reverse proxy + SPA fallback
│   └── vite.config.js        # Dev server with API proxy
├── .github/workflows/
│   ├── ci.yml                # Tests, lint, build, integration
│   └── deploy.yml            # Build + push Docker images
├── docker-compose.yml        # Full stack (Postgres + API + nginx)
├── docker-compose.dev.yml    # Dev (Postgres only)
└── .env.example              # → copy to backend/.env
```

## API Endpoints

### Auth
| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/api/auth/signup` | Register new user | 5/min |
| POST | `/api/auth/login` | Login | 10/min |
| POST | `/api/auth/refresh` | Refresh token pair | 60/min |
| POST | `/api/auth/logout` | Revoke all refresh tokens | 60/min |
| GET | `/api/auth/me` | Current user info | 60/min |
| GET | `/api/auth/google` | Google OAuth redirect | — |
| GET | `/api/auth/google/callback` | OAuth callback | — |

### Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/profile` | Get user profile |
| PUT | `/api/profile` | Update profile |
| POST | `/api/profile/import-resume` | Upload PDF → parse to profile |

### Chat
| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/api/chat` | Send message (auto-creates thread) | 20/min |

### Threads
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/threads` | List user's threads + storage usage |
| GET | `/api/threads/:id` | Get thread with all messages |
| DELETE | `/api/threads/:id` | Delete thread (cascade) |
| PATCH | `/api/threads/:id` | Rename thread |

## Testing

```bash
cd backend
pytest tests/ -v
```

Tests use in-memory SQLite with rate limiting disabled. Covers:
- Auth flow (signup, login, refresh rotation, logout, duplicates)
- Profile CRUD and user isolation
- Chat thread creation, continuation, listing, deletion, renaming
- Thread isolation between users
- Health check endpoints

## Environment Variables

See [`backend/.env.example`](backend/.env.example) for all options.

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google AI Studio API key |
| `DATABASE_URL` | No | Defaults to `postgresql://postgres:postgres@localhost:5433/job_assistant` |
| `JWT_SECRET` | Yes (prod) | Secret for JWT signing — use a random 64-char string |
| `GOOGLE_CLIENT_ID` | No | For Google OAuth login |
| `GOOGLE_CLIENT_SECRET` | No | For Google OAuth login |
| `RATE_LIMIT_ENABLED` | No | Defaults to `true` |
| `DEBUG` | No | Defaults to `false` |

## Deployment

### Docker (recommended)
```bash
docker-compose up --build -d
```

### Cloud Deployment (Free)

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for full instructions.

| Service | Platform | Cost |
|---------|----------|------|
| Frontend | Vercel | Free |
| Backend | Azure Container Apps | $0-2/mo |
| Database | Supabase PostgreSQL | Free (500MB) |

### Manual
1. Set up PostgreSQL
2. Configure `backend/.env`
3. Run `alembic upgrade head`
4. Start with `gunicorn app:app --worker-class uvicorn.workers.UvicornWorker --workers 2 --bind 0.0.0.0:5001`
5. Build frontend: `cd frontend && npm run build`
6. Serve `frontend/dist/` with nginx

## License

MIT
