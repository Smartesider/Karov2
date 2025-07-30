#!/usr/bin/env python3
"""
JuridiskPorten - FastAPI Backend
Minimal version for demonstration
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="JuridiskPorten",
    description="Modern legal services platform",
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

# Templates
templates = Jinja2Templates(directory="templates")

# Serve static files if directory exists
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

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
    uvicorn.run(app, host="0.0.0.0", port=8095)
