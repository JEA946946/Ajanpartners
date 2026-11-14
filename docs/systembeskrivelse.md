# Systembeskrivelse – Ajan Partners Bogføring

Ajan Partners Bogføring er et digitalt standardbogføringssystem. Revisorhuset Ajan Partners stiller det gratis til rådighed for sine kunder. Beskrivelsen er til Erhvervsstyrelsens anmeldelse og til kunder, revisorer og myndigheder, der skal vide, hvordan systemet opbevarer, sikrer og udleverer regnskabsmateriale.

## 1. Opbygning

| Lag | Teknologi | Rolle |
|---|---|---|
| Webklient | React 18, MUI 5 (browser) | Brugerflade for kunder og revisorhusets medarbejdere |
| API | Django 5.2 + Django REST Framework, gunicorn | Al forretningslogik, adgangskontrol og logning |
| Database | PostgreSQL 16 med django-tenants | Ét skema pr. kunde; et fælles public-skema |
| Filer | Lokalt filsystem pr. kunde (`MEDIA_ROOT/<skema>/`) | Bilag (originalfiler) |
| Worker | Samme image, `infra/worker.sh` | Backup, restore-test, bankdata, påmindelser, opbevaringsjob |
| Backup | `infra/backup.sh`, age/gpg, S3-kompatibel lagring i EU | Krypteret kopi hos tredjepart |

### Adskillelse af kunder
Hver kunde har sit eget Postgres-skema med hele bogføringen: kontoplan, posteringer, bilag, fakturaer, løn og audit-log. Skemaet vælges for hvert kald ud fra headeren `X-Client`, men først efter at systemet har tjekket, at brugeren har adgang til netop den kunde (`backend/tenancy/middleware.py`, `access.py`). Det fælles public-skema indeholder kun brugere, kunder, pakker, adgangssamtykker, revisorhusets opgaver og revisorhusets log.

### Brugere og roller
- **Kundens brugere**: administrator, bogholder og læser (`ClientMembership`). Administratoren styrer brugere, revisoradgang og eksport.
- **Revisorhusets medarbejdere**: partner, revisor, bogholder og assistent (`FirmStaff`). De kommer kun ind i en kundes bøger, hvis kunden har givet samtykke (`AccessGrant`). Samtykket har et omfang (læse, bogføre eller fuld), kan tidsbegrænses og kan tilbagekaldes med det samme. Bogholdere og assistenter ser kun de kunder, de er tildelt.
- **Pakker** (Mini, Standard, Pro) styrer, hvilke funktioner kundens egne brugere har. Revisorhuset er ikke begrænset af pakken.

## 2. Registrering og opbevaring (Bogføringsloven)

| Krav | Sådan opfyldes det |
|---|---|
| Registreringer kan ikke ændres eller slettes efter bogføring | Posteringer valideres og nummereres fortløbende pr. journal og år ved periodeafslutning. Derefter afviser databasen ændringer og sletning (triggere). Rettelser laves som tilbageføring. |
| Lukkede perioder | Lukkede måneder og regnskabsår afviser nye registreringer. Momsperioder låses efter angivelse. |
| Bilag | Hvert bilag gemmes som originalfil med SHA-256 og størrelse. Et bilag, der hører til en valideret postering, kan ikke slettes eller flyttes. |
| Audit-log | Hver kunde har en log, der kun kan tilføjes til og er hash-kædet. Den kan kontrolleres med `/audit-log/verify`. Revisorhusets handlinger er mærket og logges desuden i revisorhusets egen log, både læsning (én post pr. medarbejder, kunde og time) og skrivning. |
| Opbevaring i 5 år | Kunder slettes aldrig automatisk. Ved ophør arkiveres de (read-only), og `retain_until` sættes. Jobbet `retention_report` opretter en opgave til en partner, når perioden er udløbet. Sletning sker manuelt efter partnerens godkendelse. |
| Backup hos tredjepart | Hver nat kl. 02:30 dumpes hvert skema og dets bilag, krypteres og sendes til EU-lagring. Daglige kopier gemmes i 40 dage og månedlige for altid. Den 1. i hver måned gendannes backuppen i en testdatabase. |
| Udlevering | "Eksportér alt": SAF-T Financial DK 2.1 pr. regnskabsår, saldobalancer, alle bilag med SHA-256, audit-log og et manifest. Kan hentes af kundens administrator og af en partner/revisor med samtykke, og af en partner, når kunden er arkiveret. |
| E-faktura | OIOUBL 2.1 og Peppol BIS 3.0, både at sende og modtage (`backend/einvoice/`). |
| Bankafstemning | Bankimport, bankkobling via open banking og afstemning med krav om afsluttet afstemning ved månedsafslutning. |

## 3. Sikkerhed
- Login med brugernavn/e-mail og adgangskode. Djangos validatorer kræver mindst 10 tegn, ingen almindelige eller rent numeriske koder, og koden må ikke ligne brugernavnet. Login er begrænset til 10 forsøg pr. minut pr. IP.
- To-faktor-login (TOTP) med gendannelseskoder. Det er **obligatorisk for revisorhusets medarbejdere** og frivilligt for kunderne. Hemmeligheden er krypteret, og en kode kan kun bruges én gang.
- JWT med 12 timers levetid. Al trafik går over TLS via reverse proxy.
- CPR-numre og MFA-hemmeligheder er krypteret i databasen med en nøgle, der ligger uden for database og backup (`FIELD_ENCRYPTION_KEY`).
- Containerne kører som ikke-root. Hemmeligheder kommer fra miljøet (`.env`) og ligger aldrig i koden.

## 4. Dataflow (eksempler)
1. **Faktura**: kunden opretter en faktura → bogføres i SALG-journalen → kan sendes som e-faktura via access point → indbetalingen kommer fra banken (import/bankkobling) → matches → udlignes.
2. **Bilag fra revisorhuset**: en medarbejder opretter en bilagsforespørgsel → kunden svarer og vedhæfter bilaget i "Beskeder fra revisor" → medarbejderen bogfører i kundens bøger med kundens samtykke. Alt bliver logget.
3. **Moms**: momsangivelsen dannes ud fra bogføringen for kundens momsperiode → afstemmes mod saldobalancen → angives (via Skats system-til-system, når aftalen er på plads, ellers i TastSelv) → perioden låses og afregningen bogføres.

## 5. Drift
- Installation: `docker-compose.yml` (postgres, django, worker) og `.env` ud fra `.env.example`. Første gang: `bootstrap_firm` opretter revisorhuset og den første partner.
- Planlagte job (`infra/worker.sh`): backup 02:30, restore-test den 1. i måneden, bankdata 06:00, påmindelse om bankkobling dagligt og opbevaringsjob månedligt.
- Opdatering: push til `main` → CI (tests, lint, build) → deploy. Migrationer køres med `migrate_schemas` for alle kunder.

## 6. Ansvar
| Område | Ansvarlig |
|---|---|
| Drift, backup, sikkerhedsopdateringer | Ajan Partners (systemleverandør) |
| Korrekt bogføring og bilag | Kunden (bogføringspligtig), med hjælp fra revisorhuset efter aftale |
| Adgang for revisorhuset | Kunden (samtykke i systemet) |
| Udlevering ved ophør, til kurator og myndigheder | Ajan Partners, se `docs/udlevering.md` |
