# Fakturoid Invoice Bot - Documentation

## Overview

REST API for automated invoice creation in Fakturoid. Uses OAuth Client Credentials Flow, creates invoices from configurable generator templates, and returns PDFs as base64.

## Architecture

```
fakturoid-bot/
├── app/
│   ├── __init__.py           # Package marker
│   ├── main.py               # FastAPI application
│   ├── config.py             # Configuration management
│   ├── models.py             # Pydantic models
│   └── fakturoid_service.py  # Fakturoid API client
├── config/
│   └── templates.json        # Invoice templates configuration
├── Dockerfile                # Container image
├── docker-compose.yml        # Container orchestration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore               # Git ignore patterns
├── .cursorignore            # Cursor ignore patterns
├── CLAUDE_SKILL.md          # AI assistant skill documentation
├── features.md              # Feature tracking
└── documentation.md         # This file
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/templates` | GET | List all templates |
| `/templates/{name}` | GET | Get template details with available lines |
| `/invoice/{name}` | POST | Create invoice and get PDF |
| `/templates/reload` | POST | Reload templates without restart |

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Fakturoid credentials
```

### 2. Run with Docker

```bash
docker compose up -d
```

### 3. Create Invoice

```bash
curl -X POST http://localhost:8000/invoice/datasentics \
  -H "Content-Type: application/json" \
  -d '{"lines": {"Projektové práce - vyšší sazba": 10, "Interní projekty": 5}}'
```

## Template Configuration

Templates are defined in `config/templates.json`:

```json
{
  "template_name": {
    "generator_id": 12345,
    "subject_id": 67890,
    "due_days": 14,
    "description": "Optional description"
  }
}
```

**Fields:**
- `generator_id`: Fakturoid generator ID (template with prices)
- `subject_id`: Fakturoid subject ID (client)
- `due_days`: Payment due in days (default: 14)
- `description`: Optional human-readable description

**Adding new templates:** Just add entry to `templates.json` and call `POST /templates/reload` (or restart container).

## Invoice Creation Flow

1. **Request received** with template name and quantities
2. **Fetch generator** from Fakturoid API to get current prices
3. **Build lines** matching quantities to template prices
4. **Create invoice** with issue date = last day of previous month
5. **Download PDF** from Fakturoid
6. **Return response** with invoice details and base64 PDF

## Classes & Modules

### AppConfig (config.py)
Singleton configuration manager loading from environment and JSON.

### FakturoidService (fakturoid_service.py)
OAuth-authenticated client for Fakturoid API v3.

| Method | Description |
|--------|-------------|
| `get_generator(id)` | Fetch generator with line prices |
| `create_invoice(...)` | Create invoice from generator |
| `download_invoice_pdf(id)` | Get PDF bytes |
| `build_invoice_lines(...)` | Match quantities to template prices |

### Pydantic Models (models.py)
- `InvoiceRequest`: Input with line quantities
- `InvoiceResponse`: Output with PDF base64
- `TemplateInfo`: Template configuration details

## Authentication

Uses OAuth 2.0 Client Credentials Flow:
1. Exchange credentials for access token at `/oauth/token`
2. Use Bearer token for API requests
3. Auto-refresh before expiry (5 min buffer)

Reference: https://www.fakturoid.cz/api/v3/authorization

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FAKTUROID_CLIENT_ID` | Yes | OAuth Client ID |
| `FAKTUROID_CLIENT_SECRET` | Yes | OAuth Client Secret |
| `FAKTUROID_ACCOUNT_SLUG` | Yes | Fakturoid account slug |
| `USER_AGENT` | No | User-Agent header |
| `API_PORT` | No | API port (default: 8000) |
| `TEMPLATES_PATH` | No | Path to templates.json |

## Error Handling

- OAuth failures: 401/403 with error description
- Invalid template: 404 with available templates
- Invalid line name: 400 with available line names
- API errors: 500 with error details

Console output uses color coding:
- 🟢 Green: Success
- 🟡 Yellow: In progress
- 🔴 Red: Error
- 🔵 Cyan: API calls

## Discussion Log

### 2026-02-05
- Initial implementation with Client Credentials Flow
- Generator-based invoice creation
- PDF download functionality

### 2026-02-05 (Update)
- Refactored to REST API with FastAPI
- Configurable templates via JSON
- Dynamic price fetching from generators
- Docker containerization
- Base64 PDF response
