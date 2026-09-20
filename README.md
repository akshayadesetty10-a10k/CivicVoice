# CivicVoice

CivicVoice is a community reporting app for potholes, waste, water leaks, unsafe areas, broken streetlights, and more. Citizens can describe an issue by voice or text, let the built-in analyzer classify it, attach browser-detected location, and track its status. Administrators move reports through **Reported → In Progress → Resolved**.

## Features

- Responsive landing page and Leaflet/OpenStreetMap civic issue map.
- Browser speech-to-text (where supported), text reporting, and browser location detection.
- Local AI-style keyword analysis that produces category, severity, and a concise summary without an external API key.
- Persistent SQLite storage for users and reports.
- Email-or-phone sign-in flow, user-specific **My Complaints**, and session access control.
- Admin workspace for viewing every report and changing status.
- `PORT` support and a `/health` endpoint for deployment checks.

## Quick start

Requires Python 3.10+.

```bash
git clone https://github.com/snehithacodes-git/civicVoice.git
cd civicVoice
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8000`. On first startup, SQLite creates `instance/civicvoice.db`.

## Development sign-in

No Gmail, SMS, OAuth, or API secrets are hard-coded. The default local-demo flow accepts any valid email or phone number and displays the temporary development code `123456`. This behavior is controlled by `CIVICVOICE_AUTH_DEMO_MODE=true`.

The default development administrator is `admin@civicvoice.local`. Sign in with it and the development code to use the Admin workspace. Set your own comma-separated administrators with:

```bash
set CIVICVOICE_ADMIN_IDENTIFIERS=admin@example.com,lead@example.com
```

## Production deployment

Before public deployment, set a long random secret, turn off demo sign-in, and define administrators:

```bash
set CIVICVOICE_SECRET_KEY=<long-random-secret>
set CIVICVOICE_AUTH_DEMO_MODE=false
set CIVICVOICE_ADMIN_IDENTIFIERS=admin@your-domain.example
set PORT=8000
```

With demo mode disabled, the app deliberately refuses to fake sending a code. Connect a verified email/SMS provider (such as Auth0, Firebase Authentication, Twilio Verify, or company SSO) in `/api/auth/request-code` and `/api/auth/verify`, with credentials stored only in the host’s secret store. Never expose provider credentials in browser code or commit them to the repository. Run behind HTTPS using a production WSGI server such as Waitress or Gunicorn. For more than one app instance, use managed persistent storage instead of local SQLite.

## Architecture

| Layer | Responsibility |
| --- | --- |
| Flask (`app.py`) | Routes, sessions, keyword analysis, SQLite queries, JSON API |
| SQLite | `users` and `reports`, timestamps, ownership, and status workflow |
| Browser (`static/script.js`) | Speech recognition, geolocation, map markers, report/admin dashboards |
| UI (`templates/index.html`, `static/style.css`) | Landing page, sign-in, reporting, map, complaint views |

## Main API routes

- `POST /api/analyze` — analyze `{"text": "..."}`.
- `GET` / `POST /api/reports` — list public reports or create an authenticated report.
- `GET /api/reports?mine=1` — the signed-in user's complaints.
- `GET /api/admin/reports` and `PATCH /api/admin/reports/<id>/status` — administrator-only workflow controls.
- `POST /api/auth/request-code`, `POST /api/auth/verify`, `POST /api/auth/logout`, and `GET /api/auth/me` — sign-in/session APIs.
- `GET /api/stats` and `GET /health` — dashboard and deployment checks.

Every report stores its description, AI summary, category, severity, location text, optional coordinates, date/time, status, update time, and owning user.

## Test

```bash
python -m unittest discover -s tests
```

## License

See [LICENSE](LICENSE).
