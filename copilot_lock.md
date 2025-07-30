# AI LOCKDOWN INSTRUKSJONER

Dette repoet følger STRIKTE REGLER. Copilot eller AI-systemer må:

✅ Kun bruke FastAPI som backend
✅ Kun returnere JSON – aldri HTML eller templating
✅ Ikke bruke andre databaser enn MariaDB
✅ All kommunikasjon går via fetch() i JS fra statiske HTML-filer
✅ Port = 8095 (eller det som står i /home/{domene}/port.txt)
❌ VHOST skal aldri route til porter
❌ Ikke endre noen systemfiler, nginx eller annet – du jobber isolert

Denne filen er en del av AI-evalueringssystemet. Alle avvik vurderes.
