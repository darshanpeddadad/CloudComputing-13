# Fulda Fall 2025 Team2 Backend

FastAPI backend application for the Fulda Fall 2025 Team2 project.

## Setup

### Local Development (without Docker)

1. Create and activate a virtual environment:

   **For bash/zsh (macOS/Linux):**
   ```bash
   cd Backend
   python3 -m venv venv
   source venv/bin/activate
   ```

   **For fish shell:**
   ```fish
   cd Backend
   python3 -m venv venv
   source venv/bin/activate.fish
   ```

   **For Windows PowerShell:**
   ```powershell
   cd Backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **For Windows CMD:**
   ```cmd
   cd Backend
   python -m venv venv
   venv\Scripts\activate.bat
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment variables:
   ```bash
   cp env.example .env
   ```
   **Note:** On Windows, use `copy env.example .env` instead of `cp`.

4. Update the `.env` file with your configuration values:
   - `DATABASE_URL` defaults to SQLite (`sqlite+aiosqlite:///./app.db`) if unset.
   - For MySQL 8, set `DATABASE_URL=mysql+asyncmy://<user>:<pass>@<host>:3306/<db>`.
   - Provide `ADMIN_EMAIL` / `ADMIN_PASSWORD` (and optional name/DOB fields) so the startup seeder can create the first admin account automatically.
   - `BACKEND_CORS_ORIGINS` accepts a JSON array or comma-separated list of allowed frontend URLs (use `["*"]` to allow every origin in dev).

5. Initialize the database:
   ```bash
   alembic upgrade head
   ```

### Docker Setup (local dev)

This stack lives entirely under `Backend/` so it does not interfere with the server-side configuration.

1. Copy environment variables:
   ```bash
   cd Backend
   cp env.example .env
   ```
   **Note:** On Windows, use `copy env.example .env` instead of `cp`.

2. Update the `.env` file with your configuration values:
   - `DATABASE_URL` defaults to MySQL 8 connection string if unset.
   - MySQL 8 credentials (defaults: `fulda_user` / `fulda_pass`).
   - Provide `ADMIN_EMAIL` / `ADMIN_PASSWORD` (and optional name/DOB fields) so the startup seeder can create the first admin account automatically.
   - `BACKEND_CORS_ORIGINS` accepts a JSON array or comma-separated list of allowed frontend URLs (use `["*"]` to allow every origin in dev).

3. Build and start the services:
   ```bash
   docker compose up --build
   ```

4. The backend container will:
   - Wait for MySQL to become available
   - Run `alembic upgrade head` to apply migrations
   - Boot Uvicorn with automatic role/admin seeding on startup

5. Access the API:
   - Through Nginx at http://localhost:8080 (Swagger UI at `/docs`)
   - MySQL 8 is mapped to `localhost:3306` with credentials from `.env`

6. Stop the stack when finished:
   ```bash
   docker compose down
   ```
   Use `docker compose down -v` to remove the MySQL data volume.

## Running the Application

### Local Development (without Docker)

After completing the local setup above, run the application:

```bash
cd Backend
python main.py
```

Or with Uvicorn directly:
```bash
cd Backend
uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload
```

### Docker (local dev)

After completing the Docker setup above, the application runs automatically when you execute `docker compose up --build`. The services will be available at http://localhost:8080.

## API Documentation

Once the server is running, you can access:

**Local Development (without Docker):**
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- API base path: http://localhost:8000/api
- WebSocket chat endpoints are not listed in Swagger; see "WebSocket Chat (manual docs)" below.
- Socket.IO server is exposed at the default path `/socket.io` (see "Socket.IO usage" below).

**Docker (local dev):**
- Interactive API docs: http://localhost:8080/docs
- Alternative docs: http://localhost:8080/redoc
- API base path: http://localhost:8080/api
- WebSocket chat endpoints are not listed in Swagger; see "WebSocket Chat (manual docs)" below.
- Socket.IO server is exposed at the default path `/socket.io` (see "Socket.IO usage" below).

## Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check endpoint

## Socket.IO chat (preferred)

The Socket.IO server at `/socket.io` replaces the legacy `/ws/...` chat endpoints (those are now deprecated and should not be used). Start uvicorn with `main:socket_app` to ensure the Socket.IO server is running.

