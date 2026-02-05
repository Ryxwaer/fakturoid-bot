# Fakturoid Invoice Bot - Features

## Current Features

### v2.0 - REST API Release

- [x] **REST API** - FastAPI-based HTTP server
- [x] **Configurable Templates** - JSON-based template configuration
- [x] **Dynamic Pricing** - Fetches current prices from Fakturoid generators
- [x] **OAuth Authentication** - Client Credentials Flow for API v3
- [x] **Token Management** - Automatic token refresh before expiry
- [x] **PDF Download** - Returns invoice PDF as base64
- [x] **Docker Support** - Dockerfile and docker-compose.yml
- [x] **Health Check** - `/health` endpoint for monitoring
- [x] **Template Reload** - Hot reload without restart
- [x] **Auto Issue Date** - Last day of previous month

### v1.0 - CLI Release (Legacy)

- [x] **CLI Interface** - Interactive hour input
- [x] **Generator Support** - Load templates from Fakturoid
- [x] **Invoice Creation** - Create invoices from templates
- [x] **PDF File Download** - Save PDF to disk

## API Usage Examples

### List Available Templates

```bash
curl http://localhost:8000/templates
```

### Get Template Details (with available lines)

```bash
curl http://localhost:8000/templates/datasentics
```

Response:
```json
{
  "name": "datasentics",
  "generator_id": 261281,
  "subject_id": 22805505,
  "due_days": 15,
  "available_lines": [
    "Projektové práce - vyšší sazba",
    "Interní projekty"
  ]
}
```

### Create Invoice

```bash
curl -X POST http://localhost:8000/invoice/datasentics \
  -H "Content-Type: application/json" \
  -d '{
    "lines": {
      "Projektové práce - vyšší sazba": 10,
      "Interní projekty": 5
    }
  }'
```

Response:
```json
{
  "success": true,
  "invoice_id": 123456,
  "invoice_number": "2026-0001",
  "total": 6030.0,
  "currency": "CZK",
  "issued_on": "2026-01-31",
  "due_on": "2026-02-15",
  "pdf_base64": "JVBERi0xLjQK...",
  "lines": [...]
}
```

### Decode PDF (bash)

```bash
echo "$PDF_BASE64" | base64 -d > invoice.pdf
```

## Planned Features

### v2.1 - Enhancements

- [ ] **API Authentication** - Bearer token / API key for endpoints
- [ ] **Custom Issue Date** - Optional override in request
- [ ] **Partial Lines** - Invoice only specified lines (skip others)
- [ ] **Email Sending** - Send invoice via Fakturoid API
- [ ] **Webhook Notifications** - Notify on invoice creation

### v2.2 - Integrations

- [ ] **Time Tracking** - Import hours from Toggl, Clockify
- [ ] **Slack Bot** - Create invoices via Slack commands
- [ ] **Scheduled Invoices** - Cron-based generation

## API Reference

Based on Fakturoid API v3: https://www.fakturoid.cz/api/v3
