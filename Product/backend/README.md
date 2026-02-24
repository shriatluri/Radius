# Radius Backend

The FastAPI-based backend for the Radius compliance platform.

## Overview

This is the core API server that provides:
- Transaction monitoring and ingestion
- Risk scoring and sanctions screening
- Wallet identity verification
- Travel Rule automation
- Audit-ready record generation
- CSV/JSON export capabilities
- Web dashboard serving (static files)

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database access
- **SQLite** - Default database (PostgreSQL for production)
- **Pydantic** - Data validation
- **uvicorn** - ASGI server

## Directory Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── transactions.py
│   │   ├── wallets.py
│   │   ├── payments.py
│   │   ├── reports.py
│   │   └── travel_rule.py
│   ├── core/             # Core application code
│   │   ├── config.py     # Configuration
│   │   ├── errors.py     # Error handling
│   │   └── security.py   # Authentication
│   ├── db/               # Database models and utilities
│   │   ├── models.py     # SQLAlchemy models
│   │   └── database.py   # Database setup
│   ├── services/         # Business logic
│   │   ├── risk.py       # Risk scoring
│   │   ├── sanctions.py  # Sanctions screening
│   │   └── travel_rule.py # Travel Rule handling
│   ├── static/           # Frontend build output (served at /)
│   ├── storage.py        # In-memory storage (for non-DB mode)
│   └── main.py           # Application entry point
├── exports/              # CSV export files
├── radius_dev.db         # SQLite database file
└── requirements.txt      # Python dependencies
```

## Installation

### Prerequisites

- Python 3.9+
- pip or uv

### Setup

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional):
   ```bash
   cp ../.env.example .env
   # Edit .env with your settings
   ```

## Running the Server

### Development Mode

Start the server with hot reload:

```bash
uvicorn app.main:app --reload --port 8000
```

Or from the project root:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The server will be available at **http://localhost:8000**

### Production Mode

Start without reload:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Base URL

All API endpoints are prefixed with `/v1/`

### Core Endpoints

**Transactions:**
- `POST /v1/transactions/ingest` - Ingest a new transaction
- `GET /v1/transactions` - List transactions (with filters)
- `GET /v1/transactions/{id}` - Get transaction by ID
- `GET /v1/transactions/{id}/audit` - Get audit record

**Wallets:**
- `POST /v1/wallets/verify` - Verify wallet ownership

**Payments:**
- `POST /v1/payments/annotate` - Annotate payment with metadata

**Reports:**
- `GET /v1/reports/export` - Export transactions (CSV/JSON)

**Travel Rule:**
- `POST /v1/travel-rule/transmit` - Transmit Travel Rule data

**Health:**
- `GET /health` - Health check endpoint

### API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

The API uses API key authentication via the `X-API-Key` header.

**Demo API Keys:**
- `sk_test_acme_123456`
- `sk_test_globalcorp_789012`

To create new API keys, see the API key generation logic in `app/core/security.py`.

## Configuration

Configuration is managed via environment variables (see `app/core/config.py`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///backend/radius_dev.db` | Database connection string |
| `USE_DATABASE` | `true` | Enable database persistence |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_TOKENS` | `100` | Max requests per burst |
| `RATE_LIMIT_REFILL_RATE` | `1.67` | Tokens per second (~100/min) |
| `API_VERSION` | `0.2.0` | API version |

## Database

### SQLite (Default)

For local development, SQLite is used by default. The database file is stored at `backend/radius_dev.db`.

**Initialize database:**
```bash
# Database is auto-initialized on first startup
uvicorn app.main:app --reload
```

### PostgreSQL (Production)

For production, use PostgreSQL:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/radius"
uvicorn app.main:app
```

## Testing

Run tests from the project root:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

## Development

### Adding a New Endpoint

1. Create or modify a route file in `app/api/`
2. Add the route handler function
3. Update the API router in `app/api/__init__.py` if needed
4. Add validation models in the route file or `app/core/`
5. Test using the interactive docs at `/docs`

### Adding a New Service

1. Create a new file in `app/services/`
2. Implement the business logic
3. Import and use in route handlers
4. Add tests in `tests/`

### Code Style

We follow PEP 8 style guidelines. Format code with:

```bash
black app/
isort app/
```

Lint with:

```bash
flake8 app/
mypy app/
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Find the process
lsof -ti:8000

# Kill it
kill -9 $(lsof -ti:8000)

# Or use a different port
uvicorn app.main:app --port 8001
```

### Database Locked

If you get "database is locked" errors with SQLite:

1. Close any other connections to the database
2. Restart the server
3. Or switch to PostgreSQL for concurrent access

### Import Errors

If you get import errors:

```bash
# Make sure you're in the backend/ directory
cd backend

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Static Files Not Serving

If the frontend dashboard doesn't load:

1. Verify `app/static/` exists and contains files
2. Rebuild the frontend: `cd ../frontend && npm run build`
3. Restart the FastAPI server

## Deployment

### Using Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t radius-backend .
docker run -p 8000:8000 radius-backend
```

### Using a Process Manager

For production deployments, use a process manager like **supervisord** or **systemd**.

**systemd example** (`/etc/systemd/system/radius.service`):

```ini
[Unit]
Description=Radius API
After=network.target

[Service]
Type=simple
User=radius
WorkingDirectory=/opt/radius/backend
Environment="PATH=/opt/radius/.venv/bin"
ExecStart=/opt/radius/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable radius
sudo systemctl start radius
```

### Behind a Reverse Proxy

Use nginx or Caddy to handle HTTPS and static file serving:

**nginx example:**

```nginx
server {
    listen 80;
    server_name api.radius.dev;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Performance

### Optimization Tips

1. **Use PostgreSQL** for production (better concurrency than SQLite)
2. **Enable connection pooling** (configured in `app/db/database.py`)
3. **Add caching** for frequently accessed data (Redis)
4. **Use workers** for horizontal scaling (`--workers 4`)
5. **Enable gzip** compression in nginx/Caddy
6. **Set up CDN** for static assets

### Monitoring

Add monitoring with:
- **Prometheus** + **Grafana** for metrics
- **Sentry** for error tracking
- **DataDog** or **New Relic** for APM

## Security

### Production Checklist

- [ ] Use HTTPS (TLS certificates)
- [ ] Rotate API keys regularly
- [ ] Enable rate limiting
- [ ] Use PostgreSQL with encrypted connections
- [ ] Set up firewall rules
- [ ] Enable CORS only for trusted origins
- [ ] Use environment variables for secrets (never commit to git)
- [ ] Keep dependencies updated (`pip list --outdated`)
- [ ] Run security scans (`bandit -r app/`)
- [ ] Enable database backups

## Maintenance

### Database Backups

**SQLite:**
```bash
# Backup
cp radius_dev.db radius_dev.backup.db

# Restore
cp radius_dev.backup.db radius_dev.db
```

**PostgreSQL:**
```bash
# Backup
pg_dump radius > radius_backup.sql

# Restore
psql radius < radius_backup.sql
```

### Updating Dependencies

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade fastapi

# Update all (carefully!)
pip install --upgrade -r requirements.txt
```

### Logs

View logs:

```bash
# If running with systemd
journalctl -u radius -f

# If running manually
# Logs go to stdout/stderr
```

## Support

- **Issues**: See project GitHub issues
- **Docs**: See `/docs` folder in project root
- **API Docs**: http://localhost:8000/docs

## License

Proprietary - Radius Compliance Platform
