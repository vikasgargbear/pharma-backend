#!/usr/bin/env python3
"""
Update Product schema to match the actual database columns
"""

# Product columns from our minimal model:
product_schema = '''# ---------------- Products ----------------
class ProductBase(BaseModel):
    org_id: Optional[str] = Field(None, example="org-123")
    product_code: str = Field(..., example="PARA500")
    product_name: str = Field(..., example="Paracetamol 500mg")
    generic_name: Optional[str] = Field(None, example="Paracetamol")
    brand_name: Optional[str] = Field(None, example="Crocin")
    manufacturer: Optional[str] = Field(None, example="GSK")
    manufacturer_code: Optional[str] = Field(None, example="GSK001")
    category: Optional[str] = Field(None, example="medication")
    subcategory: Optional[str] = Field(None, example="fever")
    category_id: Optional[int] = Field(None, example=1)
    product_type_id: Optional[int] = Field(None, example=1)
    base_uom_code: Optional[str] = Field("PIECE", example="PIECE")
    purchase_uom_code: Optional[str] = Field(None, example="BOX")
    sale_uom_code: Optional[str] = Field(None, example="STRIP")
    display_uom_code: Optional[str] = Field(None, example="STRIP")
    allow_loose_units: Optional[bool] = Field(False, example=False)
    hsn_code: Optional[str] = Field(None, example="3004")
    drug_schedule: Optional[str] = Field(None, example="H")
    prescription_required: Optional[bool] = Field(False, example=True)
    is_controlled_substance: Optional[bool] = Field(False, example=False)
    purchase_price: Optional[float] = Field(None, example=10.0)
    sale_price: Optional[float] = Field(None, example=18.0)
    mrp: Optional[float] = Field(None, example=20.0)
    trade_discount_percent: Optional[float] = Field(None, example=10.0)
    gst_percent: Optional[float] = Field(None, example=12.0)
    cgst_percent: Optional[float] = Field(None, example=6.0)
    sgst_percent: Optional[float] = Field(None, example=6.0)
    igst_percent: Optional[float] = Field(None, example=0.0)
    tax_category: Optional[str] = Field("standard", example="standard")
    minimum_stock_level: Optional[int] = Field(None, example=100)
    maximum_stock_level: Optional[int] = Field(None, example=1000)
    reorder_level: Optional[int] = Field(None, example=200)
    reorder_quantity: Optional[int] = Field(None, example=500)
    pack_size: Optional[str] = Field(None, example="10 tablets")
    pack_details: Optional[dict] = Field(None, example={"strips": 10, "tablets_per_strip": 10})
    barcode: Optional[str] = Field(None, example="8901030865278")
    barcode_type: Optional[str] = Field("EAN13", example="EAN13")
    alternate_barcodes: Optional[str] = Field(None, example="1234567890123")
    storage_location: Optional[str] = Field(None, example="A1-B2")
    shelf_life_days: Optional[int] = Field(None, example=730)
    notes: Optional[str] = Field(None, example="Store in cool dry place")
    tags: Optional[str] = Field(None, example="fever,pain-relief")
    search_keywords: Optional[str] = Field(None, example="paracetamol,fever,headache")
    category_path: Optional[str] = Field(None, example="medication/fever")
    is_active: Optional[bool] = Field(True, example=True)
    is_discontinued: Optional[bool] = Field(False, example=False)
    created_by: Optional[int] = Field(None, example=1)
    is_narcotic: Optional[bool] = Field(False, example=False)
    requires_cold_chain: Optional[bool] = Field(False, example=False)
    temperature_range: Optional[str] = Field(None, example="2-8°C")
    is_habit_forming: Optional[bool] = Field(False, example=False)
    therapeutic_category: Optional[str] = Field(None, example="Analgesic")
    salt_composition: Optional[str] = Field(None, example="Paracetamol 500mg")
    strength: Optional[str] = Field(None, example="500mg")
    pack_type: Optional[str] = Field(None, example="Strip")

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    product_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
'''

print(product_schema)