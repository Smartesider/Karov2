"""
Management command to create initial data for JuridiskPorten
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import LegalPackage, ContentCategory, Content, User


class Command(BaseCommand):
    help = 'Create initial data for JuridiskPorten'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating initial data...')
        
        # Create legal packages
        packages_data = [
            {
                'package_type': 'bevillingsforvaltning',
                'name': 'Saksbehandlerstøtte – bevillingsforvaltning',
                'description': 'Ressurser for skjenking, taxi, servering m.m.',
                'detailed_description': 'Omfattende veiledning for kommunal saksbehandling innen bevillingsforvaltning.',
                'price': 1500.00,
                'color_primary': '#3E4D50',
                'sort_order': 1,
                'features': ['Skjenkebevilling', 'Taxibevilling', 'Serveringsbevilling', 'Veiledning', 'Skjemaer']
            },
            {
                'package_type': 'arbeidsrett',
                'name': 'Saksbehandlerstøtte – arbeidsrett & HR',
                'description': 'HR, ledere, personalansvar',
                'detailed_description': 'Komplett guide til arbeidsrett for HR-personell og ledere.',
                'price': 1800.00,
                'color_primary': '#A7B9BC',
                'sort_order': 2,
                'features': ['Arbeidskontrakter', 'Oppsigelser', 'Fravær', 'Varsling', 'Personalhåndbok']
            },
            {
                'package_type': 'forvaltningsrett',
                'name': 'Saksbehandlerstøtte – generell forvaltningsrett',
                'description': 'Offentlig og privat saksbehandling',
                'detailed_description': 'Forvaltningsloven, offentlighetsloven og god forvaltningsskikk.',
                'price': 2000.00,
                'color_primary': '#D3B16D',
                'sort_order': 3,
                'features': ['Forvaltningsloven', 'Offentlighetsloven', 'Partsinnsyn', 'Taushetsplikt', 'Habilitet']
            },
            {
                'package_type': 'helse',
                'name': 'Saksbehandlerstøtte – helse og pasient/brukerrettigheter',
                'description': 'Helsepersonell, pårørende, brukerstøtte',
                'detailed_description': 'Pasientrettigheter, klageadgang og dokumentasjon i helsevesenet.',
                'price': 1700.00,
                'color_primary': '#6D8B74',
                'sort_order': 4,
                'features': ['Pasientrettigheter', 'Klager', 'Tvang', 'Dokumentasjon', 'Taushetsplikt']
            }
        ]
        
        for package_data in packages_data:
            package, created = LegalPackage.objects.get_or_create(
                package_type=package_data['package_type'],
                defaults=package_data
            )
            if created:
                self.stdout.write(f'Created package: {package.name}')
            else:
                self.stdout.write(f'Package exists: {package.name}')
        
        # Create content categories
        categories_data = [
            {'name': 'Artikler', 'category_type': 'article', 'sort_order': 1},
            {'name': 'Skjemaer og maler', 'category_type': 'form', 'sort_order': 2},
            {'name': 'Spørsmål og svar', 'category_type': 'qa', 'sort_order': 3},
            {'name': 'Ressurser', 'category_type': 'resource', 'sort_order': 4},
            {'name': 'Arrangementer', 'category_type': 'event', 'sort_order': 5},
        ]
        
        for category_data in categories_data:
            category, created = ContentCategory.objects.get_or_create(
                name=category_data['name'],
                defaults=category_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Get or create a lawyer user for content authoring
        try:
            lawyer = User.objects.get(username='terje')
            lawyer.role = 'lawyer'
            lawyer.save()
        except User.DoesNotExist:
            lawyer = User.objects.create_user(
                username='lawyer',
                email='lawyer@skycode.no',
                password='temppass123',
                first_name='Legal',
                last_name='Expert',
                role='lawyer'
            )
        
        # Create sample content
        article_category = ContentCategory.objects.get(category_type='article')
        bevillingsforvaltning_package = LegalPackage.objects.get(package_type='bevillingsforvaltning')
        
        sample_content = [
            {
                'title': 'Innføring i skjenkebevilling',
                'content': '''
                <h2>Hva er skjenkebevilling?</h2>
                <p>Skjenkebevilling er en tillatelse fra kommunen som kreves for å kunne selge alkoholholdige drikker.</p>
                
                <h3>Typer skjenkebevilling</h3>
                <ul>
                    <li>Bevilling for øl og vin (alkoholholdig drikk gruppe 1 og 2)</li>
                    <li>Bevilling for brennevin (alkoholholdig drikk gruppe 3)</li>
                </ul>
                
                <h3>Krav til søker</h3>
                <p>For å få bevilling må søker oppfylle flere krav...</p>
                ''',
                'excerpt': 'Grunnleggende informasjon om skjenkebevilling og søknadsprosess.',
                'package': bevillingsforvaltning_package,
                'category': article_category,
                'author': lawyer,
                'status': 'published',
                'published_at': timezone.now(),
                'featured': True,
            }
        ]
        
        for content_data in sample_content:
            content, created = Content.objects.get_or_create(
                title=content_data['title'],
                defaults=content_data
            )
            if created:
                self.stdout.write(f'Created content: {content.title}')
        
        self.stdout.write(self.style.SUCCESS('Initial data created successfully!'))
