#!/usr/bin/env python3
"""
Simple database setup for JuridiskPorten
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext

# Database configuration
DATABASE_URL = "mysql+pymysql://skyc_karo:skyc_karo@localhost/skyc_karo"

# Create engine and session
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    organization = Column(String(255))
    job_title = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class LegalPackage(Base):
    __tablename__ = "legal_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    trial_days = Column(Integer, default=14)
    features = Column(JSON)
    color_scheme = Column(String(50), default="#3E4D50")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def setup_database():
    """Create tables and add sample data"""
    print("🚀 Setting up JuridiskPorten database...")
    
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
            print("ℹ️  Database already contains data.")
            return
        
        print("🌱 Adding sample data...")
        
        # Create users
        users = [
            User(
                email="admin@juridiskporten.no",
                hashed_password=hash_password("admin123"),
                first_name="Admin",
                last_name="User",
                is_active=True,
                is_admin=True,
                organization="JuridiskPorten AS",
                job_title="administrator"
            ),
            User(
                email="demo@juridiskporten.no",
                hashed_password=hash_password("demo123"),
                first_name="Demo",
                last_name="User",
                is_active=True,
                is_admin=False,
                organization="Demo Corporation",
                job_title="saksbehandler"
            ),
            User(
                email="karoline@juridiskporten.no",
                hashed_password=hash_password("karoline123"),
                first_name="Karoline",
                last_name="Wangberg",
                is_active=True,
                is_admin=True,
                organization="Wangberg Advokatfirma",
                job_title="advokat"
            )
        ]
        
        for user in users:
            db.add(user)
        
        db.commit()
        print("👥 Created 3 users")
        
        # Create packages
        packages = [
            LegalPackage(
                title="Saksbehandlerstøtte – bevillingsforvaltning",
                description="Omfattende ressurser for saksbehandling innen bevillinger, tillatelser og konsesjoner.",
                price=2500.00,
                trial_days=14,
                features=['AI-assistert saksbehandling', 'Ferdigutfylte skjemaer og maler', 'Juridisk database', 'Direktekontakt med jurister', 'Live webinarer'],
                color_scheme="#3E4D50",
                is_active=True
            ),
            LegalPackage(
                title="Saksbehandlerstøtte – arbeidsrett & HR",
                description="Alt du trenger for å håndtere arbeidsrettslige spørsmål og HR-utfordringer.",
                price=2200.00,
                trial_days=14,
                features=['Arbeidsrettslig AI-veiledning', 'HR-prosedyrer og maler', 'Oppsigelsesrettledning', 'Konfliktløsningsverktøy', 'Kompetanseutvikling'],
                color_scheme="#A7B9BC",
                is_active=True
            ),
            LegalPackage(
                title="Saksbehandlerstøtte – generell forvaltningsrett",
                description="Generell støtte for forvaltningsrettslige oppgaver og prosedyrer.",
                price=2800.00,
                trial_days=14,
                features=['Forvaltningsrettslig AI', 'Vedtaksmaler og prosedyrer', 'Klagebehandling', 'Juridisk analyse', 'Regelverksoppdateringer'],
                color_scheme="#D3B16D",
                is_active=True
            ),
            LegalPackage(
                title="Saksbehandlerstøtte – helse og pasient/brukerrettigheter",
                description="Spesialisert støtte for helserettslige spørsmål og pasientrettigheter.",
                price=2600.00,
                trial_days=14,
                features=['Helserettslig AI-veiledning', 'Pasientrettigheter database', 'GDPR og personvern', 'Kvalitetssikring', 'Etiske retningslinjer'],
                color_scheme="#4A90A4",
                is_active=True
            )
        ]
        
        for package in packages:
            db.add(package)
        
        db.commit()
        print("📦 Created 4 legal packages")
        
        print("✅ Database setup completed successfully!")
        print("\n🔑 Demo credentials:")
        print("   Admin: admin@juridiskporten.no / admin123")
        print("   Demo:  demo@juridiskporten.no / demo123")
        print("   Karoline: karoline@juridiskporten.no / karoline123")
        
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_database()