- **Handshake**
  - Path: `/socket.io`
  - Auth: `auth: { token: "<JWT>" }` (raw token; server adds `Bearer`), or `?token=<JWT>` query param, or `Authorization` header.
  - Transports: websocket (recommended).
  - Invalid/missing tokens are rejected during the handshake.

### Events: common
- `server:connected` → emitted to the connecting client after a successful handshake.
- `server:disconnected` → emitted when a client disconnects.
- Errors for chat flows are emitted on `direct:error` or `event_group:error`.

### Events: direct chat (`direct:*`)
Direct chats are room-scoped; room IDs are provided after join. Message length max: 4096 chars; empty/whitespace rejected.
- `direct:join` → `{target_user_id, event_id?}`  
  - Admins: can DM anyone without `event_id`; context is `admin`.  
  - Non-admins: must include `event_id` and one side must be the event organizer.  
  - Organizer cannot initiate to non-participants unless the room already exists (recipient initiated first).  
  - If the event has ended, organizer/attendee DMs are rejected.
- `direct:joined` (to sender) → `{room_id, context, event_id, target_user_id}`
- `direct:message` → `{room_id, content}` (requires prior join)
- `direct:message` (broadcast) → `{room_id, room_type:"direct", sender_id, content, context}`
- `direct:error` → `{message}` on validation failures

### Events: event group chat (`event_group:*`)
Group chat per event; message length max 4096 chars; empty/whitespace rejected. When an event ends, members receive `event_group:ended` and are disconnected.

**Important:** Event group chat is only active when the event is **APPROVED**. Unapproved or ended events reject join attempts and block messaging.

**Auto-addition rules:**
- When an admin approves an event, the event group chat room is automatically created with:
  - All admins added as `owner` role
  - The event organizer added as `owner` role
- When a user purchases a ticket for an approved event, they are automatically added to the chat room as `participant` role
- Users with `EventParticipation` records are also considered participants

- `event_group:join` → `{event_id}`  
  - **Requirements:** Event must be APPROVED (not pending/rejected) and not ended
  - **Roles:** Organizer and admins join as `owner`; ticket holders and participants join as `participant`; others are rejected
  - Event ID must be a valid UUID of an approved, active event
- `event_group:joined` (to sender) → `{room_id, event_id, role}`
- `event_group:participants` (broadcast) → `{room_id, event_id, participants:[{user_id, role}]}` whenever someone joins/leaves/disconnects. Includes all database participants (admins, organizer, ticket holders) even if not currently connected.
- `event_group:message` → `{room_id, content}` (requires prior join)
  - Messages are blocked if the event has ended or is not approved
  - When a message is attempted on an ended event, `event_group:ended` is emitted and clients are disconnected
- `event_group:message` (broadcast) → `{room_id, room_type:"event_group", event_id, sender_id, content}`
- `event_group:ended` → `{room_id, event_id, message}` when the event ends mid-session; clients are disconnected and messaging is disabled.
- `event_group:leave` → `{room_id?, event_id?}` removes the user from active connections and triggers a participants broadcast.
- `event_group:error` → `{message}` on validation failures (e.g., "Event is not approved", "Event has ended", "Not a participant").

### Quick JS example
```js
import { io } from "socket.io-client";
const socket = io("http://localhost:8000", {
  path: "/socket.io",
  auth: { token: "<JWT>" },
  transports: ["websocket"],
});
socket.on("event_group:participants", console.log);
socket.emit("event_group:join", { event_id: "<event-id>" });
```

### Events: SOS Alerts (`sos:*`)
SOS alerts are critical broadcasts sent to all administrators.

- **Room**: `admin_global` (Admins are automatically added to this room upon connection).
- `sos:alert` → emitted when a user triggers an SOS.
  - **Payload**: `{id, event_id, user_id, latitude, longitude, message, status, created_at, user: {id, first_names, last_name, email}, event: {id, title, location}}`
  - **Receivers**: All connected administrators.


## WebSocket chat (deprecated)

Legacy WebSocket endpoints under `/ws/...` are kept temporarily for compatibility but are deprecated in favor of the Socket.IO API above. Prefer the Socket.IO events for all new work.

## Testing

Run tests using pytest:

**Local execution (without Docker):**
Run from the project root directory:
```bash
Backend/venv/bin/pytest Backend/tests -q
```

## Database Migrations & Seeding

