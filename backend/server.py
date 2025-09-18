from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Request, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import qrcode
import io
import base64
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone
import hmac
import hashlib
from enum import Enum
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Fishing Permits API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Enums
class PermitType(str, Enum):
    DAILY = "daily"
    MONTHLY = "monthly" 
    YEARLY = "yearly"

class PermitStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

# Models
class CustomerInfo(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    country_code: str = "PL"

class PermitRequest(BaseModel):
    customer: CustomerInfo
    permit_types: List[PermitType]

class FishingPermit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    permit_type: PermitType
    price: float
    validity_days: int
    description: str
    customer: CustomerInfo
    status: PermitStatus = PermitStatus.PENDING
    issue_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expiry_date: datetime
    qr_code: Optional[str] = None
    order_id: Optional[str] = None

class PermitOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    customer: CustomerInfo
    permits: List[dict]
    total_amount: float
    currency: str = "PLN"
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payment_url: Optional[str] = None

# Configuration
PERMIT_PRICES = {
    PermitType.DAILY: 25.00,
    PermitType.MONTHLY: 150.00,
    PermitType.YEARLY: 500.00
}

PERMIT_VALIDITY = {
    PermitType.DAILY: 1,
    PermitType.MONTHLY: 30,
    PermitType.YEARLY: 365
}

# Helper functions
def generate_qr_code(permit_id: str, customer_name: str) -> str:
    """Generate QR code for permit verification"""
    qr_data = f"PERMIT:{permit_id}:NAME:{customer_name}:VERIFIED"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def calculate_expiry_date(permit_type: PermitType, issue_date: datetime) -> datetime:
    """Calculate permit expiry date"""
    validity_days = PERMIT_VALIDITY[permit_type]
    return issue_date + timedelta(days=validity_days)

# Database operations
async def store_permit_order(order: PermitOrder):
    """Store permit order in database"""
    order_dict = order.dict()
    order_dict['created_at'] = order_dict['created_at'].isoformat()
    await db.permit_orders.insert_one(order_dict)

async def get_permit_order(order_id: str):
    """Get permit order from database"""
    order = await db.permit_orders.find_one({"order_id": order_id})
    return order

async def update_order_status(order_id: str, status: str):
    """Update order status"""
    await db.permit_orders.update_one(
        {"order_id": order_id},
        {"$set": {"status": status}}
    )

async def store_permit(permit: FishingPermit):
    """Store permit in database"""
    permit_dict = permit.dict()
    permit_dict['issue_date'] = permit_dict['issue_date'].isoformat()
    permit_dict['expiry_date'] = permit_dict['expiry_date'].isoformat()
    await db.fishing_permits.insert_one(permit_dict)

async def get_permits_by_order(order_id: str):
    """Get all permits for an order"""
    permits = await db.fishing_permits.find({"order_id": order_id}, {"_id": 0}).to_list(length=None)
    return permits

async def verify_permit_qr(permit_id: str):
    """Verify permit by ID"""
    permit = await db.fishing_permits.find_one({"id": permit_id})
    if not permit:
        return {"valid": False, "message": "Permit not found"}
    
    # Check if permit is active and not expired
    expiry_date = datetime.fromisoformat(permit['expiry_date'])
    current_time = datetime.now(timezone.utc)
    
    if permit['status'] != PermitStatus.ACTIVE.value:
        return {"valid": False, "message": "Permit is not active"}
    
    if current_time > expiry_date:
        return {
            "valid": False, 
            "message": "Permit has expired",
            "expired_date": expiry_date.isoformat()
        }
    
    return {
        "valid": True,
        "permit": permit,
        "customer": permit['customer'],
        "expiry_date": expiry_date.isoformat()
    }

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Fishing Permits API", "version": "1.0.0"}

@api_router.post("/permits/purchase")
async def purchase_permits(permit_request: PermitRequest):
    """Initiate permit purchase"""
    try:
        # Validate customer data
        if not permit_request.customer.full_name or not permit_request.customer.email:
            raise HTTPException(status_code=400, detail="Customer name and email are required")
        
        if not permit_request.permit_types:
            raise HTTPException(status_code=400, detail="At least one permit type must be selected")
        
        # Calculate total amount and create permits
        permits = []
        total_amount = 0.0
        order_id = f"FP{int(datetime.now().timestamp())}"
        
        for permit_type in permit_request.permit_types:
            price = PERMIT_PRICES[permit_type]
            issue_date = datetime.now(timezone.utc)
            expiry_date = calculate_expiry_date(permit_type, issue_date)
            
            permit = FishingPermit(
                permit_type=permit_type,
                price=price,
                validity_days=PERMIT_VALIDITY[permit_type],
                description=f"{permit_type.value.title()} Fishing Permit",
                customer=permit_request.customer,
                issue_date=issue_date,
                expiry_date=expiry_date,
                order_id=order_id
            )
            
            # Generate QR code
            permit.qr_code = generate_qr_code(permit.id, permit_request.customer.full_name)
            
            permits.append(permit.dict())
            total_amount += price
        
        # Create order
        order = PermitOrder(
            order_id=order_id,
            customer=permit_request.customer,
            permits=permits,
            total_amount=total_amount
        )
        
        # Store order in database
        await store_permit_order(order)
        
        # For now, simulate payment success and activate permits immediately
        # In production, this would redirect to Przelewy24
        for permit_data in permits:
            permit_obj = FishingPermit(**permit_data)
            permit_obj.status = PermitStatus.ACTIVE
            await store_permit(permit_obj)
        
        await update_order_status(order_id, "completed")
        
        return {
            "success": True,
            "order_id": order_id,
            "total_amount": total_amount,
            "permits": permits,
            "message": "Permits purchased successfully!"
        }
        
    except Exception as e:
        logging.error(f"Permit purchase error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Purchase failed: {str(e)}")

@api_router.get("/permits/order/{order_id}")
async def get_order_permits(order_id: str):
    """Get permits for an order"""
    try:
        permits = await get_permits_by_order(order_id)
        if not permits:
            raise HTTPException(status_code=404, detail="No permits found for this order")
        
        return {
            "success": True,
            "order_id": order_id,
            "permits": permits
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get permits error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve permits")

@api_router.post("/permits/verify")
async def verify_permit(request: dict):
    """Verify permit using QR code data"""
    try:
        qr_data = request.get("qr_data", "")
        
        # Extract permit ID from QR data
        if not qr_data.startswith("PERMIT:"):
            raise HTTPException(status_code=400, detail="Invalid QR code format")
        
        parts = qr_data.split(":")
        if len(parts) < 4:
            raise HTTPException(status_code=400, detail="Invalid QR code data")
        
        permit_id = parts[1]
        verification_result = await verify_permit_qr(permit_id)
        
        return verification_result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Permit verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")

@api_router.get("/permits/types")
async def get_permit_types():
    """Get available permit types and prices"""
    return {
        "permit_types": [
            {
                "type": "daily",
                "name": "Dzienny",
                "price": PERMIT_PRICES[PermitType.DAILY],
                "validity_days": PERMIT_VALIDITY[PermitType.DAILY],
                "description": "Pozwolenie na połów ryb na jeden dzień"
            },
            {
                "type": "monthly", 
                "name": "Miesięczny",
                "price": PERMIT_PRICES[PermitType.MONTHLY],
                "validity_days": PERMIT_VALIDITY[PermitType.MONTHLY],
                "description": "Pozwolenie na połów ryb na jeden miesiąc"
            },
            {
                "type": "yearly",
                "name": "Roczny", 
                "price": PERMIT_PRICES[PermitType.YEARLY],
                "validity_days": PERMIT_VALIDITY[PermitType.YEARLY],
                "description": "Pozwolenie na połów ryb na cały rok"
            }
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()