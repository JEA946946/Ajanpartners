# Compliance-tjekliste: Bogføringsloven og digitale standardbogføringssystemer

Grundlag: bogføringsloven (lov nr. 700 af 24. maj 2022) og bekendtgørelsen om krav til
digitale standardbogføringssystemer (BEK nr. 97 af 26. januar 2023). Erhvervsstyrelsen
udgiver også vejledning og standardfilformater (SAF-T og standardkontoplanen). Paragrafhenvisninger
skal tjekkes mod den gældende konsoliderede tekst, før systemet anmeldes.

Status: **Opfyldt** = kode og test findes · **Delvist** = kode findes, men noget mangler · **Mangler** = ikke lavet.
Stier er relative til repo-roden.

| # | Krav | Status |
|---|------|--------|
| 1 | Systemet er registreret hos Erhvervsstyrelsen | Mangler (anmeldelse) |
| 2 | Registrering af transaktioner, bilag og sporbarhed | Opfyldt |
| 3 | Opbevaring af bilag og regnskabsmateriale i 5 år | Opfyldt |
| 4 | Automatisk backup hos en tredjepart | Delvist (drift) |
| 5 | E-faktura: sende og modtage | Opfyldt i koden (access point-aftale mangler) |
| 6 | Bankafstemning og automatisk bankdata | Opfyldt i koden (AIS-aftale mangler) |
| 7 | Adgang for myndigheder og eksport (SAF-T) | Opfyldt |
| 8 | Opbevaring efter opsigelse eller ophør | Opfyldt i koden (escrow og kontrakt mangler) |
| 9 | Sikkerhed og adgangsstyring | Opfyldt i koden (kryptering af disk og driftsprocesser mangler) |
| 10 | Logning | Opfyldt |
| 11 | Moms og indberetninger til Skat | Delvist |
| 12 | Systemdokumentation og brugervejledning | Opfyldt (skal holdes ajour) |

---

## 1. Registrering hos Erhvervsstyrelsen
- **Krav:** Udbydere af digitale standardbogføringssystemer skal anmelde systemet til
  Erhvervsstyrelsen, og systemet skal opfylde bekendtgørelsens krav.
- **I koden:** Ingen kode. Denne tjekliste er grundlaget for anmeldelsen.
- **Mangler:** Anmeldelse på virk.dk, systembeskrivelse (se punkt 12), og at
  rigtige adaptere er slået til for e-faktura, backup og bank (punkt 4–6).

## 2. Registrering af transaktioner, bilag og sporbarhed
- **Krav:** Alle transaktioner registreres løbende og med kontrolspor. Hver postering skal
  kunne føres tilbage til sit bilag. Rettelser må ikke slette det oprindelige.
- **I koden:**
  - Kladde → bogført → valideret, fortløbende nummer pr. journal og år: `backend/journals/models.py`,
    `backend/journals/numbering.py`, `backend/journals/closing.py`.
  - Validerede posteringer er låst af DB-triggere (`backend/journals/migrations/0013_*`, `0015_*`,
    `0017_*`). Rettelser sker ved tilbageføring (`reversal_of`).
  - Lukkede perioder og regnskabsår afviser alt: `backend/journals/periods.py`.
  - Bilag med SHA-256 og fingeraftryk: `backend/core/models.py` (`Document`), `backend/core/uploads.py`.
  - E-fakturaer gemmes uændret med SHA-256: `backend/einvoice/models.py`. Når en modtaget
    e-faktura bliver til en regning, gemmes XML'en som bilag (`core.Document` med `bill`, SHA-256
    og størrelse som ved upload): `backend/einvoice/services.py: attach_xml`. Testen tjekker, at
    bilagets hash er den samme som e-fakturaens.
