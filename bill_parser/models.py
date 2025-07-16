"""Pydantic data structures representing an invoice and its line items.
These models are shared by all bill-parser components.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class InvoiceItem(BaseModel):
    description: str
    hsn: Optional[str] = None
    batch: Optional[str] = None
    expiry: Optional[str] = None  # Keep as string – batch parsing varies
    quantity: float
    unit_price: float
    discount: Optional[float] = 0.0
    tax_percent: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    total: float


class Invoice(BaseModel):
    supplier_name: str
    supplier_gstin: Optional[str] = None
    invoice_number: str
    invoice_date: date
    buyer_gstin: Optional[str] = None

    items: List[InvoiceItem]

    subtotal: Optional[float] = None
    cgst: Optional[float] = None
    sgst: Optional[float] = None
    igst: Optional[float] = None
    grand_total: Optional[float] = None

    # Raw text is useful for debugging but excluded from export
    raw_text: str = Field(..., exclude=True, repr=False)

    confidence: float = Field(1.0, ge=0, le=1, description="Overall extraction confidence")

    @validator("supplier_name", "invoice_number", pre=True, always=True)
    def not_empty(cls, v: str) -> str:  # noqa: D401
        if not v:
            raise ValueError("Required field missing in parsed invoice")
        return v
