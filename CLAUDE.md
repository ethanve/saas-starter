# SaaS Starter Template

A production-ready SaaS monorepo with a Python/FastAPI backend and Next.js frontend, deployed on Railway.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy (async), PostgreSQL, Redis |
| **Frontend** | Next.js 15 (App Router), React 19, Tailwind CSS v4, shadcn/ui |
| **Auth** | JWT (access/refresh tokens), Google OAuth 2.0, httpOnly cookies, Argon2 passwords |
| **File Storage** | Local filesystem (Railway volume in production) |
| **Package Managers** | UV (Python), Bun (JavaScript) |
| **CI/CD** | GitHub Actions (lint + test on PR, build check) |
| **Deployment** | Railway (services, PostgreSQL, Redis, volumes) |
| **AI Tools** | Claude Code with gstack skills + impeccable.style |

## Project Structure

```
saas-starter-template/
├── CLAUDE.md            # This file — project guide + Claude instructions
├── Makefile             # Root dev commands
├── docker-compose.yml   # PostgreSQL + Redis for local dev
├── .github/workflows/   # CI/CD
├── api/                 # Python/FastAPI backend
│   ├── src/app/         # Application code
│   │   ├── core/        # Config, database, middleware, storage
│   │   ├── auth/        # JWT auth, OAuth, password hashing
│   │   │   └── oauth/   # Google OAuth flow
│   │   ├── organization/ # Multi-tenant orgs, memberships
│   │   └── upload/      # File upload routes
│   ├── alembic/         # Database migrations
│   ├── tests/           # Pytest tests
│   ├── Dockerfile
│   └── railway.toml
└── web/                 # Next.js frontend
    ├── src/app/
    │   ├── (marketing)/ # Landing, pricing, about pages
    │   ├── (auth)/      # Login, signup forms
    │   ├── (app)/       # Dashboard (authenticated)
    │   └── oauth/       # OAuth callback handler
    ├── .claude/skills/  # impeccable.style design skills
    ├── Dockerfile
    └── railway.toml
```

---

## Installing Dev Tools

> **For the user:** Follow these steps in order. Open Terminal and run each command. If a step asks you to restart your terminal, do so before continuing.

### 1. Homebrew (macOS package manager)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After install, follow the instructions it prints to add Homebrew to your PATH. Then restart your terminal.

### 2. Python 3.12+

```bash
brew install python@3.12
```

Verify: `python3 --version` should show 3.12 or higher.

### 3. UV (Python package manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal, then verify: `uv --version`

### 4. Bun (JavaScript runtime)

```bash
curl -fsSL https://bun.sh/install | bash
```

Restart your terminal, then verify: `bun --version`

### 5. Docker Desktop

1. Download from https://www.docker.com/products/docker-desktop/
2. Open the downloaded `.dmg` file and drag Docker to Applications
3. Open Docker from Applications — it will start the Docker daemon
4. Verify in terminal: `docker --version`

### 6. GitHub CLI

```bash
brew install gh
gh auth login
```

Follow the prompts to authenticate with your GitHub account.

### 7. Railway CLI

```bash
brew install railway
railway login
```

Follow the prompts to authenticate with your Railway account.

### 8. Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Or download from https://claude.ai/download — choose "Claude Code" for your platform.

### 9. gstack (Claude Code skills)

Paste this into Claude Code and let it run:

```
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup
```

This gives you `/ship`, `/review`, `/qa`, `/investigate`, `/browse`, and 20+ more skills.

---

## First-Time Setup

> **For Claude:** When the user asks to "set up" or "get started", run these commands in order.

```bash
# 1. Start PostgreSQL and Redis
docker compose up -d

# 2. Install Python dependencies
cd api && uv sync --all-extras && cd ..

# 3. Create the .env file for the API
cp api/.env.example api/.env

# 4. Run database migrations
cd api && uv run alembic upgrade head && cd ..

# 5. Install frontend dependencies
cd web && bun install && cd ..

# 6. Verify everything works
cd api && uv run pytest && cd ..
cd web && bun run build && cd ..
```

If all steps pass, you're ready to develop.

---

## Development Workflow

### Starting the dev servers

```bash
make dev
```

This starts both:
- **API** at http://localhost:8000 (with auto-reload)
- **Frontend** at http://localhost:3000 (with Turbopack)

### Running just one

```bash
make dev-api    # API only
make dev-web    # Frontend only
```

### Running tests

```bash
make test       # Run API tests
make lint       # Lint API code
```

### Database operations

```bash
make migrate                    # Apply pending migrations
make migration name="add_foo"   # Create new migration
make db-up                      # Start PostgreSQL + Redis
make db-down                    # Stop PostgreSQL + Redis
```

---

## Adding Features (Test-Driven Development)

Always follow this pattern when building new features:

### 1. Write the test first

