# Fakturoid Invoice API - Claude Skill

## Overview

This skill allows you to create invoices in Fakturoid and retrieve PDFs. The API automatically fetches current prices from Fakturoid templates - you only need to provide quantities (hours).

**Base URL:** `https://fakturoid.ryxwaer.com`

## Authentication

All endpoints (except `/health`) require HTTP Basic Auth.

```bash
curl -u "$API_USER:$API_PASS" https://fakturoid.ryxwaer.com/
```

---

## Datasentics Invoice

Creates a monthly invoice for Datasentics consulting work.

### Step 1: Create Invoice

```
POST /invoice/datasentics
```

**Request:**
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

**Example:**
```bash
curl -s -u "$API_USER:$API_PASS" -X POST https://fakturoid.ryxwaer.com/invoice/datasentics \
  -H "Content-Type: application/json" \
  -d '{"lines": {"Projektové práce - vyšší sazba": 10, "Interní projekty": 5}}'
```

**Response:**
```json
{
  "success": true,
  "invoice_id": 123456,
  "invoice_number": "20260001",
  "filename": "adampolicek-20260001.pdf",
  "total": 6030.0,
  "currency": "CZK",
  "issued_on": "2026-01-31",
  "due_on": "2026-02-15",
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
  ],
  "pdf_url": "/invoice/123456/pdf"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether invoice was created |
| `invoice_id` | integer | Fakturoid invoice ID |
| `invoice_number` | string | Invoice number (e.g., "20260001") |
| `filename` | string | Suggested PDF filename (e.g., "adampolicek-20260001.pdf") |
| `total` | float | **Total amount to pay - VERIFY THIS!** |
| `currency` | string | Currency code (CZK) |
| `issued_on` | string | Issue date (last day of previous month) |
| `due_on` | string | Payment due date |
| `lines` | array | Line items with quantities and prices |
| `pdf_url` | string | Endpoint to download PDF |

### Step 2: Validate Total

Before downloading the PDF, verify the `total` amount is correct based on the data provided.

### Step 3: Download PDF

After confirming the total is correct, download the PDF directly to file:

```
GET /invoice/{invoice_id}/pdf
```

**Example (save directly to file):**
```bash
curl -s -u "$API_USER:$API_PASS" https://fakturoid.ryxwaer.com/invoice/123456/pdf > invoice.pdf
```

The PDF is returned directly as binary content (application/pdf), not base64 encoded.

---

## Complete Workflow Example

```bash
# 1. Create invoice and get metadata
RESPONSE=$(curl -s -u "$API_USER:$API_PASS" -X POST https://fakturoid.ryxwaer.com/invoice/datasentics \
  -H "Content-Type: application/json" \
  -d '{"lines": {"Projektové práce - vyšší sazba": 10, "Interní projekty": 5}}')

# 2. Check the response (total, invoice_number, etc.)
echo "$RESPONSE" | jq

# 3. Extract invoice_id and filename, then download PDF
INVOICE_ID=$(echo "$RESPONSE" | jq -r '.invoice_id')
FILENAME=$(echo "$RESPONSE" | jq -r '.filename')
curl -s -u "$API_USER:$API_PASS" "https://fakturoid.ryxwaer.com/invoice/$INVOICE_ID/pdf" > "$FILENAME"
```

---

## Other Endpoints

### List Available Templates (requires auth)

```bash
curl -u "$API_USER:$API_PASS" https://fakturoid.ryxwaer.com/templates
```

### Get Template Details (requires auth)

```bash
curl -u "$API_USER:$API_PASS" https://fakturoid.ryxwaer.com/templates/datasentics
```

Returns available line names that can be invoiced.

### Health Check (no auth required)

```bash
curl https://fakturoid.ryxwaer.com/health
```

---

## Important Notes

1. **Issue Date**: Always set to the last day of the previous month (automatic by template)
2. **Prices**: Fetched live from Fakturoid generator template - if prices change in Fakturoid, invoices will use new prices
3. **Line Names**: Must match exactly as defined in Fakturoid generator (case-sensitive)
4. **Validation**: Always verify the `total` amount before downloading the PDF
5. **PDF Download**: Returns binary PDF directly - pipe to file with `> invoice.pdf`

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 401 | Unauthorized (invalid or missing credentials) |
| 400 | Invalid request (wrong line names, missing data) |
| 404 | Template or invoice not found |
| 500 | Fakturoid API error |

Error response format:
```json
{
  "success": false,
  "error": "Error description",
  "detail": "Additional details"
}
```