Alembic handles schema migrations using the async SQLAlchemy metadata.

- Auto-apply latest migration: `alembic upgrade head`
- Create a new migration from model changes: `alembic revision --autogenerate -m "description"`
- Roll back: `alembic downgrade -1`
- When adding models/fields, update the SQLAlchemy models first, then run `alembic revision --autogenerate -m "short_description"` to capture the changes, review the generated script, and commit it alongside the model edits.

Seeding (roles + default admin) runs automatically on application startup. Configure `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and optional name/DOB fields in `.env`. Docker `compose up` executes migrations first, then FastAPI's startup hook seeds roles/admin.  

To seed demo event categories, organizers, and events manually (not run on startup):

**Docker execution (local dev):**
Run from the `Backend/` directory:
```bash
cd Backend
docker exec -e PYTHONPATH=/app fulda-backend-dev python scripts/seed_events.py
```

**Docker execution (production):**
Run from the project root directory:
```bash
docker exec -e PYTHONPATH=/app fastapi-backend python scripts/seed_events.py
```

**Local execution (without Docker):**
Run from the `Backend/` directory:
```bash
cd Backend
venv/bin/python scripts/seed_events.py
```

This script:
- Creates 10 users with the 'user' role (if they don't exist)
- Seeds 11 event categories
- Creates 50 events (25 approved, 15 pending, 10 rejected) with faker-generated titles and descriptions
- Assigns events to the 10 users as organizers
- Runs idempotently—rerunning it won't duplicate data if events already exist

**Note:** The event seeder requires the 'user' role to exist. This is automatically created on application startup via the FastAPI lifespan hook.

## Project Structure

```
Backend/
├── main.py               # Main FastAPI application
├── app/
│   ├── database/         # Async SQLAlchemy engine/session setup (Alembic uses this metadata)
│   ├── seeders/          # Startup seeding for base roles/admin
│   ├── auth/             # Authentication domain (routers, controllers, services, repositories, models)
│   └── interests/        # Interest domain (models, repositories, services)
├── scripts/              # Manual seeding scripts
│   └── seed_events.py    # Seed event categories, organizers, and events
├── alembic.ini           # Alembic configuration
├── migrations/           # Alembic environment & versioned migrations
├── requirements.txt      # Python dependencies
├── env.example           # Environment variables template
├── docker-compose.yml    # Backend-only docker stack (FastAPI + MySQL + Nginx)
├── docker/
│   └── nginx/default.conf
└── README.md             # This file
```

## Naming Conventions

We follow the conventions described at [VisualGit Naming Conventions](https://visualgit.readthedocs.io/en/latest/pages/naming_convention.html):
- Modules/files use `snake_case` so filenames map directly to their primary class or concept (e.g., `auth_controller.py` defines `AuthController`).
- Classes use `PascalCase` (e.g., `AuthService`, `UserRepository`).
- Functions and variables use `snake_case`.
- Constants use `UPPER_SNAKE_CASE`.

Keeping to these rules makes it easy to locate classes by filename and keeps the layered architecture predictable.

### Domain Layers

Every feature area is structured by layers:
- **Presentation:** FastAPI routers plus request/response DTOs (e.g., `presentation/<domain>_router.py`).
- **Controllers:** Thin coordinators translating presentation DTOs into service calls (`controllers/<domain>_controller.py`).
- **Services:** Business logic, orchestration, and coordination of security/validation concerns (`services/<domain>_service.py`).
- **Repositories:** Database persistence via SQLAlchemy (`repositories/<entity>_repository.py`) using async sessions.
- **Models:** ORM entities and relationships (`models/*.py`) plus join tables (`models/associations.py`).
- **Security:** Hashing/token utilities or other domain-specific helpers (`security/*.py`).
- **Validation/Schemas:** Internal command/query DTOs (Pydantic models) shared between layers (`schemas/*.py`); prefer Pydantic validators over ad-hoc checks.

When adding new domains or features, mirror this structure so responsibilities stay separated and test coverage remains focused.

### Seeding & Admin Account

On startup the application:
1. Ensures core tables exist via the async SQLAlchemy engine.
2. Seeds the `admin` and `user` roles.
3. Creates/updates an admin user using `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and optional name/DOB fields from `.env`.

Keep those env variables set (or override them in deployment) so environments always have a bootstrap administrator.
