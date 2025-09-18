from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import hmac
import hashlib
from enum import Enum
import json
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security setup
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Special codes
CONTROLLER_CODE = "JEZIOROWIELISZEW"

# Create the main app
app = FastAPI(title="Fishing Permits API", version="2.0.0")
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    CLIENT = "client"
    CONTROLLER = "controller"
    ADMIN = "admin"

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
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    hashed_password: str
    role: UserRole = UserRole.CLIENT
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    controller_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class CustomerInfo(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    country_code: str = "PL"

class PermitRequest(BaseModel):
    permit_types: List[PermitType]

class FishingPermit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    permit_type: PermitType
    price: float
    validity_days: int
    description: str
    customer_id: str
    customer_info: CustomerInfo
    status: PermitStatus = PermitStatus.ACTIVE
    issue_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expiry_date: datetime
    qr_code: Optional[str] = None
    order_id: str

class PermitOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    customer_id: str
    customer_info: CustomerInfo
    permits: List[dict]
    total_amount: float
    currency: str = "PLN"
    status: str = "completed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VerificationLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    controller_id: str
    controller_name: str
    permit_id: str
    permit_holder: str
    verification_result: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    location: Optional[str] = "Jezioro Wieliszew"

# Configuration - Updated prices
PERMIT_PRICES = {
    PermitType.DAILY: 20.00,    # Updated from 25.00
    PermitType.MONTHLY: 60.00,  # Updated from 150.00
    PermitType.YEARLY: 300.00   # Updated from 500.00
}

PERMIT_VALIDITY = {
    PermitType.DAILY: 1,
    PermitType.MONTHLY: 30,
    PermitType.YEARLY: 365
}

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.get("is_active", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: UserRole):
    def role_checker(current_user: dict = Depends(get_current_active_user)):
        if current_user["role"] != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

def require_roles(required_roles: List[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_active_user)):
        user_role = current_user["role"]
        if user_role not in [role.value for role in required_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

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
async def get_user_by_email(email: str):
    """Get user by email"""
    user = await db.users.find_one({"email": email}, {"_id": 0})
    return user

async def get_user_by_id(user_id: str):
    """Get user by ID"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return user

async def create_user(user_data: dict):
    """Create new user"""
    # Remove any _id field before inserting
    if '_id' in user_data:
        del user_data['_id']
    result = await db.users.insert_one(user_data)
    return result

async def update_user_login(user_id: str):
    """Update user last login"""
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )

async def store_permit_order(order: PermitOrder):
    """Store permit order in database"""
    order_dict = order.dict()
    order_dict['created_at'] = order_dict['created_at'].isoformat()
    await db.permit_orders.insert_one(order_dict)

async def get_permit_order(order_id: str):
    """Get permit order from database"""
    order = await db.permit_orders.find_one({"order_id": order_id}, {"_id": 0})
    return order

async def store_permit(permit: FishingPermit):
    """Store permit in database"""
    permit_dict = permit.dict()
    permit_dict['issue_date'] = permit_dict['issue_date'].isoformat()
    permit_dict['expiry_date'] = permit_dict['expiry_date'].isoformat()
    await db.fishing_permits.insert_one(permit_dict)

async def get_permits_by_customer(customer_id: str):
    """Get all permits for a customer"""
    permits = await db.fishing_permits.find({"customer_id": customer_id}, {"_id": 0}).to_list(length=None)
    return permits

async def get_permit_by_id(permit_id: str):
    """Get permit by ID"""
    permit = await db.fishing_permits.find_one({"id": permit_id}, {"_id": 0})
    return permit

async def store_verification_log(log: VerificationLog):
    """Store verification log"""
    log_dict = log.dict()
    log_dict['timestamp'] = log_dict['timestamp'].isoformat()
    await db.verification_logs.insert_one(log_dict)

async def get_verification_logs_by_controller(controller_id: str):
    """Get verification logs for a controller"""
    logs = await db.verification_logs.find({"controller_id": controller_id}, {"_id": 0}).sort("timestamp", -1).to_list(length=50)
    return logs

async def verify_permit_qr(permit_id: str):
    """Verify permit by ID"""
    permit = await get_permit_by_id(permit_id)
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
        "customer": permit['customer_info'],
        "expiry_date": expiry_date.isoformat()
    }

# Check for first admin user
async def ensure_admin_user():
    """Ensure admin user exists"""
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD') 
    admin_name = os.environ.get('ADMIN_NAME', 'Administrator')
    
    if admin_email and admin_password:
        existing_admin = await get_user_by_email(admin_email)
        if not existing_admin:
            admin_user = {
                "id": str(uuid.uuid4()),
                "email": admin_email,
                "full_name": admin_name,
                "hashed_password": get_password_hash(admin_password),
                "role": UserRole.ADMIN.value,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await create_user(admin_user)
            logging.info(f"Admin user created: {admin_email}")

# Authentication endpoints
@api_router.post("/auth/register", response_model=Dict[str, Any])
async def register(user_data: UserCreate):
    """Register new user"""
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Determine user role
        role = UserRole.CLIENT
        if user_data.controller_code:
            if user_data.controller_code.strip() == CONTROLLER_CODE:
                role = UserRole.CONTROLLER
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid controller code"
                )
        
        # Create user
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": get_password_hash(user_data.password),
            "role": role.value,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await create_user(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        
        # Remove password from response
        user_response = {k: v for k, v in user.items() if k != "hashed_password"}
        
        # Simple response without complex user object
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "role": role.value
            },
            "message": f"Registration successful as {role.value}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login", response_model=Token)
async def login(form_data: UserLogin):
    """Login user"""
    try:
        user = await get_user_by_email(form_data.email)
        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.get("is_active", False):
            raise HTTPException(
                status_code=400,
                detail="Inactive user"
            )
        
        # Update last login
        await update_user_login(user["id"])
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["id"]}, expires_delta=access_token_expires
        )
        
        # Remove password from response
        user_response = {k: v for k, v in user.items() if k != "hashed_password"}
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user

# Permit endpoints
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

@api_router.post("/permits/purchase")
async def purchase_permits(
    permit_request: PermitRequest,
    current_user: dict = Depends(require_role(UserRole.CLIENT))
):
    """Purchase permits - only for clients"""
    try:
        if not permit_request.permit_types:
            raise HTTPException(status_code=400, detail="At least one permit type must be selected")
        
        # Calculate total amount and create permits
        permits = []
        total_amount = 0.0
        order_id = f"FP{int(datetime.now().timestamp())}"
        
        # Get customer info from user
        customer_info = CustomerInfo(
            full_name=current_user["full_name"],
            email=current_user["email"]
        )
        
        for permit_type in permit_request.permit_types:
            price = PERMIT_PRICES[permit_type]
            issue_date = datetime.now(timezone.utc)
            expiry_date = calculate_expiry_date(permit_type, issue_date)
            
            permit = FishingPermit(
                permit_type=permit_type,
                price=price,
                validity_days=PERMIT_VALIDITY[permit_type],
                description=f"{permit_type.value.title()} Fishing Permit",
                customer_id=current_user["id"],
                customer_info=customer_info,
                issue_date=issue_date,
                expiry_date=expiry_date,
                order_id=order_id
            )
            
            # Generate QR code
            permit.qr_code = generate_qr_code(permit.id, current_user["full_name"])
            
            permits.append(permit.dict())
            total_amount += price
        
        # Create order
        order = PermitOrder(
            order_id=order_id,
            customer_id=current_user["id"],
            customer_info=customer_info,
            permits=permits,
            total_amount=total_amount
        )
        
        # Store order and permits in database
        await store_permit_order(order)
        
        for permit_data in permits:
            permit_obj = FishingPermit(**permit_data)
            await store_permit(permit_obj)
        
        return {
            "success": True,
            "order_id": order_id,
            "total_amount": total_amount,
            "permits": permits,
            "message": "Permits purchased successfully!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Permit purchase error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Purchase failed: {str(e)}")

@api_router.get("/permits/my-permits")
async def get_my_permits(current_user: dict = Depends(require_role(UserRole.CLIENT))):
    """Get permits for current user"""
    try:
        permits = await get_permits_by_customer(current_user["id"])
        return {
            "success": True,
            "permits": permits
        }
    except Exception as e:
        logging.error(f"Get permits error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve permits")

@api_router.post("/permits/verify")
async def verify_permit(
    request: dict,
    current_user: dict = Depends(require_role(UserRole.CONTROLLER))
):
    """Verify permit using QR code data - only for controllers"""
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
        
        # Log verification
        log = VerificationLog(
            controller_id=current_user["id"],
            controller_name=current_user["full_name"],
            permit_id=permit_id,
            permit_holder=parts[3] if len(parts) > 3 else "Unknown",
            verification_result=verification_result["valid"]
        )
        await store_verification_log(log)
        
        return verification_result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Permit verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")

@api_router.get("/controller/verification-history")
async def get_verification_history(
    current_user: dict = Depends(require_role(UserRole.CONTROLLER))
):
    """Get verification history for controller"""
    try:
        logs = await get_verification_logs_by_controller(current_user["id"])
        return {
            "success": True,
            "logs": logs
        }
    except Exception as e:
        logging.error(f"Get verification history error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve verification history")

@api_router.get("/admin/stats")
async def get_admin_stats(current_user: dict = Depends(require_role(UserRole.ADMIN))):
    """Get admin statistics"""
    try:
        # Count users by role
        users_stats = await db.users.aggregate([
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ]).to_list(length=None)
        
        # Count permits by type
        permits_stats = await db.fishing_permits.aggregate([
            {"$group": {"_id": "$permit_type", "count": {"$sum": 1}, "total_revenue": {"$sum": "$price"}}}
        ]).to_list(length=None)
        
        # Recent verifications
        recent_verifications = await db.verification_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(10).to_list(length=10)
        
        return {
            "success": True,
            "users_by_role": {stat["_id"]: stat["count"] for stat in users_stats},
            "permits_by_type": {stat["_id"]: {"count": stat["count"], "revenue": stat["total_revenue"]} for stat in permits_stats},
            "recent_verifications": recent_verifications
        }
    except Exception as e:
        logging.error(f"Get admin stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin statistics")

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Fishing Permits API v2.0", "version": "2.0.0"}

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

@app.on_event("startup")
async def startup_event():
    """Initialize app on startup"""
    await ensure_admin_user()
    logger.info("Fishing Permits API v2.0 started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()