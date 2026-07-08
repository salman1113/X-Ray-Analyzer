# Contributing to AI X-Ray Analyzer

## Getting Started

1. Clone the repo
2. Create your branch from `main`
3. Make your changes
4. Open a Pull Request

## Branch Naming

Use this format:

```
feature/short-description    → new features
fix/short-description        → bug fixes
docs/short-description       → documentation only
```

Examples:
- `feature/scan-upload`
- `fix/login-otp-timeout`
- `docs/update-readme`

## Workflow

```
1. git checkout main
2. git pull origin main
3. git checkout -b feature/your-feature
4. ... make changes ...
5. git add -A
6. git commit -m "feat: short description"
7. git push -u origin feature/your-feature
8. Open PR on GitHub → request review
9. After approval → merge into main
```

## Commit Messages

Keep them short and clear:

```
feat: add patient search filter
fix: OTP expiry not handled correctly
docs: update API endpoints manual
refactor: simplify scan upload logic
```

## Rules

- **Never push directly to `main`** — always use a PR
- **One feature per PR** — small PRs are easier to review
- **Pull before you branch** — always start from latest `main`
- **Test locally before pushing** — make sure the app runs
- **Ask for help early** — if you're stuck or unsure, ask in the group

## Running Locally

### Backend
```bash
cd backend
docker compose up --build
# API at http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# App at http://localhost:5173
```

## Before Opening a PR

Check these pass:

```bash
# Backend — no syntax errors
cd backend
python -c "import ast, pathlib; [ast.parse(p.read_text(), filename=str(p)) for p in pathlib.Path('.').rglob('*.py')]"

# Frontend — builds without errors
cd frontend
npm run build
```

## Code Style

- **Backend:** formatted with `black`, linted with `ruff`
- **Frontend:** linted with ESLint (runs on `npm run lint`)
- **CSS:** use the design system CSS variables (`var(--primary)`, `var(--ink)`, etc.)
- **Components:** use Tailwind utility classes, not custom CSS

## Project Structure

```
backend/
├── core/       ← Infrastructure (DB, auth, middleware)
├── routes/     ← API endpoints (one folder per domain)
├── services/   ← Shared services (email)
└── scripts/    ← CLI tools

frontend/
├── src/api/        ← API client modules
├── src/components/ ← Reusable UI
├── src/context/    ← Global state
└── src/pages/      ← Page components
```

## Need Help?

- Check `.manuals/` for detailed documentation
- Read `README.md` for setup instructions
- Ask in the group chat before spending hours stuck
