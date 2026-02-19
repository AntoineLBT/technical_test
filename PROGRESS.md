# Implementation Progress

Technical test for Dailymotion — user registration API with email verification.

**Stack:** Python 3.12 · FastAPI · asyncpg (no ORM) · PostgreSQL · Mailhog · pytest + httpx · uv · Docker

---

## Commit Plan & Status

| # | Commit message | Status |
|---|----------------|--------|
| 1 | `chore: add project spec` | ✅ Done |
| 2 | `chore: scaffold project structure, pyproject.toml, Dockerfile, docker-compose` | ✅ Done |
| 3 | `fix: tell hatchling to package the app/ directory` | ✅ Done |
| 4 | `feat: add PostgreSQL migration runner and asyncpg pool lifespan` | ✅ Done |
| 5 | `chore: switch to uv for dependency management` | ✅ Done |
| 6 | `feat: add Pydantic v2 schemas and custom exception handlers` | ✅ Done |
| 7 | `feat: implement UserRepository and CodeRepository (raw SQL)` | ✅ Done |
| 8 | `feat: implement EmailService with aiosmtplib to Mailhog` | ✅ Done |
| 9 | `feat: implement UserService (register + activate orchestration)` | ✅ Done |
| 10 | `feat: add /users and /users/activate router with HTTPBasic and Depends` | ✅ Done |
| 11 | `test: add pytest fixtures with test DB isolation and AsyncClient` | ✅ Done |
| 12 | `test: add registration and activation test cases` | ✅ Done |
| 13 | `docs: README with architecture diagram and run instructions` | ✅ Done |

---

## Key Design Decisions

- **No ORM** — raw SQL via asyncpg (`fetchrow`, `fetch`, `execute`)
- **Migration runner** — `schema_migrations` table tracks applied files; only unapplied SQL files in `migrations/` are run on startup, in alphabetical order
- **Password rules** — min 12 chars, 1 uppercase, 1 lowercase, 1 special character
- **Code expiry** — `expires_at` computed DB-side (`NOW() + INTERVAL '1 minute'`) to avoid clock drift
- **Replay prevention** — `used_at` timestamp (nullable) instead of boolean; set on activation
- **Email** — `EmailService` wraps `aiosmtplib` sending to Mailhog SMTP port 1025; abstraction boundary so prod can swap to SendGrid/Mailgun
- **Transaction boundary** — owned by the router, not the service layer
- **Basic Auth** — FastAPI `HTTPBasic` + `HTTPBasicCredentials`; bcrypt constant-time comparison
- **Dev deps** — managed by uv in `[dependency-groups] dev`; excluded from prod Docker image via `--no-dev`

---

## Project Structure

```
app/
├── main.py              ✅ lifespan, app factory, exception handler registration
├── config.py            ✅ pydantic-settings
├── dependencies.py      ✅ get_pool, get_db, get_http_client (Depends providers)
├── database.py          ✅ create_pool + migration runner
├── routers/
│   └── users.py         ✅ POST /users, POST /users/activate
├── schemas/
│   └── user.py          ✅ UserCreate, UserResponse, ActivateRequest, MessageResponse
├── services/
│   ├── user_service.py  ✅ register() + activate() orchestration
│   └── email_service.py ✅ aiosmtplib → Mailhog:1025
├── repositories/
│   ├── user_repository.py   ✅ raw SQL on users table
│   └── code_repository.py   ✅ raw SQL on activation_codes table
└── exceptions/
    ├── base.py          ✅ AppException + domain exceptions
    └── handlers.py      ✅ register_exception_handlers(app)

migrations/
└── 001_initial.sql      ✅ users + activation_codes tables

tests/
├── conftest.py          ✅ pool fixture, TRUNCATE per test, httpx AsyncClient
├── test_register.py     ✅
└── test_activate.py     ✅
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/users` | None | Register with email + password → sends 4-digit code |
| POST | `/users/activate` | HTTP Basic | Activate account with 4-digit code (body) |

---

## Running the Project

```bash
# Start app + postgres + mailhog
docker compose up --build

# Run tests
docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit

# Local dev (VS Code): select .venv interpreter after running:
uv sync
```
