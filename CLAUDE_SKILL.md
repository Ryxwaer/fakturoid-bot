# Fakturoid Invoice API - Claude Skill

## Overview

This skill allows you to create invoices in Fakturoid and retrieve PDFs. The API automatically fetches current prices from Fakturoid templates - you only need to provide quantities (hours).

**Base URL:** `fakturoid.ryxwaer.com`

## Authentication

All endpoints (except `/health`) require HTTP Basic Auth.

```bash
curl -u "username:password" https://fakturoid.ryxwaer.com/templates
```

Or with header:
```bash
curl -H "Authorization: Basic $(echo -n 'username:password' | base64)" ...
```

---

## Datasentics Invoice

Creates a monthly invoice for Datasentics consulting work.

### Endpoint

```
POST /invoice/datasentics
```

### Request

```json
{
  "lines": {
    "Projektové práce - vyšší sazba": <hours_higher_rate>,
    "Interní projekty": <hours_internal>
  }
}
```

**Parameters:**
- `Projektové práce - vyšší sazba` - Hours for project work at higher rate
- `Interní projekty` - Hours for internal projects

### Example Request

```bash
curl -u "$API_USER:$API_PASS" -X POST https://fakturoid.ryxwaer.com/invoice/datasentics \
  -H "Content-Type: application/json" \
  -d '{
    "lines": {
      "Projektové práce - vyšší sazba": 10,
      "Interní projekty": 5
    }
  }'
```

### Response

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
  "lines": [
    {
      "name": "Projektové práce - vyšší sazba",
      "quantity": 10.0,
      "unit_name": "h",
      "unit_price": 423.0,
      "vat_rate": 0.0
    },
    {
      "name": "Interní projekty",
      "quantity": 5.0,
      "unit_name": "h",
      "unit_price": 360.0,
      "vat_rate": 0.0
    }
  ]
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether invoice was created |
| `invoice_id` | integer | Fakturoid invoice ID |
| `invoice_number` | string | Invoice number (e.g., "2026-0001") |
| `total` | float | **Total amount to pay** |
| `currency` | string | Currency code (CZK) |
| `issued_on` | string | Issue date (last day of previous month) |
| `due_on` | string | Payment due date |
| `pdf_base64` | string | Invoice PDF encoded as base64 |
| `lines` | array | Line items with quantities and prices |

### How to Save the PDF

Extract and decode the PDF directly from the response (no need to handle base64 in context):

```bash
curl -s -u "$API_USER:$API_PASS" -X POST https://fakturoid.ryxwaer.com/invoice/datasentics \
  -H "Content-Type: application/json" \
  -d '{"lines": {"Projektové práce - vyšší sazba": 10, "Interní projekty": 5}}' \
  | jq -r '.pdf_base64' | base64 -d > invoice.pdf
```

To get both the invoice details AND save the PDF:

```bash
# Save full response and extract PDF in one go
curl -s -u "$API_USER:$API_PASS" -X POST https://fakturoid.ryxwaer.com/invoice/datasentics \
  -H "Content-Type: application/json" \
  -d '{"lines": {"Projektové práce - vyšší sazba": 10, "Interní projekty": 5}}' \
  | tee >(jq -r '.pdf_base64' | base64 -d > invoice.pdf) \
  | jq 'del(.pdf_base64)'
```

This outputs the JSON response (without the large base64 field) while saving the PDF to file.

---

## Other Endpoints

### List Available Templates (requires auth)

```bash
curl -u "$API_USER:$API_PASS" https://fakturoid.ryxwaer.com/templates
```

Shows all configured invoice templates.

### Get Template Details (requires auth)

```bash
curl -u "$API_USER:$API_PASS" https://fakturoid.ryxwaer.com/templates/datasentics
```

Returns template configuration and available line names that can be invoiced.

### Health Check (no auth required)

```bash
curl https://fakturoid.ryxwaer.com/health
```

Returns API health status.

---

## Important Notes

1. **Issue Date**: Always set to the last day of the previous month (automatic)
2. **Prices**: Fetched live from Fakturoid generator template - if prices change in Fakturoid, invoices will use new prices
3. **Line Names**: Must match exactly as defined in Fakturoid generator (case-sensitive)
4. **PDF**: Always included in response as base64-encoded string

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 401 | Unauthorized (invalid or missing credentials) |
| 400 | Invalid request (wrong line names, missing data) |
| 404 | Template not found |
| 500 | Fakturoid API error |

Error response format:
```json
{
  "success": false,
  "error": "Error description",
  "detail": "Additional details"
}
```
