# Brugervejledning – Ajan Partners Bogføring

Til kunderne. Revisorhusets medarbejdere har deres egen del af programmet (admin-portalen) og finder vejledningen nederst.

## Kom i gang
1. Du får en e-mail fra Ajan Partners med brugernavn og en midlertidig adgangskode. Log ind, og skift adgangskoden under **Min profil** (klik på dine initialer øverst til højre).
2. Første gang bliver du spurgt, om Ajan Partners må arbejde i jeres bogføring. Vælg omfanget:
   - **Læse**: revisor kan se, men ikke ændre.
   - **Bogføre**: revisor kan bogføre, afstemme og lave moms, men ikke ændre brugere og adgang.
   - **Fuld adgang**: som jeres egen administrator.
   Du kan sætte en slutdato og altid trække adgangen tilbage under **Indstillinger → Revisoradgang**.
3. Vi anbefaler at slå **to-faktor-login** til under Min profil. Så skal du også bruge en kode fra telefonen, når du logger ind. Gem gendannelseskoderne et sikkert sted.

## Pakker
Programmet er gratis. Hvilke funktioner I har, afhænger af jeres aftale med Ajan Partners:

| | Mini | Standard | Pro |
|---|---|---|---|
| Bilag, fakturering og rapporter | ✓ (10 fakturaer/md.) | ✓ | ✓ |
| Regninger, bank, moms, e-faktura, posteringer | – | ✓ | ✓ |
| Løn og projekter | – | – | ✓ |
| Brugere | 1 | 3 | ubegrænset |

I Mini-pakken uploader I bilag og fakturerer, og Ajan Partners laver bogføringen. Mangler I en funktion, så kontakt os.

## Det daglige
- **Bilag**: upload kvitteringer og regninger under Bilag. Hvert bilag får et nummer og en kontrolsum, så det kan dokumenteres, at det ikke er ændret.
- **Fakturaer**: opret kunden (CVR eller EAN for offentlige kunder), lav fakturaen og send den som PDF eller e-faktura. Fakturanumre er fortløbende og kan ikke genbruges.
- **Bank**: kobl banken på under Bank → Bankkobling, eller importér kontoudtog. Banklinjer, der ikke kan placeres, ligger på "bank til afstemning", indtil de er kategoriseret.
- **Beskeder fra revisor**: her spørger vi, når vi mangler et bilag eller en forklaring. Svar direkte, og vedhæft bilaget.

## Måneds- og årsafslutning
Når en måned lukkes, bliver posteringerne endelige og nummereres. De kan derefter ikke ændres; en fejl rettes med en modpostering. Kræv af jer selv (eller af os), at bankafstemningen er færdig, før måneden lukkes. Momsangivelsen dannes ud fra bogføringen for jeres momsperiode. Ved årets afslutning overføres resultatet til egenkapitalen, og året låses.

## Opbevaring og eksport
Bogføringsloven kræver, at regnskabsmaterialet gemmes i 5 år. Vi tager backup hver nat og gemmer en krypteret kopi i EU. Under **Indstillinger → Eksport af data** kan administratoren altid hente alt (SAF-T-fil, saldobalancer, bilag og log), også hvis I stopper hos os.

---

## Til revisorhusets medarbejdere
- Admin-portalen ligger under **/admin**. Du skal have to-faktor-login, før du kommer ind.
- **Kunder**: oversigt med adgangsstatus, næste frist og åbne opgaver. "Arbejd i kunden" åbner kundens bøger. Det kræver kundens samtykke, og alt logges. Et gult banner viser, at du arbejder hos en kunde.
- **Opret kunde**: CVR-opslag udfylder stamdata. Vælg pakke, momsperiode og kontoplan. Kunden skal godkende adgangen ved første login.
- **Fristkalender**: moms, A-skat og AM-bidrag, årsrapport og selvangivelse, beregnet ud fra kundens stamdata. Tjek altid mod Skats kalender ved tvivl.
- **Opgaver**: bilagsforespørgsler og spørgsmål til kunden. Interne opgaver kan kunden ikke se.
- **Eksportér alt**: på kundedetaljen; se `docs/udlevering.md` for proceduren ved ophør, kurator og myndigheder.
