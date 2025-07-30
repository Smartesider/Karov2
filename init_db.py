#!/usr/bin/env python3
"""
Database initialization script for JuridiskPorten
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from main import Base, User, LegalPackage, Content, DATABASE_URL

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def init_database():
    """Initialize database with tables and seed data"""
    print("🚀 Initializing JuridiskPorten database...")
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Create all tables
    print("📋 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("ℹ️  Database already contains data. Skipping seed data creation.")
            return
        
        print("🌱 Seeding initial data...")
        
        # Create admin user
        admin_user = User(
            email="admin@juridiskporten.no",
            hashed_password=hash_password("admin123"),
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_admin=True,
            organization="JuridiskPorten AS",
            job_title="administrator"
        )
        db.add(admin_user)
        
        # Create demo user
        demo_user = User(
            email="demo@juridiskporten.no",
            hashed_password=hash_password("demo123"),
            first_name="Demo",
            last_name="User",
            is_active=True,
            is_admin=False,
            organization="Demo Corporation",
            job_title="saksbehandler"
        )
        db.add(demo_user)
        
        # Create test lawyer
        lawyer_user = User(
            email="karoline@juridiskporten.no",
            hashed_password=hash_password("karoline123"),
            first_name="Karoline",
            last_name="Wangberg",
            is_active=True,
            is_admin=True,
            organization="Wangberg Advokatfirma",
            job_title="advokat"
        )
        db.add(lawyer_user)
        
        # Commit users first to get IDs
        db.commit()
        print("👥 Created users: admin, demo, karoline")
        
        # Create legal packages
        packages = [
            {
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
                "color_scheme": "#3E4D50"
            },
            {
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
                "color_scheme": "#A7B9BC"
            },
            {
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
                "color_scheme": "#D3B16D"
            },
            {
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
                "color_scheme": "#4A90A4"
            }
        ]
        
        for pkg_data in packages:
            package = LegalPackage(
                title=pkg_data["title"],
                description=pkg_data["description"],
                price=pkg_data["price"],
                trial_days=pkg_data["trial_days"],
                features=pkg_data["features"],
                color_scheme=pkg_data["color_scheme"],
                is_active=True
            )
            db.add(package)
        
        db.commit()
        print("📦 Created 4 legal packages")
        
        print("✅ Database initialization completed successfully!")
        print("\n🔑 Demo credentials:")
        print("   Admin: admin@juridiskporten.no / admin123")
        print("   Demo:  demo@juridiskporten.no / demo123")
        print("   Karoline: karoline@juridiskporten.no / karoline123")
        print("\n🌐 Server will be available at:")
        print("   Local: http://127.0.0.1:8095")
        print("   External: https://skycode.no/karo/ (after proxy setup)")
        
    except Exception as e:
        print(f"❌ Error during database initialization: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
