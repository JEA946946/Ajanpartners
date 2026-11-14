# Bogføring (bookkeeping.vmmorocco.com) – arbejdsnoter til Claude

Django-backend (`backend/`) og React/MUI-frontend (`frontend/`). Fra 2026-10-27 arbejder vi kun her. Bøgerne blev tømt og startet forfra på den marokkanske kontoplan (PCGM).

## Lov og kontoplan
- `Law/` er den gældende kilde: `Plan Comptable marocain (1).pdf` (PCGM) og `guide_fiscal_complet_agence.pdf` (LF 2026, rejsebureau med gæster fra udlandet). Ved uenighed vinder den over `TAX_REFERENCE_MOROCCO.md`.
- `backend/accounts/pcgm.py`: hele PCGM, klasse 1–8 og 0 (klasse 9 er udeladt), plus egne underkonti. Klasse 8 og 0 er inaktive. Trykfejl i PDF'en er rettet; listen står i filens docstring.
- `backend/accounts/chart.py`: alle konti koden bogfører på. Kontonumre må aldrig hårdkodes andre steder; brug konstanterne derfra (backend) og `frontend/src/utils/chart.ts` (frontend).
- `seed_accounts` kører ved hver containerstart. Den opretter manglende konti og retter forældre, men omdøber og sletter aldrig.

## Bogføringsregler (régime de la marge, Art. 125 bis CGI)
| Hændelse | Debet | Kredit |
|---|---|---|
| Faktura (TTC, brutto) | 3421 Clients | 71243 Prestations de services |
| Kunden betaler | 5141x bank | 3421 |
| Forudbetaling før faktura | 5141x | 4421 |
| Turismeleverandør (hotel, guide, transport) TTC, ingen fradrag | 61263x | 4411 |
| Driftsomkostning med TVA | 61xx HT + 34552 | 4411 |
| TVA på margin pr. periode = (salg − kostpris) / 1,2 × 20 % | 71243 | 4455 |
| Løn | 61711 + 61741 | 4432 netto / 4441 CNSS / 44525 IR |
| Husleje med RAS 10/15 % | 61312 | 4411 netto + 4457 |

- Banklinjer importeres mod 34971 (à classer). Kategorisering, match af regninger og match af fakturaer omskriver dette ben.
- CIH 600 EUR (51413) er i euro, ikke dirham. Euroer har ingen dirham-værdi, før de veksles til CIH 300 (51411); først da bogføres indtægten med de dirham, der kom ind (`journals/receipts.py`). Indtil da står modposten på 34972 (EUR).
- Linjer med `currency` ≠ MAD holdes ude af alle dirham-summer: rapporter, TVA, margin, pengestrøm og board. Brug `JournalEntryLine.objects.in_mad()` i nye summer. Råbalance og balance viser EUR-saldi for sig selv (`foreign_rows`). Kontokort regner saldoen i kontoens egen valuta.
- Margin og TVA beregnes i `journals/margin.py` og vises på siden Margin/TVA (`/margin-recognition`). Den gamle bogføring "margin_recognition" (240000→420000) findes ikke længere.

## Journaler, validering og periodeafslutning (Loi 9-88)
- Hver postering ligger i én journal (`journals.Journal`): BQ1 CIH 300 (51411), BQ2 CIH 600 (51412), BQ3 CIH 600 EUR (51413), BQ4 BP 09 (51414), CA kasse (51611), AC køb, VE salg, PA løn, OD diverse og AN åbning. Koderne står kun i `journals/journal_for.py`. Bank- og kasselinjer går i kontoens journal (`journal_for_account`), resten efter `source` (`journal_for_source`).
- Status: kladde (`is_posted=False`, uden for bøgerne), brouillard (bogført, kan rettes) og valideret (`validated_at`).
- Validering sker kun ved månedsafslutning (`journals/closing.py`, siden `/closing`). Måneder lukkes i rækkefølge. Lukningen kræver ingen kladder, at alle posteringer balancerer, og en afsluttet bankafstemning pr. bankjournal på månedens sidste dag. Saldo på 34971 er en advarsel. Posteringerne får endeligt nummer pr. journal og år i datoorden (`BQ1-2026-00001`); indtil da har de et kladdenummer `BR-000001`.
- En valideret postering kan aldrig ændres eller slettes. Det håndhæves af signaler (`journals/signals.py`) og en database-trigger (migration 0013). Rettelser sker ved tilbageføring (`reverse_entry`, contre-passation) i en åben måned. `closed_period_error` afviser alt i en lukket måned eller et lukket år. Et lukket regnskabsår kan ikke genåbnes.
- `reset_bookkeeping` løfter låsen med `journals.signals.allow_reset()`.

