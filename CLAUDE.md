# Ajan Partners Bogføring – arbejdsnoter

Gratis bogføringsprogram, som revisorhuset Ajan Partners tilbyder sine kunder. Dansk marked: Bogføringsloven (lov nr. 700 af 24/5/2022 + bekendtgørelser om digitale standardbogføringssystemer), momsloven, Årsregnskabsloven (klasse A/B), dansk løn. Kopieret 2026-11-14 fra `vmm-platform/bookkeeping` (marokkansk, single-tenant) og bygget om.

Django 5.2 + DRF backend (`backend/`), React 18 + MUI 5 + Vite frontend (`frontend/`). Sprog i UI og kode-kommentarer: dansk. Valuta: DKK.

## Multi-tenancy (django-tenants, ét Postgres-skema pr. kunde)
- **Public-skemaet** (`tenancy/`, `firm/`, auth): `Firm`, `ClientCompany` (tenant; CVR, pakke, momsperiode, status), `Package`, `FirmStaff` (partner/revisor/bogholder/assistent), `StaffAssignment`, `ClientMembership` (kundens egne brugere: admin/accountant/viewer), `AccessGrant` (revisorhusets adgang iht. kundeaftalen: oprettes aktiv, afsluttes af en partner ved ophør), `TermsDocument`/`TermsAcceptance` (versionerede betingelser og bevis for accept), `FirmAuditLog`.
- **Tenant-skemaer** (`c_<slug>`): accounts, journals, sales, purchases, core, payroll — hele bogføringen. Nye bogføringsapps skal i `TENANT_APPS` i `config/settings/base.py`; apps med tværgående data (revisorhusets opgaver, frister) i `SHARED_APPS`.
- `tenancy/middleware.py`: alle `/api/v1/`-kald undtagen `auth/`, `me`, `me/`, `public/` kræver headeren `X-Client: <slug>`. Middleware'en tjekker adgang (`tenancy/access.py: resolve`), pakkens funktioner (`tenancy/features.py: FEATURE_PATHS`), arkivstatus, og sætter skemaet. `request.tenant` er kunden, `request.client_access` rolle og vej ind (member/firm).
- Pakkerne (Mini/Standard/Pro, alle gratis) begrænser **kun kundens egne brugere**. Revisorhuset har alle funktioner, når det har en aktiv grant. Ny funktion → tilføj den i `FEATURES`, `DEFAULT_PACKAGES` og `FEATURE_PATHS`, og i frontend `feature` på route (`App.tsx`) og menupunkt (`Layout.tsx`).
- Rettigheder: `core.permissions.RoleWriteAccess` (læs alle, skriv admin/accountant), `IsAdmin` (kundens administrator), `IsFirmStaff`, `IsFirmPartner` (admin-portalen).
- Audit: `core.audit.log_action` skriver i kundens hash-kædede log. Når en medarbejder fra revisorhuset handler, tilføjes `_via: firm` m.m. automatisk (via `tenancy/context.py`). Skrivende kald fra revisorhuset logges også i `FirmAuditLog`.
- Kunder oprettes med `tenancy.services.create_client` (skema + migrationer + `seed_accounts --template` + en **aktiv** AccessGrant iht. kundeaftalen). Kundens brugere accepterer forretningsbetingelser og databehandleraftale ved første login (`/onboarding`, `tenancy/terms.py`). Middleware'en afviser kundens brugere med `terms_acceptance_required`, indtil det er sket (undtagen `export-all`). Tests med kundebrugere skal kalde `tenancy.terms.accept(...)`.
- Bilag gemmes pr. skema (`TenantFileSystemStorage`, `MEDIA_ROOT/<schema>/`).

## Sikkerhed
- Adgangskoder: Djangos validatorer (min. 10 tegn m.m.). Brug `validate_password` ved alle oprettelser/skift.
- To-faktor (TOTP): `tenancy/mfa.py`, `tenancy/auth_views.py` (`/auth/login` → `mfa_required` + `/auth/mfa/verify`, `/me/mfa/*`, `/me/password`). Obligatorisk for `FirmStaff` (`FIRM_MFA_REQUIRED`, håndhæves i `IsFirmStaff`/`IsFirmPartner` og i middleware ved kundeadgang). Tests, der ikke tester MFA, bruger `@override_settings(FIRM_MFA_REQUIRED=False)`.
- Revisorhusets læsning logges i `FirmAuditLog` (`read`, én pr. medarbejder/kunde/time), skrivning altid.
- "Eksportér alt": `tenancy/export.py` (SAF-T 2.1 pr. år, saldobalancer, bilag, audit-log, manifest). `/api/v1/export-all` og `/api/firm/clients/<slug>/export-all`.
- Opbevaring: `retention_report` (månedligt) laver en opgave til en partner; intet slettes automatisk.

