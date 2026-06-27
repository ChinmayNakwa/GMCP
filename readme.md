# Google Workspace MCP

A multi-user [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server suite that exposes Google Calendar, Gmail, Meet, and Sheets as tools for AI agents like Claude. Deployed on AWS with per-user OAuth isolation, this lets any MCP-compatible AI assistant act on a user's Google Workspace data on their behalf — without ever hardcoding credentials.

## Why this exists

Most MCP servers are built for a single user running everything locally. This project solves a harder problem: **multiple users, one deployment.** Each person authenticates once through a standard OAuth consent flow; their tokens are stored independently and refreshed automatically, so the same running server can safely serve many users at once.

## Architecture

```
                    ┌─────────────────────────┐
                    │   AWS EC2 (Ubuntu)      │
                    │                         │
   User Browser ───►│  nginx (port 80)        │
                    │   ├── /auth   → Flask   │──► Google OAuth
                    │   ├── /calendar → :8001 │──► Google Calendar API
                    │   ├── /gmail    → :8002 │──► Gmail API
                    │   ├── /meet     → :8003 │──► Google Meet API
                    │   └── /sheets   → :8004 │──► Google Sheets API
                    │                         │
                    │  systemd manages all    │
                    │  5 processes, restarts  │
                    │  on crash/reboot         │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │  AWS RDS (PostgreSQL)   │
                    │  user_tokens table      │
                    │  (per-user, per-service)│
                    └─────────────────────────┘
```

Each MCP server runs as an independent FastMCP process speaking **streamable-HTTP**, reverse-proxied through nginx under its own path. A lightweight Flask service handles the OAuth dance and persists refreshable tokens to Postgres, keyed by `user_id` and service name.

## Features

- **Google Calendar** — list, create, update, delete events; fetch by ID
- **Gmail** — search/list messages, fetch full message details, send mail with attachments
- **Google Meet** — create and retrieve Meet spaces
- **Google Sheets** — create spreadsheets, read/write ranges, append rows, clear ranges, find & replace
- **Per-user OAuth 2.0** — no shared credentials; each user grants their own scopes and gets isolated, auto-refreshing tokens
- **Production-style deployment** — nginx reverse proxy, systemd-managed services, PostgreSQL-backed persistence

## Tech stack

| Layer | Technology |
|---|---|
| MCP servers | Python, [FastMCP](https://gofastmcp.com) |
| Auth server | Flask |
| Token storage | PostgreSQL (AWS RDS) |
| Reverse proxy | nginx |
| Process management | systemd |
| Hosting | AWS EC2 |
| Google APIs | Calendar v3, Gmail v1, Meet v2, Sheets v4 |

## Project structure

```
.
├── auth/
│   └── auth_server.py        # OAuth flow: /auth/start, /auth/callback
├── models/
│   └── db.py                 # Token persistence (save_token / load_token)
├── google_auth/
│   └── services/              # Per-service credential + client builders
│       ├── google_calendar.py
│       ├── google_mail.py
│       ├── google_meet.py
│       └── google_sheets.py
├── mcp_server/
│   ├── run_calendar_mcp.py    # FastMCP tool definitions, port 8001
│   ├── run_gmail_mcp.py       # port 8002
│   ├── run_meet_mcp.py        # port 8003
│   └── run_sheets_mcp.py      # port 8004
├── server-configs/
│   ├── mcp                    # nginx site config
│   └── mcp-*.service          # systemd unit files
├── .env.example
└── requirements.txt
```

## Setup

> **Note on Docker files:** This repo still contains `Dockerfile`, `docker_files/*.Dockerfile`, and `docker-compose.yml` from an earlier iteration. The current deployment uses **systemd + nginx directly on the host** instead of containers (see `server-configs/`), which proved simpler to operate on a single free-tier EC2 instance. The Docker files are kept for reference but are not used in the deployment steps below.

### 1. Google Cloud Console

1. Create a project and enable the Calendar, Gmail, Meet, and Sheets APIs.
2. Create an **OAuth 2.0 Client ID** of type **Web application**.
3. Add an authorized redirect URI: `http://YOUR_HOST/auth/callback`
4. Download the client secret JSON and save it as `credentials/credentials.json`.
5. Add your Google account as a test user under **OAuth consent screen → Audience** while the app is in testing mode.

### 2. Database

```sql
CREATE TABLE user_tokens (
    user_id TEXT,
    service TEXT,
    token_json TEXT,
    PRIMARY KEY (user_id, service)
);
```

### 3. Environment

Copy `.env.example` to `.env` and fill in your values:

```env
DATABASE_URL=postgresql://user:pass@your-rds-endpoint:5432/postgres?sslmode=require
REDIRECT_URI=http://YOUR_HOST/auth/callback
FLASK_SECRET=a_random_string
```

### 4. Install & run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export PYTHONPATH=$(pwd)
python auth/auth_server.py            # OAuth server, port 5000
python mcp_server/run_calendar_mcp.py # repeat for gmail/meet/sheets
```

### 5. Deploy (systemd + nginx)

Unit files for each service live in `server-configs/`. Copy them to `/etc/systemd/system/`, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mcp-auth mcp-calendar mcp-gmail mcp-meet mcp-sheets
```

Copy `server-configs/mcp` to `/etc/nginx/sites-available/mcp`, symlink it into `sites-enabled/`, and reload nginx.

## Authenticating a user

Visit:

```
http://YOUR_HOST/auth/start?user_id=<any-identifier>
```

Complete the Google consent screen. The user's tokens are stored against that `user_id` and refreshed automatically on expiry.

## Connecting to Claude

Add each server as a remote MCP connector (via [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) for clients that only support local commands):

```json
{
  "mcpServers": {
    "GoogleCalendar": {
      "command": "npx",
      "args": ["mcp-remote", "http://YOUR_HOST/calendar/mcp", "--allow-http"]
    }
  }
}
```

Repeat for `/gmail/mcp`, `/meet/mcp`, and `/sheets/mcp`.

## Security notes

- `credentials/`, `.env`, and all token files are git-ignored — never commit secrets.
- Tokens are isolated per `user_id`; no user can access another's data.
- For production use beyond a demo, front `user_id` with a signed JWT or session-based auth instead of a plain query parameter, and move to HTTPS with a real domain + Let's Encrypt certificate.

## License

See [LICENSE.md](./LICENSE.md).