```python
# api/tests/test_my_feature.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_thing(client: AsyncClient):
    response = await client.post("/api/v1/things", json={"name": "test"})
    assert response.status_code == 201
```

### 2. Run the test (it should fail)

```bash
cd api && uv run pytest tests/test_my_feature.py -v
```

### 3. Implement the feature

Create the model, schema, service, and route following the existing patterns (see Architecture section below).

### 4. Run the test again (it should pass)

```bash
cd api && uv run pytest tests/test_my_feature.py -v
```

### 5. Run all tests to ensure nothing is broken

```bash
cd api && uv run pytest
```

---

## GitHub Setup

> **For the user:** Run these commands to create your GitHub repository.

```bash
# Initialize git (if not already)
git init
git add -A
git commit -m "Initial commit: SaaS starter template"

# Create a GitHub repo and push
gh repo create my-saas-app --private --push --source=.
```

### Branch Strategy

- `main` — production branch, always deployable
- Feature branches: `feat/feature-name`, `fix/bug-name`, `chore/task-name`

Never push directly to main. Always create a branch and open a PR:

```bash
git checkout -b feat/my-feature
# ... make changes ...
git add -A && git commit -m "Add my feature"
git push -u origin feat/my-feature
gh pr create --fill
```

---

## CI/CD

GitHub Actions runs automatically on every PR and push to main:

- **lint-api**: Checks Python code style with Ruff
- **test-api**: Runs pytest against a real PostgreSQL + Redis
- **build-web**: Verifies the Next.js frontend builds successfully

If CI fails, check the Actions tab in your GitHub repo to see the error.

---

## gstack Skills

After installing gstack, you have these key commands in Claude Code:

| Command | What it does |
|---------|-------------|
| `/ship` | Run tests, review diff, create PR |
| `/review` | Staff-engineer level code review |
| `/qa` | Opens a real browser, finds bugs, fixes them |
| `/investigate` | Systematic root-cause debugging |
| `/browse` | Headless browser for testing |
| `/cso` | Security audit (OWASP Top 10 + STRIDE) |
| `/design-review` | Visual QA and design fixes |
| `/retro` | Weekly engineering retrospective |

Use `/ship` when you're ready to push your feature to GitHub. Use `/review` before merging any PR.

---

## Railway Deployment

> **For the user:** Follow these steps to deploy your app to Railway.

### 1. Create a Railway project

```bash
railway init
```

Choose "Empty Project" when prompted.

### 2. Add a PostgreSQL database