## Admin-portalen
- Backend: `firm/` → `/api/firm/...` (public). Frontend: `frontend/src/admin/` (route `/admin/*`), API-klient `firmApi` i `services/api.ts`.
- Tal fra en kundes bøger kræver aktiv grant (`active_grant`). Stamdata gør ikke.
- **Skabeloner** (`/admin/templates`): filer i `backend/firm/doc_templates/<kategori>/<id>.md` (JSON-front-matter + Django-skabelonsprog, format i `docs/skabeloner-format.md`). Fletning i `firm/templating.py` (kunde, revisorhus, regnskabsår, nøgletal), branchegrupper ud fra DB25 i `firm/branche.py`, Word-eksport i `firm/docx_export.py`. Kun tags `if/for/comment` er tilladt. `firm.tests_templates.AllTemplatesTests` fletter hver skabelon for flere selskabsformer og brancher – kør den efter nye skabeloner.
- **Hvidvask/KYC** (`/admin/aml`, kundefanen Hvidvask): `firm/models.py` (`KycPerson`, `KycAssessment`, `AmlReport`), `firm/views_kyc.py`, spørgsmål i `firm/checklists/kyc.json` (hjemler kun fra `docs/skabeloner-verifikation/`). Godkendt vurdering er låst (sha256), ny vurdering = ny version; personer slettes aldrig (markeres inaktive). Underretninger kun for partnere og logges uden kunde/indhold. `kyc_review_report` (månedligt i `infra/worker.sh`) opretter interne opgaver. Næste faser: kundeaccept/uafhængighed, opdrag og kvalitetsstyring, tid/fakturering, arkiv, fuldmagter og dashboard.

## Frontend
- `hooks/useClient.tsx`: `/me` (kunder, revisorrolle, manglende accept af betingelser) og den valgte kunde (`features`, `access`). `useFeature('payroll')`, `RequireFeature`.
- `services/api.ts` sætter `X-Client` fra `localStorage.ap_client` på alle kald undtagen `/auth`, `/me`.
- Kontonumre kun via `frontend/src/utils/chart.ts`.

## Bogføringsregler (bevaret fra originalen)
- Hver postering i én journal; status kladde → bogført → valideret ved periodeafslutning. Validerede posteringer kan aldrig ændres (signaler + DB-trigger, journals migration 0013/0015); rettelser via tilbageføring. Lukket periode/år afviser alt.
- Fortløbende nummerering pr. journal og år ved validering.
- Udligning (lettrage) på debitor-/kreditorkonti med tiers.
- Kontonumre må aldrig hårdkodes udenfor `backend/accounts/chart.py` og `frontend/src/utils/chart.ts`.

## Drift og test
- Lokalt: Homebrew Postgres på localhost, database `ajanpartners`. `cd backend && export DJANGO_SETTINGS_MODULE=config.settings.local`.
  - `.venv/bin/python manage.py migrate_schemas --shared` (public) og `migrate_schemas` (alle kunder).
  - `.venv/bin/python manage.py bootstrap_firm --firm-name … --cvr … [--address … --email … --phone …] --partner-email … --partner-password …` (kan køres igen; kun angivne stamdata opdateres).
  - Tests: `.venv/bin/python manage.py test <moduler>` (django-tenants: brug `django_tenants.test.cases.TenantTestCase` for tenant-tests).
- Hele testsuiten: `TEST_DB_NAME=test_ap_main .venv/bin/python manage.py test --noinput` (≈190 tests, ca. 3 min).
- Lokalt: backend `manage.py runserver 8011` (8001 bruges af et andet projekt), frontend `BOOKKEEPING_API_URL=http://localhost:8011 npm run dev` → http://localhost:5174.
- Frontend: `cd frontend && npm run lint && npm run build`.
- Dokumentation: `docs/systembeskrivelse.md`, `docs/brugervejledning.md`, `docs/udlevering.md`, `docs/compliance-bogforingsloven.md`.
- Opbevaring: Bogføringsloven kræver 5 år. Kunder slettes aldrig, de arkiveres (`archive_client`, read-only, `auto_drop_schema = False`).