## Tiers, lettrage og ét sted for hver betaling
- Linjer på 3421, 4421 og 4411 har en tiers (`partner_type`/`partner_id`/`partner_name`, lokal Customer- eller Supplier-id). Fakturaer, kreditnotaer, regninger, CRM-sync og bankmatch sætter den; manuelle posteringer kræver den (`_tiers_error` i `journals/views.py`).
- Lettrage (`journals/lettrage.py`, siden `/lettrage`): linjer på samme konto og tiers, som går i nul, får samme kode (AA, AB …). En fuldt betalt regning og en fuldt modtaget MAD-faktura udlignes automatisk; undo fjerner koden. Kun lettrage-felterne må ændres på en valideret linje (signal + migration 0015).
- Aldersfordelingen kommer fra de ikke-udlignede linjer, FIFO pr. tiers, med 60 dages betalingsfrist (Loi 69-21).
- Kontoudtoget er den eneste kilde til bevægelser i bankerne: betalingssiden opretter ikke længere betalinger, udgifter bogføres kun fra kassen (CA), løn krediterer 4432 (udbetalingen kategoriseres mod 4432), og CRM-leverandørbetalinger bogføres DR 61263x / CR 4411 i AC. CRM-fakturaer kan ikke længere importeres som fakturaer; CRM-sync bogfører dem i VE.

## Data og drift
- Apps: accounts, core (betalinger, afstemning, dokumenter, audit, firmaindstillinger), journals (posteringer, bankimport, CRM-sync, kvitteringer), purchases, sales, payroll, board (read-only API til board-appen).
- CRM-sync: `journals/cmr_sync.py` (kommandoen `sync_cmr` og siden CMR Sync). Der er ingen scheduler; synkronisering sker kun, når nogen starter den.
- `reset_bookkeeping [--confirm]`: tømmer alle tal og flytter stamdata over på PCGM. Uden `--confirm` er det en tør kørsel.
- Prod: `/opt/dmc-bookkeeping` på 144.76.60.47, container `dmc_bookkeeping_django`, database `dmc_bookkeeping` i containeren `dmc-cmr-db`. Push til `main` deployer via `.github/workflows/deploy-bookkeeping.yml`. Backup tages med `docker exec dmc-cmr-db pg_dump -U postgres dmc_bookkeeping > /opt/backups/…`.
- Uploadede filer (bilag) ligger på værten i `/opt/dmc-bookkeeping/media`, monteret som `/app/media`. De hentes kun via `documents/<id>/download` (kræver login). Hvert bilag får SHA-256 og størrelse ved upload, og et bilag til en valideret postering kan ikke slettes eller flyttes. Logoer gemmes som base64 i databasen.
- `infra/backup.sh` kører hver nat kl. 02:30 (cron, installeres af deploy-workflowet) og gemmer database og media i `/opt/backups/bookkeeping`: daglige kopier i 40 dage, den 1. i hver måned for altid (10 års opbevaring, Loi 9-88 art. 22).
- Audit-loggen er append-only og hash-kædet (`core/audit.py`, `verify_chain`, `/audit-log/verify`); en trigger (core migration 0011) afviser UPDATE og DELETE. Skriv altid via `log_action`.
- Tests: `cd backend && DB_HOST=dmc-cmr-db.orb.local DB_PASSWORD=… DJANGO_SETTINGS_MODULE=config.settings.local .venv/bin/python manage.py test core.tests_ledger core.tests_pure core.tests_reset journals.tests_cmr_sync journals.tests_receipts`. Adgangskoden står i `crm/api/.envs/.local/.postgres`. `DB_NAME` vælger en anden lokal database.
- Frontend: `npm run lint && npm run build`.