1. Open your project in the Railway dashboard (https://railway.com/dashboard)
2. Click **+ New** → **Database** → **PostgreSQL**
3. Railway will create a PostgreSQL instance with connection variables

### 3. Add a Redis database

1. Click **+ New** → **Database** → **Redis**

### 4. Deploy the API service

```bash
cd api
railway link    # Select your project
railway up      # Deploy
```

Or connect your GitHub repo for auto-deploy:
1. In Railway dashboard, click **+ New** → **GitHub Repo**
2. Select your repo
3. Set the **Root Directory** to `api`
4. Railway will auto-deploy on every push to main

### 5. Configure API environment variables

In the Railway dashboard, go to your API service → **Variables** tab and add:

```
ENVIRONMENT=production
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
UPLOAD_DIR=/data/uploads
API__FRONTEND_URL=https://your-frontend-domain.up.railway.app
```

For Google OAuth (optional):
```
OAUTH__GOOGLE__CLIENT_ID=your-client-id
OAUTH__GOOGLE__CLIENT_SECRET=your-client-secret
OAUTH__GOOGLE__REDIRECT_URI=https://your-api-domain.up.railway.app/api/v1/oauth/google/callback
OAUTH__FRONTEND_SUCCESS_URL=https://your-frontend-domain.up.railway.app/oauth/callback
OAUTH__FRONTEND_ERROR_URL=https://your-frontend-domain.up.railway.app/oauth/error
```

### 6. Add a volume for file uploads

1. Go to API service → **Volumes** tab
2. Click **+ Add Volume**
3. Set mount path to `/data/uploads`
4. Set size (5 GB is plenty to start)

### 7. Deploy the frontend service

1. In Railway dashboard, click **+ New** → **GitHub Repo**
2. Select your repo again
3. Set **Root Directory** to `web`
4. Add variable: `NEXT_PUBLIC_API_URL=https://your-api-domain.up.railway.app`

### 8. Set up custom domains (optional)

1. Go to each service → **Settings** → **Public Networking**
2. Click **Generate Domain** for a free `*.up.railway.app` subdomain
3. Or add a custom domain and point your DNS CNAME to the provided value

---

## Coding Conventions

> **For Claude:** Follow these rules when writing code in this project.

### Python (API)

- Python 3.12+, type hints on all function signatures
- Use `str | None` (not `Optional[str]`), `list[str]` (not `List[str]`)
- Double quotes for strings
- Line length: 100 characters
- Use loguru with `{placeholder}` format:
  ```python
  logger.info("Processing item {id}", id=item_id)
  ```
- Table names prefixed with `app_` (e.g., `app_users`, `app_organizations`)
- Public IDs use prefixed nanoids (e.g., `user_abc123`, `org_xyz789`)
- All models extend `BaseModel` from `app.core.models`
- Use `Session` (annotated dependency) for database access in routes
- Errors use `AppException` subclasses from `app.core.exceptions`

### TypeScript (Frontend)

- TypeScript strict mode
- Use `@/` path alias for imports from `src/`
- App Router conventions: `page.tsx` for routes, `layout.tsx` for layouts
- Client components use `"use client"` directive
- API calls use `apiFetch` from `@/lib/api`
- Auth uses httpOnly cookies (credentials: "include" on all API calls)

### Testing

- Every new API feature must have tests
- Tests live in `api/tests/`
- Use the `client` fixture for HTTP tests
- Use `test_session` fixture for direct database operations

---

## Architecture Guide

### Adding a New API Module

Follow this pattern (example: "projects" module):

1. **Create the module directory:**
   ```
   api/src/app/project/
   ├── __init__.py
   ├── models.py     # SQLAlchemy models
   ├── schemas.py    # Pydantic request/response schemas
   ├── service.py    # Business logic
   └── routes.py     # FastAPI routes
   ```

2. **Define the model** (`models.py`):
   ```python
   from app.core.models import OrganizationScopedBaseModel, PublicIDMixin
   from sqlalchemy import String
   from sqlalchemy.orm import Mapped, mapped_column

   class Project(OrganizationScopedBaseModel, PublicIDMixin):
       __tablename__ = "app_projects"
       _public_id_prefix = "proj_"
       name: Mapped[str] = mapped_column(String(255), nullable=False)
   ```

3. **Register the model** in `api/src/app/models.py`:
   ```python
   from app.project.models import Project  # noqa: F401
   ```

4. **Create a migration:**
   ```bash
   cd api && uv run alembic revision --autogenerate -m "add_projects_table"
   cd api && uv run alembic upgrade head
   ```

5. **Add schemas, service, routes** following the auth or organization module patterns.

6. **Register the router** in `api/src/app/api.py`:
   ```python
   from app.project.routes import router as project_router
   api_router.include_router(project_router)
   ```

### Adding a New Frontend Page

1. Create a new directory under the appropriate route group:
   - Public pages → `web/src/app/(marketing)/`
   - Auth pages → `web/src/app/(auth)/`
   - Authenticated pages → `web/src/app/(app)/`

2. Create `page.tsx` in the new directory.

3. For authenticated pages, use `apiFetch` from `@/lib/api` for data fetching.

### Auth Flow

1. User signs up or logs in → API returns JWT tokens + sets httpOnly cookies
2. Frontend includes `credentials: "include"` on all API requests
3. Browser automatically sends cookies → API verifies JWT from cookie or Authorization header
4. Token refresh: POST to `/api/v1/auth/refresh` before access token expires
5. OAuth: redirects to Google → callback creates/links user → returns one-time code → frontend exchanges for cookies

---

## impeccable.style Skills

The frontend has impeccable.style installed in `web/.claude/skills/`. Key commands:

| Command | Purpose |
|---------|---------|
| `/teach-impeccable` | One-time setup: teach it your design context |
| `/audit` | Technical quality check (a11y, performance) |
| `/critique` | UX design review |
| `/polish` | Final pass before shipping |
| `/typeset` | Fix typography issues |
| `/arrange` | Fix layout and spacing |
| `/colorize` | Add strategic color |
| `/animate` | Add purposeful motion |

Run `/teach-impeccable` once after cloning to personalize the design skills for your project.

---

## Environment Variables Reference

### API (`api/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | development/staging/production/test | development |
| `DATABASE_URL` | PostgreSQL connection string | postgresql://app:app@localhost:5434/app |
| `REDIS_URL` | Redis connection string | redis://localhost:6381 |
| `SECRET_KEY` | JWT signing key (required in production) | auto-generated in dev |
| `UPLOAD_DIR` | File upload directory | ./uploads |
| `LOG_LEVEL` | Logging level | INFO |
| `API__FRONTEND_URL` | Frontend URL for CORS | http://localhost:3000 |
| `OAUTH__GOOGLE__CLIENT_ID` | Google OAuth client ID | — |
| `OAUTH__GOOGLE__CLIENT_SECRET` | Google OAuth secret | — |
| `OAUTH__GOOGLE__REDIRECT_URI` | OAuth callback URL | — |

### Frontend (`web/.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | http://localhost:8000 |
