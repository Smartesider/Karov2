"""
Phase 2 content creation command
Creates sample content with rich text, categories, and bookmarks for testing
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import (
    LegalPackage, Content, ContentCategory, 
    ContentBookmark, UserProgress
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create Phase 2 sample content for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating Phase 2 sample content...')

        # Get or create test lawyer
        lawyer, created = User.objects.get_or_create(
            email='lawyer@juridiskporten.no',
            defaults={
                'username': 'lawyer_test',
                'first_name': 'Legal',
                'last_name': 'Expert',
                'role': 'lawyer',
                'is_verified': True
            }
        )
        if created:
            lawyer.set_password('testpass123')
            lawyer.save()

        # Get packages
        packages = LegalPackage.objects.all()
        
        if not packages:
            self.stdout.write(self.style.ERROR('No packages found. Run initial_data command first.'))
            return

        # Create additional content categories
        categories = [
            ('article', 'Legal Articles', 'In-depth legal analysis and guidance'),
            ('form', 'Legal Forms', 'Templates and forms for legal processes'),
            ('checklist', 'Checklists', 'Step-by-step verification lists'),
            ('qa', 'Q&A', 'Frequently asked questions and answers'),
            ('guide', 'Guides', 'Comprehensive how-to guides'),
        ]

        created_categories = {}
        for cat_type, name, description in categories:
            category, created = ContentCategory.objects.get_or_create(
                name=name,
                defaults={
                    'category_type': cat_type,
                    'description': description,
                    'is_active': True
                }
            )
            created_categories[cat_type] = category

        # Sample content for each package
        content_data = {
            'bevillingsforvaltning': [
                {
                    'title': 'Søknad om skjenkebevilling - Fullstendig guide',
                    'content_type': 'guide',
                    'content': '''<h2>Innledning</h2>
                    <p>Søknad om skjenkebevilling kan være en kompleks prosess som krever grundig planlegging og forståelse av gjeldende regelverk. Denne guiden gir deg en omfattende oversikt over prosessen.</p>
                    
                    <h3>Krav til søkeren</h3>
                    <ul>
                        <li>Minimum 20 år gammel</li>
                        <li>Ikke være umyndiggjort</li>
                        <li>Ha tilfredsstillende vandel</li>
                        <li>Ikke ha betydelig forfalent gjeld til det offentlige</li>
                    </ul>
                    
                    <h3>Dokumentasjon som må vedlegges</h3>
                    <p>For å sikre en smidig søknadsprosess, må følgende dokumenter legges ved:</p>
                    
                    <h4>Personlige dokumenter</h4>
                    <ul>
                        <li>Kopi av gyldig legitimasjon</li>
                        <li>Politiattest (ikke eldre enn 3 måneder)</li>
                        <li>Skatteoppgjør for siste 2 år</li>
                    </ul>
                    
                    <h4>Virksomhetsdokumenter</h4>
                    <ul>
                        <li>Foretaksregisterutskrift</li>
                        <li>Firmaattest</li>
                        <li>Leiekontrakt eller eiendomsbevis</li>
                        <li>Tegninger av lokalene</li>
                    </ul>''',
                    'excerpt': 'Komplett guide for søknad om skjenkebevilling med alle nødvendige dokumenter og krav.',
                    'priority': 100,
                    'featured': True
                },
                {
                    'title': 'Sjekkliste: Før du søker om taxiløyve',
                    'content_type': 'checklist',
                    'content': '''<h2>Obligatoriske krav</h2>
                    <h3>☐ Alderskrav</h3>
                    <p>Du må være fylt 21 år</p>
                    
                    <h3>☐ Helsekrav</h3>
                    <p>Gyldig helseattest fra lege (ikke eldre enn 6 måneder)</p>
                    
                    <h3>☐ Førerrett</h3>
                    <p>Gyldig førerkort klasse B i minimum 3 år</p>
                    
                    <h3>☐ Vandelskrav</h3>
                    <p>Politiattest som dokumenterer tilfredsstillende vandel</p>
                    
                    <h2>Dokumentasjon</h2>
                    <h3>☐ Søknadsskjema</h3>
                    <p>Utfylt og signert søknadsskjema</p>
                    
                    <h3>☐ Legitimasjon</h3>
                    <p>Kopi av gyldig legitimasjon</p>
                    
                    <h3>☐ Gebyr</h3>
                    <p>Betalt søknadsgebyr (varierer mellom kommuner)</p>''',
                    'excerpt': 'Praktisk sjekkliste for alle som skal søke om taxiløyve.',
                    'priority': 90
                },
                {
                    'title': 'Vanlige feil i bevillingssøknader',
                    'content_type': 'article',
                    'content': '''<h2>De mest vanlige feilene</h2>
                    
                    <h3>1. Ufullstendig dokumentasjon</h3>
                    <p>Den vanligste feilen er å sende inn søknaden uten all nødvendig dokumentasjon. Dette fører til forsinkelser og kan i verste fall føre til avslag.</p>
                    
                    <h3>2. Utdaterte dokumenter</h3>
                    <p>Mange dokumenter har begrenset gyldighet. Pass på at politiattester, helseattester og andre tidssensitive dokumenter er innenfor gyldig periode.</p>
                    
                    <h3>3. Feil utfylling av skjemaer</h3>
                    <p>Kontroller at alle felter er korrekt utfylt og at all informasjon stemmer overens mellom ulike dokumenter.</p>
                    
                    <h3>4. Manglende signatur</h3>
                    <p>Alle søknader må være signert av riktig person med signaturrett.</p>''',
                    'excerpt': 'Lær om de vanligste feilene i bevillingssøknader og hvordan du unngår dem.',
                    'priority': 80
                },
            ],
            'arbeidsrett': [
                {
                    'title': 'Ansettelseskontrakter: Juridiske krav og beste praksis',
                    'content_type': 'guide',
                    'content': '''<h2>Lovpålagte krav til ansettelseskontrakter</h2>
                    
                    <p>Alle arbeidsavtaler må inneholde visse minimumskrav i henhold til arbeidsmiljøloven. Her er en oversikt over de viktigste elementene.</p>
                    
                    <h3>Obligatoriske opplysninger</h3>
                    <ul>
                        <li>Navn og adresse til partene</li>
                        <li>Arbeidsstedets adresse</li>
                        <li>Stillingstittel eller kort beskrivelse av arbeidet</li>
                        <li>Tidspunkt for arbeidsforholdets begynnelse</li>
                        <li>Ved midlertidig ansettelse: forventet varighet</li>
                        <li>Oppsigelsesfrister</li>
                        <li>Lønn og lønnsbestemmelser</li>
                        <li>Avtalt arbeidstid</li>
                        <li>Ferie- og feriepengebestemmelser</li>
                    </ul>
                    
                    <h3>Gode råd for utforming</h3>
                    <p>En god ansettelseskontrakt bør være klar og tydelig. Unngå juridisk sjargong som kan skape forvirring.</p>''',
                    'excerpt': 'Alt du trenger å vite om juridiske krav til ansettelseskontrakter.',
                    'priority': 100,
                    'featured': True
                },
                {
                    'title': 'Oppsigelse av arbeidsforhold - Prosedyrer og fallgruver',
                    'content_type': 'article',
                    'content': '''<h2>Krav til saklig oppsigelse</h2>
                    
                    <p>Oppsigelse av arbeidsforhold må være saklig begrunnet og følge korrekt prosedyre. Manglende overholdelse kan føre til erstatningsansvar.</p>
                    
                    <h3>Saklige oppsigelsesgrunn</h3>
                    <p>Oppsigelse må være begrunnet i:</p>
                    <ul>
                        <li>Arbeidstakerens forhold</li>
                        <li>Bedriftens forhold</li>
                        <li>Andre saklige årsaker</li>
                    </ul>
                    
                    <h3>Prosedyrekrav</h3>
                    <ol>
                        <li>Drøftingsplikt med tillitsvalgte</li>
                        <li>Samtale med arbeidstaker</li>
                        <li>Skriftlig oppsigelse med begrunnelse</li>
                        <li>Overholdelse av oppsigelsesfrister</li>
                    </ol>''',
                    'excerpt': 'Juridisk veiledning for korrekt håndtering av oppsigelsesprosesser.',
                    'priority': 90
                },
            ]
        }

        # Create content for each package
        total_created = 0
        for package in packages:
            if package.package_type in content_data:
                for content_item in content_data[package.package_type]:
                    content, created = Content.objects.get_or_create(
                        title=content_item['title'],
                        package=package,
                        defaults={
                            'content_type': content_item['content_type'],
                            'content': content_item['content'],
                            'excerpt': content_item['excerpt'],
                            'author': lawyer,
                            'category': created_categories[content_item['content_type']],
                            'status': 'published',
                            'published_at': timezone.now(),
                            'priority': content_item.get('priority', 50),
                            'featured': content_item.get('featured', False),
                            'meta_description': content_item['excerpt'][:150],
                        }
                    )
                    if created:
                        total_created += 1
                        self.stdout.write(f'✓ Created: {content.title}')

        # Create some sample bookmarks and progress
        if User.objects.filter(role='client').exists():
            client = User.objects.filter(role='client').first()
            published_content = Content.objects.filter(status='published')[:5]
            
            for content in published_content:
                # Create some bookmarks
                ContentBookmark.objects.get_or_create(
                    user=client,
                    content=content,
                    defaults={'notes': f'Bookmarked for later review: {content.title}'}
                )
                
                # Create some progress records
                UserProgress.objects.get_or_create(
                    user=client,
                    content=content,
                    defaults={
                        'status': 'in_progress',
                        'started_at': timezone.now()
                    }
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {total_created} content items for Phase 2!')
        )
        self.stdout.write('Phase 2 sample data is ready for testing.')
