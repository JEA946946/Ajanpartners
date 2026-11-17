# Brugervejledning – Ajan Partners Bogføring

Til kunderne. Revisorhusets medarbejdere har deres egen del af programmet (admin-portalen) og finder vejledningen nederst.

## Kom i gang
1. Du får en e-mail fra Ajan Partners med brugernavn og en midlertidig adgangskode. Log ind, og skift adgangskoden under **Min profil** (klik på dine initialer øverst til højre).
2. Første gang skal du læse og acceptere **forretningsbetingelserne** og **databehandleraftalen**. De supplerer jeres aftale med Ajan Partners. Ajan Partners har adgang til jeres bøger efter aftalen, så de kan levere bogføring, moms og regnskab, og al deres læsning og ændring logges. Under **Indstillinger → Aftale og betingelser** kan du altid se aftalen, hvem i Ajan Partners der har adgang, og hvad der er accepteret.
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
- **Kunder**: oversigt med adgangsstatus, næste frist og åbne opgaver. "Arbejd i kunden" åbner kundens bøger efter kundeaftalen, og alt logges. Et gult banner viser, at du arbejder hos en kunde.
- **Opret kunde**: CVR-opslag udfylder stamdata. Vælg pakke, momsperiode og kontoplan, og angiv eventuelt en reference til opdragsbrevet. I har adgang med det samme. Kunden accepterer betingelserne ved første login.
- **Skabeloner**: opdragsbreve, erklæringer, ledelseserklæringer, generalforsamlings- og selskabsdokumenter, hvidvask/kundekendskab, årsafslutning, skat og kundebreve. Vælg skabelon og kunde, så flettes stamdata, regnskabsår, frister, nøgletal fra bogføringen og branchespecifikke afsnit ind (ud fra branchekoden). Udfyld de felter, der mangler (markeret […]), ret evt. i teksten, og hent den som Word eller PDF. Fra kundedetaljen åbner **Dokumenter** skabelonerne med kunden valgt. Skabelonerne er et udgangspunkt; den underskrivende revisor tilpasser til opgaven.
- **Hvidvask (KYC)**: under kunden → fanen **Hvidvask** registreres reelle ejere, ledelse og personer, der handler på kundens vegne (fødselsdato – ikke CPR – kontrolmetode, evt. kopi af legitimation, PEP). Risikovurderingen udfyldes som en kladde: ni spørgsmål med henvisning til hvidvaskloven, formål og tilsigtet beskaffenhed, midlernes oprindelse (krævet ved PEP), samlet risiko og begrundelse. Systemet foreslår en risiko ud fra husets branchevurdering og registrerede PEP'er, men revisoren tager selv stilling. En **partner** godkender, og så er vurderingen låst (med kontrolsum); en opdatering er en ny version. Næste opdatering beregnes ud fra husets politik (Revisorhuset → Hvidvask, standard 36/24/12 måneder for lav/normal/høj). Siden **Hvidvask (KYC)** viser kunder, der mangler eller skal opdateres, og partnere kan registrere interne underretninger. Oplysningerne vises aldrig for kunden. Den månedlige kørsel opretter en intern opgave, når kundekendskab mangler eller er forfaldent.
- **Kundeaccept**: under kunden → fanen **Kundeaccept** vurderes accept af en ny kunde/opgave og fortsættelse (syv spørgsmål om kundekendskab, uafhængighedstrusler, skift af revisor, kompetencer, god revisorskik og vederlag med henvisning til revisorloven og bekendtgørelserne om uafhængighed og intern organisation). En partner accepterer eller afviser; en accepteret vurdering er låst. Accept kræver, at kundekendskabet er godkendt og opdateret, at der ikke er uafklarede uafhængighedsforhold for kunden, og at der ikke foreligger en trussel, som altid udelukker opgaven (BEK 520/2024 § 2). Andre trusler skal dokumenteres sammen med sikkerhedsforanstaltningerne.
- **Uafhængighed**: hver medarbejder underskriver én gang om året en erklæring (syv spørgsmål efter BEK 520/2024 §§ 2 og 7). Et "ja" eller et nyt forhold i løbet af året registreres pr. kunde og **fjerner straks medarbejderen fra kunden**; medarbejderen kan ikke tildeles kunden igen, før en partner har afklaret forholdet (fjernet, afhændet/ophørt, sikkerhedsforanstaltninger – kun ved øvrige trusler – eller huset afstår). Et forhold, der vedrører en partner, skal afklares af en anden partner. Partnere ser, hvem der mangler at underskrive.
- **Betingelser**: partnere publicerer nye versioner af forretningsbetingelser, databehandleraftale og privatlivspolitik. En ny version skal accepteres igen af kunderne.
- **Fristkalender**: moms, A-skat og AM-bidrag, årsrapport og selvangivelse, beregnet ud fra kundens stamdata. Tjek altid mod Skats kalender ved tvivl.
- **Opgaver**: bilagsforespørgsler og spørgsmål til kunden. Interne opgaver kan kunden ikke se.
- **Eksportér alt**: på kundedetaljen; se `docs/udlevering.md` for proceduren ved ophør, kurator og myndigheder.
