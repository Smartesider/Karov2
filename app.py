#!/usr/bin/env python3
"""
JuridiskPorten - FastAPI Backend
🧷 Kun MariaDB skal brukes – ingen andre drivere!
🛑 Ingen templating! HTML-servering skjer via statiske filer – kun API med JSON
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import hashlib
from typing import Optional, Dict, Any

# 🧷 Kun MariaDB skal brukes – ingen andre drivere!
# Ikke importer sqlite3, psycopg2, asyncpg eller annet

# Create FastAPI app
app = FastAPI(
    title="JuridiskPorten",
    description="Modern legal services platform - JSON API only",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "juridisk-portal-secret-key-change-in-production"
ALGORITHM = "HS256"

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Mock user database (replace with MariaDB later)
USERS_DB = {
    "karoline": {
        "id": 1,
        "username": "karoline",
        "password_hash": hashlib.sha256("VestbyOgKjenn".encode()).hexdigest(),
        "role": "admin",
        "full_name": "Karoline"
    },
    "testuser": {
        "id": 2,
        "username": "testuser",
        "password_hash": hashlib.sha256("test123".encode()).hexdigest(),
        "role": "user",
        "full_name": "Test Bruker"
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Authentication endpoints
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Check if user exists
    user_data = USERS_DB.get(request.username)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify password
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    if password_hash != user_data["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user_data["username"]})
    
    # Return response
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=user_data["id"],
            username=user_data["username"],
            role=user_data["role"],
            full_name=user_data["full_name"]
        )
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(username: str = Depends(verify_token)):
    user_data = USERS_DB.get(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user_data["id"],
        username=user_data["username"],
        role=user_data["role"],
        full_name=user_data["full_name"]
    )

@app.post("/api/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

# Admin endpoints
@app.get("/api/admin/stats")
async def get_admin_stats(username: str = Depends(verify_token)):
    user_data = USERS_DB.get(username)
    if not user_data or user_data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "total_users": len(USERS_DB),
        "total_packages": 4,
        "active_subscriptions": 15,
        "monthly_revenue": 35000
    }

# API Mock endpoints
@app.get("/api/packages")
async def get_packages():
    return [
        {
            "id": 1,
            "title": "Saksbehandlerstøtte – bevillingsforvaltning",
            "description": "Omfattende ressurser for saksbehandling innen bevillinger, tillatelser og konsesjoner.",
            "price": 2500.00,
            "trial_days": 14,
            "features": [
                "AI-assistert saksbehandling",
                "Ferdigutfylte skjemaer og maler",
                "Juridisk database med precedenser",
                "Direktekontakt med ekspertjurister",
                "Live webinarer og kurs"
            ],
            "color_scheme": "#3E4D50",
            "is_active": True
        },
        {
            "id": 2,
            "title": "Saksbehandlerstøtte – arbeidsrett & HR",
            "description": "Alt du trenger for å håndtere arbeidsrettslige spørsmål og HR-utfordringer.",
            "price": 2200.00,
            "trial_days": 14,
            "features": [
                "Arbeidsrettslig AI-veiledning",
                "HR-prosedyrer og maler",
                "Oppsigelsesrettledning",
                "Konfliktløsningsverktøy",
                "Kompetanseutvikling"
            ],
            "color_scheme": "#A7B9BC",
            "is_active": True
        },
        {
            "id": 3,
            "title": "Saksbehandlerstøtte – generell forvaltningsrett",
            "description": "Generell støtte for forvaltningsrettslige oppgaver og prosedyrer.",
            "price": 2800.00,
            "trial_days": 14,
            "features": [
                "Forvaltningsrettslig AI",
                "Vedtaksmaler og prosedyrer",
                "Klagebehandling",
                "Juridisk analyse",
                "Regelverksoppdateringer"
            ],
            "color_scheme": "#D3B16D",
            "is_active": True
        },
        {
            "id": 4,
            "title": "Saksbehandlerstøtte – helse og pasient/brukerrettigheter",
            "description": "Spesialisert støtte for helserettslige spørsmål og pasientrettigheter.",
            "price": 2600.00,
            "trial_days": 14,
            "features": [
                "Helserettslig AI-veiledning",
                "Pasientrettigheter database",
                "GDPR og personvern",
                "Kvalitetssikring",
                "Etiske retningslinjer"
            ],
            "color_scheme": "#4A90A4",
            "is_active": True
        }
    ]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "JuridiskPorten is running!"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting JuridiskPorten...")
    print("🌐 Will be available at:")
    print("   Local: http://127.0.0.1:8095")
    print("   External: https://skycode.no/karo/ (after proxy setup)")
    print("🔐 Test credentials:")
    print("   Admin: karoline / VestbyOgKjenn")
    print("   User: testuser / test123")
    uvicorn.run(app, host="0.0.0.0", port=8095)
