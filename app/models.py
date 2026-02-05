"""
Pydantic Models for API Request/Response
"""

from typing import Dict, Optional, List
from pydantic import BaseModel, Field


class InvoiceRequest(BaseModel):
    """Request model for creating an invoice"""
    lines: Dict[str, float] = Field(
        ...,
        description="Mapping of line names to quantities (e.g., hours)",
        examples=[{"Projektové práce - vyšší sazba": 10, "Interní projekty": 5}]
    )


class InvoiceLine(BaseModel):
    """Single invoice line item"""
    name: str
    quantity: float
    unit_name: str
    unit_price: float
    vat_rate: float


class InvoiceResponse(BaseModel):
    """Response model for created invoice (metadata only, no PDF)"""
    success: bool
    invoice_id: int
    invoice_number: str
    total: float
    currency: str
    issued_on: str
    due_on: str
    lines: List[InvoiceLine]
    pdf_url: str  # URL to download PDF


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None


class TemplateInfo(BaseModel):
    """Template information for listing"""
    name: str
    generator_id: int
    subject_id: int
    due_days: int
    description: Optional[str] = None
    available_lines: Optional[List[str]] = None


class TemplatesListResponse(BaseModel):
    """Response for listing available templates"""
    templates: List[TemplateInfo]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    templates_loaded: int
