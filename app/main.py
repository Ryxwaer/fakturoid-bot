"""
Fakturoid Invoice REST API
FastAPI application for creating invoices from configurable templates
"""

import sys
import base64
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from termcolor import colored
from dotenv import load_dotenv

from app.config import get_config, AppConfig
from app.models import (
    InvoiceRequest,
    InvoiceResponse,
    InvoiceLine,
    ErrorResponse,
    TemplateInfo,
    TemplatesListResponse,
    HealthResponse
)
from app.fakturoid_service import FakturoidService, get_last_day_of_previous_month

sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Global service instance
FAKTUROID_SERVICE: FakturoidService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize services on startup"""
    global FAKTUROID_SERVICE
    
    print(colored("\n═══ FAKTUROID INVOICE API ═══\n", "blue", attrs=["bold"]))
    
    config = get_config()
    
    # Validate configuration
    if not config.FAKTUROID_CLIENT_ID or not config.FAKTUROID_CLIENT_SECRET:
        print(colored("✗ Missing Fakturoid credentials in environment", "red"))
        raise RuntimeError("Missing FAKTUROID_CLIENT_ID or FAKTUROID_CLIENT_SECRET")
    
    if not config.FAKTUROID_ACCOUNT_SLUG:
        print(colored("✗ Missing FAKTUROID_ACCOUNT_SLUG in environment", "red"))
        raise RuntimeError("Missing FAKTUROID_ACCOUNT_SLUG")
    
    # Initialize Fakturoid service
    FAKTUROID_SERVICE = FakturoidService(
        client_id=config.FAKTUROID_CLIENT_ID,
        client_secret=config.FAKTUROID_CLIENT_SECRET,
        account_slug=config.FAKTUROID_ACCOUNT_SLUG,
        user_agent=config.USER_AGENT
    )
    
    print(colored(f"✓ API ready with {len(config.list_templates())} templates\n", "green"))
    
    yield
    
    print(colored("\n✓ Shutting down...", "yellow"))


# Create FastAPI app
app = FastAPI(
    title="Fakturoid Invoice API",
    description="REST API for creating invoices from configurable templates",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    config = get_config()
    return HealthResponse(
        status="healthy",
        templates_loaded=len(config.list_templates())
    )


@app.get("/templates", response_model=TemplatesListResponse, tags=["Templates"])
async def list_templates():
    """
    List all available invoice templates
    
    Returns template names and their configuration (without fetching line details)
    """
    config = get_config()
    templates = config.list_templates()
    
    template_list = []
    for name, tmpl in templates.items():
        template_list.append(TemplateInfo(
            name=name,
            generator_id=tmpl.generator_id,
            subject_id=tmpl.subject_id,
            due_days=tmpl.due_days,
            description=tmpl.description
        ))
    
    return TemplatesListResponse(templates=template_list)


@app.get(
    "/templates/{template_name}",
    response_model=TemplateInfo,
    responses={404: {"model": ErrorResponse}},
    tags=["Templates"]
)
async def get_template_details(
    template_name: str = Path(..., description="Template name from configuration")
):
    """
    Get template details including available line names from Fakturoid
    
    Fetches the generator from Fakturoid to show available lines that can be invoiced
    """
    config = get_config()
    template = config.get_template(template_name)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found. Available: {list(config.list_templates().keys())}"
        )
    
    # Fetch generator to get line names
    try:
        generator = FAKTUROID_SERVICE.get_generator(template.generator_id)
        available_lines = [line["name"] for line in generator.get("lines", [])]
    except Exception as e:
        available_lines = None
        print(colored(f"⚠ Could not fetch generator lines: {e}", "yellow"))
    
    return TemplateInfo(
        name=template_name,
        generator_id=template.generator_id,
        subject_id=template.subject_id,
        due_days=template.due_days,
        description=template.description,
        available_lines=available_lines
    )


@app.post(
    "/invoice/{template_name}",
    response_model=InvoiceResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    tags=["Invoices"]
)
async def create_invoice(
    template_name: str = Path(..., description="Template name from configuration"),
    request: InvoiceRequest = ...
):
    """
    Create an invoice using a template
    
    - **template_name**: Name of the template (e.g., 'datasentics')
    - **lines**: Mapping of line names to quantities
    
    The invoice will be created with:
    - Issue date: Last day of previous month
    - Line prices: Fetched from Fakturoid generator template
    - Line quantities: From request body
    
    Returns the created invoice details with PDF as base64
    """
    config = get_config()
    template = config.get_template(template_name)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found. Available: {list(config.list_templates().keys())}"
        )
    
    if not request.lines:
        raise HTTPException(
            status_code=400,
            detail="Request must contain at least one line with quantity"
        )
    
    try:
        # 1. Fetch generator to get current prices
        generator = FAKTUROID_SERVICE.get_generator(template.generator_id)
        generator_lines = generator.get("lines", [])
        
        if not generator_lines:
            raise HTTPException(
                status_code=400,
                detail=f"Generator {template.generator_id} has no lines configured"
            )
        
        # 2. Build invoice lines (match quantities to template prices)
        invoice_lines = FAKTUROID_SERVICE.build_invoice_lines(
            generator_lines=generator_lines,
            quantities=request.lines
        )
        
        # 3. Create invoice
        issue_date = get_last_day_of_previous_month()
        invoice = FAKTUROID_SERVICE.create_invoice(
            generator_id=template.generator_id,
            subject_id=template.subject_id,
            lines=invoice_lines,
            issued_on=issue_date,
            due_days=template.due_days
        )
        
        # 4. Download PDF
        pdf_bytes = FAKTUROID_SERVICE.download_invoice_pdf(invoice["id"])
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        
        # 5. Build response
        response_lines = [
            InvoiceLine(
                name=line["name"],
                quantity=float(line["quantity"]),
                unit_name=line.get("unit_name", ""),
                unit_price=float(line.get("unit_price", 0)),
                vat_rate=float(line.get("vat_rate", 0))
            )
            for line in invoice.get("lines", [])
        ]
        
        return InvoiceResponse(
            success=True,
            invoice_id=invoice["id"],
            invoice_number=invoice["number"],
            total=float(invoice.get("total", 0)),
            currency=invoice.get("currency", "CZK"),
            issued_on=invoice.get("issued_on", issue_date),
            due_on=invoice.get("due_on", ""),
            pdf_base64=pdf_base64,
            lines=response_lines
        )
        
    except ValueError as e:
        # Line name mismatch
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(colored(f"✗ Error creating invoice: {e}", "red"))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create invoice: {str(e)}"
        )


@app.post("/templates/reload", tags=["Templates"])
async def reload_templates():
    """
    Reload templates from configuration file
    
    Use this after modifying templates.json without restarting the server
    """
    config = get_config()
    config.reload_templates()
    return {
        "success": True,
        "message": f"Reloaded {len(config.list_templates())} templates"
    }