- **Mangler:** Ingen i koden. `core/uploads.validate_upload` tillader ikke `.xml`, så
  e-fakturabilaget oprettes direkte (det kommer fra access point'et, ikke fra en bruger).

## 3. Opbevaring af bilag og regnskabsmateriale i 5 år
- **Krav:** Regnskabsmateriale, også bilag, opbevares i 5 år fra udgangen af regnskabsåret.
  Det skal være sikret mod ændring og tab, og det skal kunne fremfindes.
- **I koden:**
  - Kunder slettes aldrig, de arkiveres: `tenancy/services.py: archive_client` (read-only,
    `retain_until`, `auto_drop_schema = False`). Middleware'en afviser skrivning:
    `backend/tenancy/middleware.py`.
  - Bilag gemmes pr. skema (`MEDIA_ROOT/<skema>/`) og kommer med i backuppen (punkt 4).
- **Lukket:**
  - `manage.py retention_report` (månedligt i `infra/worker.sh`) opretter en intern opgave til en
    partner, når en arkiveret kundes opbevaringsperiode er udløbet. Intet slettes automatisk.
  - "Eksportér alt" (`tenancy/export.py`): SAF-T 2.1 pr. regnskabsår, saldobalancer, alle bilag
    med SHA-256, audit-log med kædekontrol og MANIFEST.txt. Kunden: `GET /api/v1/export-all`
    (Indstillinger → Eksport af data). Admin-portalen: `GET /api/firm/clients/<slug>/export-all`.

## 4. Automatisk backup hos en tredjepart
- **Krav:** Systemet tager automatisk backup af regnskabsmaterialet hos en tredjepart, og
  den kan gendannes.
- **I koden:**
  - `infra/backup.sh backup`: `pg_dump` pr. skema (hver kunde for sig), bilag pr. skema,
    roller, SHA256SUMS og et manifest. Alt krypteres med age eller gpg (kun den offentlige
    nøgle ligger på serveren) og uploades til S3-kompatibel lagring (aws-cli, endpoint/region
    fra env).
  - Opbevaring: daglige kopier i 40 dage, månedlige kopier gemmes for altid (`monthly/`).
  - `infra/backup.sh restore-test`: henter den seneste backup, tjekker checksum, dekrypterer og
    gendanner den i en midlertidig database, og kontrollerer antallet af skemaer og tabeller.
  - Worker-containeren kører backup kl. 02:30 og restore-test den 1. i måneden
    (`infra/worker.sh`, `docker-compose.yml`).
- **Mangler (drift):**
  - En aftale med en lagerudbyder i EU (databehandleraftale), en bucket med versionering eller
    object lock, nøgler i `.env`, og den private age-nøgle opbevaret offline hos to personer.
  - Overvågning af `BACKUP_HEALTHCHECK_URL` (alarm, hvis der ikke er pinget inden for 26 timer).
  - Dokumenteret gendannelsesprocedure og en log over restore-tests.

## 5. E-faktura: sende og modtage
- **Krav:** Systemet kan sende og modtage elektroniske fakturaer i et standardformat
  (OIOUBL/Peppol BIS) og tilknytte dem bogføringen.
- **I koden:** `backend/einvoice/`
  - Dannelse af Peppol BIS Billing 3.0 og OIOUBL 2.1 (Invoice/CreditNote): `ubl.py`.
  - Læsning af indgående UBL med defusedxml (ingen entiteter) og forslag til leverandør, konto
    og momskode via CVR/GLN: `parse.py`.
  - Indbakke → regning (kladde) med audit-log: `services.py`, endpoints `einvoice/send/<id>`,
    `einvoice/inbox`, `einvoice/inbox/<id>/to-bill`. Pakkerne styrer adgangen via `einvoice_send` og `einvoice_receive`.
  - Access point-adapter: mock (default) og stubs for NemHandel, Storecove og Pagero: `access_point.py`.
  - Frontend: `frontend/src/pages/EInvoiceInbox.tsx`, `frontend/src/components/EInvoiceSendButton.tsx`.
  - Officiel validering i testene og CI: `backend/einvoice/tests_schematron.py`. Dannede
    fakturaer og kreditnotaer valideres mod UBL 2.1 XSD (OASIS), CEN EN 16931-schematron
    (validation-1.3.17), Peppol BIS 3.0-schematron (3.0.22) og Erhvervsstyrelsens OIOUBL 2.1-schematron
    (v1.17.2). Alle er grønne. Artefakter, kilder og licenser: `backend/einvoice/validation/SOURCES.txt`.
  - OIOUBL 2.1 dannes efter de danske kodelister (CustomizationID `OIOUBL-2.1`, ProfileID med
    schemeAgencyID 320, `DK:CVR`/`GLN`, StructuredDK-adresser, TaxScheme 63) og er verificeret mod
    schematron. GLN tjekkes for GS1-kontrolciffer.
- **Mangler:**
  - En aftale med et access point (eller NemHandel-tilslutning med OCES3-certifikat) og
    implementering af den valgte adapter, inkl. webhook/polling for indgående dokumenter.
  - Applikationssvar (Invoice Response/MLR) og afvisning tilbage til afsenderen.
  - Licensen for Peppol-schematron'en skal afklares, før kildekoden udgives offentligt (se SOURCES.txt).

## 6. Bankafstemning og automatisk bankdata
- **Krav:** Systemet understøtter registrering og afstemning af betalinger, gerne automatisk
  via bankdata.
- **I koden:**
  - Bankimport (CSV/Excel), dublet-kontrol og parkering på "bank til afstemning":
    `backend/journals/views.py` (`bank_statement_*`). Afstemning: `core.models.BankReconciliation`.
  - Open banking (PSD2/AIS): `backend/integrations/bank_feeds.py` med mock og stubs (Aiia,
    Tink, Enable Banking). Samtykke i 180 dage (`integrations/models.py`). Daglig hentning
    via `manage.py fetch_bank_feeds`, som bruger journals' bankimport, så kontrollerne er de
    samme. Kundens endpoints: `bank-feeds/...`, som pakkerne styrer via `bank_feed`.
  - UI: `frontend/src/pages/BankFeeds.tsx` (Bank → Bankkobling). Kobl bank på, se status,
    hent nu, forny samtykke og afbryd. Siden viser et banner, når samtykket udløber om under 14 dage.
  - Påmindelse: `manage.py bank_feed_reminders` opretter én opgave til kunden (`firm.FirmTask`,
    `kind="opgave"`, synlig for kunden) pr. kobling og samtykkeperiode. Den kører dagligt i
    `infra/worker.sh`.
- **Mangler:**
  - En aftale med en licenseret AIS-udbyder og implementering af adapteren (redirect-flow
    for samtykket; UI'et følger allerede `authorization_url`).

## 7. Adgang for myndigheder og eksport (SAF-T)
- **Krav:** Regnskabsmaterialet kan udleveres til myndighederne digitalt i et struktureret
  format (SAF-T Financial DK efter Erhvervsstyrelsens skema) og kan overføres til et andet system.
- **I koden:** `backend/saft/`
  - `GET /api/v1/saft/export?from=&to=[&version=1.0|2.1]` henter filen. Eksporten logges i audit-loggen.
  - Header, MasterFiles (alle konti med primo/ultimo og `StandardAccountID` fra
    `Account.standard_code`, Customers, Suppliers, TaxTable) og GeneralLedgerEntries
    (Journal → Transaction → Line). Kun bogførte posteringer er med.
  - SourceDocuments: SalesInvoices (fakturaer og kreditnotaer), PurchaseInvoices (regninger) og
    Payments, når deres postering er bogført og med i filen (`backend/saft/source_documents.py`).
  - Bankkonti i Header: IBAN eller reg.nr./kontonr. hentes i denne rækkefølge: fra `CompanySettings`
    (første bankkonto), fra felter på kontoen eller journalen, og fra bankkoblingens IBAN.
    Mangler de, skrives "MANGLER", og eksporten giver en tydelig advarsel (`stats["warnings"]`,
    `Header/HeaderComment`, svar-headeren `X-SAFT-Warnings`). `?check=1` returnerer tal og
    advarsler som JSON før udlevering.
  - Valideres i testene mod Erhvervsstyrelsens XSD v1.0 og v2.1 (også med SourceDocuments)
    (`backend/saft/xsd/`, kilde: git.erst.dk/standard-filformater).
  - Default er `SAFT_VERSION=2.1` (krævet fra 1. januar 2027). 1.0 kan stadig vælges med `?version=1.0`.
- **Mangler:**
  - Standardmomskoder (`StandardTaxCode`) og standardkonti kommer fra `TaxCode.standard_code`
    og `Account.standard_code`, og kontoplanen og momskoderne skal have dem udfyldt (data, ikke kode).

## 8. Opbevaring efter opsigelse eller ophør
- **Krav:** Når en kunde opsiger aftalen eller ophører, skal materialet stadig opbevares og
  være tilgængeligt i 5 år (også ved konkurs eller ophør hos udbyderen).
- **I koden:** `archive_client` (read-only med `retain_until`). Skemaet slettes ikke. Backuppen
  har skemaer pr. kunde, så en kunde kan gendannes og udleveres for sig.
- **Lukket i koden:** "Eksportér alt" virker også for arkiverede kunder (kundens administrator,
  og en partner uden samtykke ved ophør, kurator eller myndighed – logges som `export_all`).
  Procedure: `docs/udlevering.md`.
- **Mangler (organisatorisk):** Kontraktbestemmelse med kunderne og deponering (escrow) af
  backupnøglen og lageradgangen, som beskrevet i `docs/udlevering.md` afsnit 4.

## 9. Sikkerhed og adgangsstyring
- **Krav:** Kun autoriserede brugere har adgang, og data er beskyttet mod uautoriseret ændring.
  Kommunikationen er krypteret.
- **I koden:**
  - Ét Postgres-skema pr. kunde, `X-Client` og adgangskontrol i `tenancy/middleware.py` og
    `tenancy/access.py`. Testet i `tenancy/tests_isolation.py`.
  - Roller (admin/accountant/viewer) i `core/permissions.py`. Revisorens adgang kræver kundens
    samtykke (`AccessGrant`), som kan tidsbegrænses og tilbagekaldes.
  - Throttling af login (`REST_FRAMEWORK.DEFAULT_THROTTLE_RATES`), JWT og sikre cookies i
    `config/settings/server.py`. TLS i reverse proxy (`docker-compose.server.yml`).
  - Backups er krypteret (punkt 4). Containerne kører som en ikke-root-bruger (`backend/Dockerfile`).
- **Lukket:**
  - `AUTH_PASSWORD_VALIDATORS` er slået til (mindst 10 tegn, almindelige koder, kun tal, ligner
    brugernavnet) og bruges ved oprettelse, nulstilling og skift (`/api/v1/me/password`).
  - To-faktor-login (TOTP + 10 gendannelseskoder, ingen genbrug af koder, hemmelighed krypteret):
    `tenancy/mfa.py`, `tenancy/auth_views.py`. **Obligatorisk for revisorhusets medarbejdere**
    (`FIRM_MFA_REQUIRED`), både i admin-portalen og når de åbner en kundes bøger. Testet i
    `tenancy/tests_security.py`.
  - `FIELD_ENCRYPTION_KEY` skal komme fra miljøet i produktion (`config/settings/server.py`).
- **Mangler (drift):** Kryptering af disk/volumen hos hostingudbyderen, periodisk
  adgangsgennemgang (fx kvartalsvis: medarbejdere, tildelinger, aktive samtykker) og en proces
  for sikkerhedsopdateringer.

## 10. Logning
- **Krav:** Ændringer og adgang logges, så det kan dokumenteres, hvem der har gjort hvad og hvornår.
- **I koden:**
  - Hash-kædet audit-log pr. kunde, som kun kan tilføjes til (DB-trigger): `core/audit.py`,
    `core/migrations/0011_audit_append_only.py`. Revisorhusets handlinger mærkes `_via: firm`.
  - `FirmAuditLog` for hver skrivning fra revisorhuset: `tenancy/middleware.py`.
  - E-faktura (send og regning), bankimport (journals) og SAF-T-eksport logges.
- **Lukket:** Revisorhusets læseadgang logges i `FirmAuditLog` (`read`, én post pr. medarbejder,
  kunde og time med den første sti), også for nøgletal og saldobalance i admin-portalen. Login,
  MFA-ændringer og eksporter logges.
- **Mangler (drift):** Central opsamling og opbevaring af server-logs.

## 11. Moms og indberetninger til Skat
- **Krav:** Ikke et krav i bekendtgørelsen, men en del af momsloven og praksis. Momsangivelsen
  skal kunne dannes ud fra bogføringen.
- **I koden:** Momsangivelse og afstemning: `core/vat.py` og `core/vat_views.py`. Adapter for
  system-til-system: `integrations/skat_vat.py` (mock og stub). Uden aftale tastes felterne i TastSelv.
- **Mangler:** Godkendelse som systemleverandør hos Skattestyrelsen, et OCES3-certifikat og
  implementering af stubben. Det samme gælder eIndkomst for løn (`payroll/`).

## 12. Systemdokumentation og brugervejledning
- **Krav:** Der skal findes en beskrivelse af systemet og vejledning til brugerne, også i, hvordan
  materialet opbevares og eksporteres.
- **Lukket:** `docs/systembeskrivelse.md` (arkitektur, dataflow, backup, adgang, ansvar),
  `docs/brugervejledning.md` (kunder og medarbejdere) og `docs/udlevering.md` (procedure ved
  ophør, kurator og myndigheder).

---

### Aftaler og certifikater, der skal på plads, før de rigtige adaptere slås til

| Adapter (env) | Værdi | Kræver |
|---|---|---|
| `CVR_PROVIDER` | `cvrapi` | Ingen aftale til få opslag (token anbefales: `CVRAPI_TOKEN`) |
| `CVR_PROVIDER` | `virk` | Aftale med Erhvervsstyrelsen om CVR System-til-system (brugernavn og adgangskode) |
| `CURRENCY_PROVIDER` | `nationalbank` | Ingen (offentligt XML-feed) |
| `BANK_FEED_PROVIDER` | `aiia`/`tink`/`enablebanking` | Kundeaftale med en licenseret AIS-udbyder, klient-id/secret eller nøgle, redirect-URL |
| `EINVOICE_ACCESS_POINT` | `nemhandel` | NemHandel-tilslutning, OCES3-virksomhedscertifikat, registrering i NemHandelsregistret (SMP) |
| `EINVOICE_ACCESS_POINT` | `storecove`/`pagero` | Aftale med et certificeret Peppol access point og API-nøgle |
| `SKAT_VAT_PROVIDER` | `skat` | Godkendelse som systemleverandør, OCES3-certifikat, kundens fuldmagt i TastSelv Erhverv |
| backup (`BACKUP_S3_*`) | – | Lagerudbyder i EU med databehandleraftale, bucket med versionering eller object lock |
