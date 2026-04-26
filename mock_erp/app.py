"""
Mock ERP API - FastAPI service for PO and Vendor data
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path

app = FastAPI(title="Mock ERP API", version="1.0")

# Load PO data
DATA_PATH = Path(__file__).parent / "data" / "PO_Records.json"
if not DATA_PATH.exists():
    DATA_PATH = Path(__file__).parent.parent / "data" / "erp_mock_data" / "PO_Records.json"

print(f"[ERP] Looking for PO data at: {DATA_PATH}")

if not DATA_PATH.exists():
    print(f"[ERP ERROR] PO data file not found at: {DATA_PATH}")
    print(f"[ERP] Creating empty PO data structure...")
    PO_DATA = []
else:
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            PO_DATA = json.load(f)
        print(f"[ERP] Loaded {len(PO_DATA)} purchase orders")
    except Exception as e:
        print(f"[ERP ERROR] Failed to load PO data: {e}")
        PO_DATA = []

# Models
class LineItem(BaseModel):
    item_code: str
    description: str
    qty: float
    unit_price: float
    currency: str

class PurchaseOrder(BaseModel):
    po_number: str
    vendor_id: str
    line_items: List[LineItem]

class Vendor(BaseModel):
    vendor_id: str
    vendor_name: str
    status: str

# Mock vendor data
VENDORS = {
    "VEND-001": {"vendor_id": "VEND-001", "vendor_name": "Global Logistics Ltd", "status": "active"},
    "VEND-002": {"vendor_id": "VEND-002", "vendor_name": "Secure Supplies Inc", "status": "active"},
    "VEND-003": {"vendor_id": "VEND-003", "vendor_name": "EuroBox SA", "status": "active"},
    "VEND-004": {"vendor_id": "VEND-004", "vendor_name": "HafenLogistik GmbH", "status": "active"},
    "VEND-005": {"vendor_id": "VEND-005", "vendor_name": "SwiftMove Couriers", "status": "active"},
    "VEND-006": {"vendor_id": "VEND-006", "vendor_name": "Mumbai Freight Services", "status": "active"}
}

@app.get("/")
def root():
    return {"message": "Mock ERP API - Running", "endpoints": ["/po/{po_number}", "/vendor/{vendor_id}"]}

@app.get("/po/{po_number}", response_model=PurchaseOrder)
def get_purchase_order(po_number: str):
    """Get purchase order by PO number"""
    for po in PO_DATA:
        if po["po_number"] == po_number:
            return po
    raise HTTPException(status_code=404, detail=f"PO {po_number} not found")

@app.get("/vendor/{vendor_id}", response_model=Vendor)
def get_vendor(vendor_id: str):
    """Get vendor information by vendor ID"""
    if vendor_id in VENDORS:
        return VENDORS[vendor_id]
    raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found")

if __name__ == "__main__":
    import uvicorn
    import sys
    
    print("=" * 60)
    print("🚀 Starting Mock ERP API on http://localhost:8001")
    print("=" * 60)
    print(f"Loaded {len(PO_DATA)} purchase orders")
    print(f"Loaded {len(VENDORS)} vendors")
    print("=" * 60)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    except Exception as e:
        print(f"[ERP ERROR] Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
