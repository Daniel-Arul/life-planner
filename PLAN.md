# Life Planner: Project Plan

## Context
This is a personal, self-hosted app for tracking **workouts, expenses, to-dos, ideas, and plans**. One **calendar** view brings them together. It runs on a Raspberry Pi at home. Away from home, it's reached privately over **Tailscale**, so nothing is exposed to the public internet. The stack is **Python (FastAPI) + SvelteKit**. The project directory (`/home/daniel/src/life-planner`) is empty, so this is a new build.

**Defaults I chose** (easy to change):
- Single user with a password login.
- Docker Compose for deployment.
- A 64-bit OS on a Pi 4 or Pi 5.

**Status:** milestones 1–6 done (skeleton, auth, UI kit; to-dos, events, calendar; expenses and budgets; workouts; ideas; PWA, offline handling and export). Next: milestone 7, deploying to the Pi.

**Changes from the original plan so far:**
- On laptops, edit forms open as a modal window rather than a master–detail side pane, so every page shares one editor.
- Editing a recurring event changes the whole series; occurrences of a series can't be dragged individually (one-off exceptions could come later).
- Event times are stored as local wall-clock times with no timezone, so recurring events keep their local time across daylight-saving changes.
- Shortcuts: `n` (new item), `/` (focus the page's search box; only Ideas has one so far), and `g` then `h`/`c`/`t`/`e`/`w`/`i` (go to Home, Calendar, To-dos, Expenses, Workouts or Ideas).
- Charts are small hand-built SVG components instead of Chart.js/LayerChart, keeping the bundle light and the look consistent. Chart marks use a deeper peach (`#e8894b`), because the pastel is too faint to read as a mark.
- Expense categories have no color of their own. Expense charts are a single series in the module's peach, and over-budget shows as a status color with an icon and text.
- The currency is set by `PLANNER_CURRENCY` in `.env` (default CAD) and served to the app from `/api/config`. The expense date field is `spent_on`.
- The migration seeds starter categories (Groceries, Eating out, Transport, Housing, Bills, Health, Fun, Shopping, Other). Budgets are edited in Settings.
- Workouts store one row per exercise: sets × reps at a weight, or distance plus time for cardio (table `workout_entry`). Typing a new exercise name creates it. Units come from `PLANNER_UNITS` (metric = kg/km, the default; imperial = lb/mi), and stored numbers are never converted.
- Workouts on the calendar open the editor rather than dragging. The log form has "Same as last time" to copy a previous session's exercises.
- Workout charts use a deeper mint (`#2f9e78`, which passes 3:1 contrast). Spending and workouts share one column-chart component; exercise progress uses a line chart.
- The pixel font no longer draws digits (its 5/S and 3/8 are too alike), so numbers everywhere fall back to IBM Plex Mono.
- PWA: the service worker caches only the app itself (code, styles, fonts, icons) and never `/api` data, so pages always show live data from the Pi. Offline, the cached app opens and shows a "can't reach your planner, check Tailscale" screen or banner instead of a browser error. Home-screen icon shortcuts (long-press) open the add forms via `?add=todo|expense|workout|idea`.
- Export: `/api/export.json` (everything) and `/api/export/{todos,events,expenses,workouts,ideas}.csv`, linked from Settings. There's no import yet; the nightly SQLite backup in milestone 7 is the restore path.
- An expired session (after 30 days) sends you back to the login page.
- Idea tags are stored as a JSON list on the idea (normalized to lowercase, no `#`) rather than in a separate table. "Active" means New or Exploring. The Markdown editor is a plain textarea with Write/Preview tabs, rendered with `marked` and sanitized with DOMPurify (links open in a new tab).

---

## Architecture

```
Phone / laptop ──(Tailscale, HTTPS via `tailscale serve`)──▶ Raspberry Pi
                                                           └─ Docker: life-planner container
                                                                ├─ FastAPI (uvicorn) on 127.0.0.1:8000
                                                                │    ├─ /api/*  JSON REST API
                                                                │    └─ /*      serves built SvelteKit static files
                                                                └─ SQLite DB in mounted volume ./data/planner.db
```

- **Backend:** FastAPI, SQLModel (SQLAlchemy), and SQLite in WAL mode. Alembic handles migrations. Pydantic handles validation.
- **Frontend:** SvelteKit with `adapter-static` (SPA mode) and TypeScript. Tailwind for styling. `@event-calendar/core` provides the Svelte-native month/week/day calendar. Chart.js or LayerChart draws the expense and workout charts.
- **One container, one process.** FastAPI serves both the API and the static frontend. This keeps RAM use low on the Pi and avoids CORS.
- **PWA:** a manifest and a service worker, so the app installs to the phone home screen and works like a native app.

## Visual design: soft retro computer
The look is a late-80s/early-90s desktop (classic Mac OS / Windows 3.1 feel) on soft white "paper," with pastel accents.

**Color tokens** (CSS variables in `src/app.css`, mirrored in the Tailwind theme):
| Token | Value | Use |
|---|---|---|
| `--bg` | `#FAF7F0` soft warm white | page background |
| `--surface` | `#FFFEFB` | window bodies, cards |
| `--ink` | `#2B2A33` soft charcoal | text, 2px outlines, hard shadows |
| `--muted` | `#8A8696` | secondary text, gridlines |
| `--lavender` | `#CDB4FF` | events/plans, primary buttons |
| `--mint` | `#B5EAD7` | workouts |
| `--peach` | `#FFCBA4` | expenses |
| `--butter` | `#FFF1A8` | to-dos, highlights |
| `--sky` | `#A7D8F0` | ideas |
| `--rose` | `#F7B2C4` | overdue / over budget / destructive |

Each module has its own pastel. That pastel colors the module's title bar, its calendar chips, and its chart series, so you can tell what an item is at a glance.

**Type:**
- Headings and title bars use a pixel font: *Pixelify Sans* or *Silkscreen*.
- Body text and numbers use a readable monospace: *IBM Plex Mono*, with tabular figures for money and weights.
- Fonts are self-hosted with `@fontsource` packages, so the PWA works offline.

**Retro UI kit** (`src/lib/ui/`):
- **`Window`**: every panel is a "window." It has a 2px ink border and a hard offset shadow (`4px 4px 0 var(--ink)`, no blur). Its title bar is striped in the module's pastel and carries close/minimize squares as decoration.
- **`Button`**: chunky beveled button. Pressing it sinks the button 2px and removes the shadow.
- **Form controls:** inputs, checkboxes, and selects use square corners, inset bevels, and a blinking block cursor on focus.
- **`MenuBar`**: on desktop, a top bar with the app name, a clock, and module "menus." On phones, a bottom dock of pixel icons from `pixelarticons`.
- **Desktop treatment:** a subtle dithered or dot-grid background pattern. Loading uses a pixel progress bar, and empty states show "floppy disk" art.
- **Calendar:** restyled `@event-calendar` grid with ink gridlines, pastel event chips, and a blinking outline on today's cell.
- **Charts:** flat pastel fills with ink outlines, no gradients, and stepped or blocky bars.

**Guardrails:**
- Pastels are only ever used as fills behind ink-colored text, so contrast stays at WCAG AA.
- `prefers-reduced-motion` disables the blink and press animations.
- The design stays mobile-first: windows stack full-width on phones.

## Responsive layout (phone + laptop)
Styles are written mobile-first, with Tailwind breakpoints at `md` = 768px and `lg` = 1024px.

| Area | Phone (< 768px) | Laptop (≥ 1024px) |
|---|---|---|
| Navigation | Bottom dock of pixel icons (thumb-reachable), with a floating "+" quick-add button | Top `MenuBar` plus a left sidebar listing the modules |
| Dashboard | Windows stacked in one column | 2–3 column grid of windows |
| Calendar | Day/agenda list view by default, swipe between days, tap a day to add | Month and week grid by default; drag to create or move events |
| Lists (to-dos, expenses, ideas) | Full-width cards; edit opens a full-screen sheet | Table or list next to a detail/edit pane (master–detail) |
| Forms | Full-screen sheets with large tap targets (≥ 44px) and native date/number inputs (`inputmode="decimal"` for amounts) | Side drawer or modal window |
| Charts | Full width, simplified axes | Side by side with summaries |

Other details:
- Use `100dvh` and safe-area insets (`env(safe-area-inset-*)`) so the bottom dock clears the iPhone home bar when installed as a PWA.
- Pointer-specific CSS: `@media (hover: hover)` gives hover states and drag only on laptops; touch devices get tap and swipe.
- On phones, the retro chrome is lighter: thinner shadows and title bars without decoration, to save space.
- Laptops get keyboard shortcuts: `n` for new item, `g c` for the calendar, `/` for search.

## Data model (SQLite tables)
| Entity | Key fields |
|---|---|
| `event` (plans) | id, title, notes, start, end, all_day, rrule (optional recurrence), color |
| `todo` | id, title, notes, due_date (nullable), priority, status (open/done), completed_at, list/tag |
| `workout` | id, date, type (strength/cardio/other), duration_min, notes |
| `workout_set` | id, workout_id, exercise, sets, reps, weight, distance, time |
| `exercise` | id, name, category (gives autocomplete and progress charts) |
| `expense` | id, date, amount (stored as integer cents), category_id, description, payment_method |
| `expense_category` | id, name, monthly_budget (optional), color |
| `idea` | id, title, body (markdown), tags, status (new/exploring/done/archived), created_at |
| `user` | id, username, password_hash (argon2) |

All tables have `created_at` and `updated_at`.

## Calendar aggregation
`GET /api/calendar?start=&end=` returns one unified feed for the visible range:
- **Events**, including recurring events expanded with `dateutil.rrule`.
- **To-dos** that have a due date.
- **Workouts**, as a marker on each day.
- **Expenses**, as a daily total badge.

Each item carries a `kind` field. The frontend uses it to color the item and to filter by kind with toggle chips.

Clicking an item opens its edit drawer. Clicking an empty day opens a quick-add menu: event, to-do, workout, or expense.

## API (REST, all under `/api`, all behind auth)
- `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`. These use an HTTP-only session cookie.
- Standard CRUD for `/events`, `/todos`, `/workouts` (sets nested), `/expenses`, `/expense-categories`, `/ideas`, `/exercises`.
- Summaries:
  - `/stats/expenses?month=`: totals by category, plus spending against budget.
  - `/stats/workouts?range=`: weekly volume, frequency, and progress per exercise.
- `/export` downloads a JSON or CSV dump of all data.

## Frontend pages
- `/` **Dashboard:** today's events, open and overdue to-dos, this week's workouts, and month-to-date spending.
- `/calendar`: month, week, and day views with kind filters.
- `/todos`: list with quick add, filters, and drag to reorder.
- `/workouts`: workout log, a new-workout form (with exercise autocomplete), and progress charts.
- `/expenses`: list, quick add, and a monthly category breakdown with budget bars.
- `/ideas`: card or list view with a markdown editor, tags, and status.
- `/settings`: password, categories, and data export.

The layout is mobile-first, with a bottom nav on phones and a side nav on desktop.

## Project layout
```
life-planner/
├─ PLAN.md
├─ backend/
│  ├─ pyproject.toml
│  ├─ alembic/ , alembic.ini
│  └─ app/
│     ├─ main.py          # FastAPI app, static mount, routers
│     ├─ config.py        # settings via env (DB path, secret key)
│     ├─ db.py            # engine, session, WAL pragma
│     ├─ auth.py          # argon2 hashing, session cookie, dependency
│     ├─ models/          # one module per domain
│     ├─ routers/         # events, todos, workouts, expenses, ideas, calendar, stats
│     └─ cli.py           # `create-user` command
│  └─ tests/              # pytest + httpx TestClient
├─ frontend/
│  ├─ package.json, svelte.config.js (adapter-static), vite.config.ts
│  └─ src/
│     ├─ lib/api.ts       # typed fetch wrapper
│     ├─ lib/components/  # forms, drawers, charts, nav
│     └─ routes/          # pages listed above
├─ Dockerfile             # multi-stage: node build → python runtime
├─ docker-compose.yml
├─ scripts/backup.sh      # sqlite3 .backup + rotation
└─ .env.example
```

## Deployment on the Pi
1. **Prepare the OS.** Install Raspberry Pi OS Lite (64-bit), then install Docker and the compose plugin.
2. **Build the image.** Use a multi-stage `Dockerfile`:
   - Stage 1: `node:20-slim` runs `npm ci && npm run build`.
   - Stage 2: `python:3.12-slim` installs the backend and copies in `frontend/build`.
   - Build it on the Pi, or cross-build on a laptop with `docker buildx --platform linux/arm64`.
3. **Run it.** In `docker-compose.yml`:
   - Set `restart: unless-stopped`.
   - Mount the volume `./data:/data`.
   - Publish the port on loopback only: `127.0.0.1:8000:8000`.
   - Read secrets from `.env`.
   - At startup, run `alembic upgrade head`, then start uvicorn.
4. **Set up Tailscale.** Run `curl -fsSL https://tailscale.com/install.sh | sh` and then `sudo tailscale up`. MagicDNS is on by default.
5. **Enable HTTPS.** Run `sudo tailscale serve --bg 8000`. The app is then at `https://<pi-name>.<tailnet>.ts.net` with a valid certificate, and the PWA and service worker need HTTPS. Because the app port is bound to localhost only, it can be reached **only** through Tailscale.
6. **Create the user.** Run `docker compose exec app python -m app.cli create-user`.
7. **Set up backups.** A systemd timer or cron job runs `scripts/backup.sh` nightly. It uses `sqlite3 planner.db ".backup ..."`, keeps 14 days of copies, and can optionally rsync them off the Pi.
8. **Updates:** `git pull && docker compose up -d --build`.

## Security notes
- No public exposure: nothing gets port-forwarded on the router. Tailscale ACLs can restrict access to your own devices.
- The app keeps its own login as a second layer, using argon2 password hashes.
- The session cookie is `HttpOnly`, `Secure`, and `SameSite=Lax`.
- Login attempts are rate-limited.

## Build milestones
1. **Skeleton:** FastAPI and SvelteKit scaffolds, the Dockerfile and compose file, a health check, and auth with login. Also build the **retro UI kit** (tokens, fonts, `Window`, `Button`, `MenuBar`, form controls) so every later page uses it from the start.
2. **To-dos and events,** plus the calendar page and the `/api/calendar` aggregation. This is the core of the app.
3. **Expenses:** categories, budgets, and the monthly summary chart.
4. **Workouts:** sets, the exercise library, and progress charts.
5. **Ideas:** markdown editor and tags.
6. **Dashboard, PWA, and export.**
7. **Pi deployment:** Tailscale serve and the backup timer.

## Verification
- **Backend:** `pytest` covers:
  - CRUD for each entity.
  - Auth: requests without a session get 401.
  - Calendar aggregation, including recurring-event expansion across the range.
  - Expense totals computed in cents.
- **Frontend:** `npm run check`, which runs svelte-check and the types. Then a manual pass in `npm run dev`, with Vite proxying `/api` to `localhost:8000`.
- **Responsive check:** in browser devtools device mode, test 375px (phone), 768px (tablet), and 1440px (laptop). Confirm there's no horizontal scroll, the dock or sidebar switches at the breakpoint, and forms are usable by touch. Then repeat the check on your real phone and laptop.
- **Container:** run `docker compose up --build` locally and confirm that login, creating each item type, and seeing the items on the calendar all work.
- **On the Pi:**
  - From a phone on mobile data (not home Wi-Fi) with Tailscale on, open `https://<pi>.<tailnet>.ts.net`, log in, and install it as a PWA.
  - Confirm that `http://<pi-lan-ip>:8000` is **not** reachable.
  - Run the backup script, then restore the copy to a temp file and open it with `sqlite3`.
