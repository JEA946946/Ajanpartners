---
{
  "title": "Aftale om bogføring, løn og moms",
  "description": "Aftale om løbende bogholderi, lønadministration og momsangivelse (ikke-erklæringsopgave). Indeholder ansvarsfordeling, frister, adgang til bogføringssystemet og databehandleraftale efter GDPR art. 28.",
  "kind": "brev",
  "references": ["Bogføringsloven (lov nr. 700 af 24/05/2022)", "Momsloven", "Skatteforvaltningsloven", "Kildeskatteloven og indkomstregisterloven (eIndkomst)", "Databeskyttelsesforordningen art. 28", "Hvidvaskloven § 1, stk. 1, nr. 14 og 16, og § 5", "Revisorloven § 24"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "bogfoering", "label": "Løbende bogføring", "type": "checkbox", "default": true},
    {"name": "bogfoering_frekvens", "label": "Bogføringsfrekvens", "type": "select", "options": ["ugentligt", "hver 14. dag", "månedligt", "kvartalsvis"], "default": "månedligt"},
    {"name": "loen", "label": "Lønadministration", "type": "checkbox", "default": false},
    {"name": "antal_loenmodtagere", "label": "Forventet antal lønmodtagere", "type": "number"},
    {"name": "loenperiode", "label": "Lønperiode", "type": "select", "options": ["månedsløn", "14-dagesløn", "månedsløn og 14-dagesløn"], "default": "månedsløn"},
    {"name": "moms", "label": "Momsangivelse", "type": "checkbox", "default": true},
    {"name": "debitor_kreditor", "label": "Betaling af kreditorer og opfølgning på debitorer", "type": "checkbox", "default": false},
    {"name": "rapportering", "label": "Periodisk rapportering (balance/resultat)", "type": "select", "options": ["ingen", "månedlig", "kvartalsvis", "halvårlig"], "default": "kvartalsvis"},
    {"name": "materialefrist", "label": "Kundens frist for aflevering af bilag (dage efter periodens udløb)", "type": "number", "default": "8"},
    {"name": "pris", "label": "Pris (fast månedligt beløb eller anden prisaftale)", "type": "text"},
    {"name": "timepris", "label": "Timepris for ekstraarbejde (kr. ekskl. moms)", "type": "number"},
    {"name": "loen_pris", "label": "Pris pr. lønseddel (kr. ekskl. moms)", "type": "number"},
    {"name": "opsigelse", "label": "Opsigelsesvarsel", "type": "select", "options": ["1 måned til udgangen af en måned", "3 måneder til udgangen af en måned", "løbende måned + 1 måned"], "default": "3 måneder til udgangen af en måned"},
    {"name": "ikrafttraeden", "label": "Aftalen gælder fra", "type": "date"},
    {"name": "ansvarsbegraensning", "label": "Ansvarsbegrænsning – beløb/formulering (udfyldes af revisor)", "type": "text"},
    {"name": "reklamationsfrist", "label": "Frist for at fremsætte krav, fx \"6 måneder\" (udfyldes af revisor)", "type": "text"},
    {"name": "underdatabehandlere", "label": "Underdatabehandlere (fx hosting, lønsystem)", "type": "textarea", "default": "Hosting af bogføringssystemet: [udbyder, land]\nLønsystem: [udbyder, land]"}
  ]
}
---
**{{ kunde.navn }}**
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

CVR-nr. {{ kunde.cvr }}

{{ dato.idag }}

# Aftale om bogføring{% if felt.loen %}, løn{% endif %}{% if felt.moms %} og moms{% endif %}

Mellem {{ kunde.navn }} (herefter "kunden") og {{ firma.navn }}, CVR-nr. {{ firma.cvr }} (herefter "vi") er indgået aftale om følgende ydelser med virkning fra {{ felt.ikrafttraeden }}.

Opgaverne er **ikke erklæringsopgaver**. Vi afgiver ingen erklæring med eller uden sikkerhed om bogføringen, lønnen eller momsangivelserne, og vores arbejde kan ikke erstatte revision, review eller opstilling, som i givet fald aftales særskilt.

## 1. Ydelser

{% if felt.bogfoering %}**Bogføring.** Vi bogfører kundens bilag {{ felt.bogfoering_frekvens }} i vores bogføringsprogram, herunder registrering af køb, salg, bank, kasse og lønninger, afstemning af bank- og mellemregningskonti samt udligning af debitorer og kreditorer. Bogføringen sker efter bogføringslovens krav, og transaktioner registreres i én journal med fortløbende nummerering.
{% endif %}
{% if felt.loen %}**Løn.** Vi udarbejder løn ({{ felt.loenperiode }}) til ca. {{ felt.antal_loenmodtagere }} lønmodtagere, indberetter til eIndkomst, beregner og indberetter A-skat, AM-bidrag, ATP, feriepenge (Feriepengeinfo/FerieKonto eller feriekort), pension efter de oplysninger, kunden giver os, samt øvrige lovpligtige lønrelaterede bidrag efter de gældende regler. Kunden godkender lønnen, før den udbetales, og afgiver alle oplysninger om ansættelser, fratrædelser, lønændringer, sygdom, ferie og personalegoder rettidigt.
{% endif %}
{% if felt.moms %}**Moms.** Vi opgør og angiver moms ({{ kunde.momsperiode }}) på TastSelv Erhverv på grundlag af bogføringen og indberetter EU-salg uden moms, hvor det er relevant. Kunden betaler selv momsen til skattekontoen.{% if branche.momsfritaget %} Kunden har helt eller delvis momsfritagne aktiviteter. Vi opgør delvis fradragsret og lønsumsafgift efter de oplysninger, kunden giver os om fordelingen af aktiviteterne.{% endif %}{% if branche.byggeri %} Kunden skal oplyse os om køb og salg af varer og ydelser, der er omfattet af omvendt betalingspligt (momslovens § 46, stk. 1, fx metalskrot), og om køb af ydelser fra udenlandske virksomheder, så momsen opgøres korrekt.{% endif %}{% if branche.bilhandel %} Brugtmoms (momslovens § 69 ff.) og registreringsafgift kræver korrekt dokumentation for hver bil, herunder lagerbog og købsaftaler. Kunden skal levere dokumentationen sammen med bilagene.{% endif %}{% if branche.restauration %} Ved salg af drikkevarer og fødevarer skal kunden have et kassesystem, der lever op til de gældende krav, og levere dagsopgørelser (z-rapporter) for hver dag.{% endif %}
{% endif %}
{% if felt.debitor_kreditor %}**Betaling og opfølgning.** Vi forbereder betalinger til kreditorer i kundens netbank til kundens godkendelse og følger op på forfaldne debitorer efter kundens instruks. Vi har ikke selvstændig fuldmagt til at gennemføre betalinger.
{% endif %}
{% if felt.rapportering != "ingen" %}**Rapportering.** Vi udarbejder {{ felt.rapportering }} balance og resultatopgørelse med sammenligningstal. Rapporterne er ikke revideret eller gennemgået og indeholder ikke nødvendigvis alle periodiseringer.
{% endif %}

Opgaver, der ikke er nævnt ovenfor (fx årsregnskab, selvangivelse, rådgivning, dialog med Skattestyrelsen ved kontrol), aftales og afregnes særskilt.

## 2. Ansvarsfordeling

| Område | Kunden | {{ firma.navn }} |
|---|---|---|
| Ledelsens ansvar for bogføring, regnskab og intern kontrol (bogføringsloven) | ✔ | |
| Fuldstændige, rigtige og rettidige bilag og oplysninger | ✔ | |
| Opbevaring af bilag og regnskabsmateriale i 5 år | ✔ (via systemet) | Systemet opbevarer det materiale, der uploades |
| Kasse, kasseafstemning og dagsopgørelser | ✔ | |
| Registrering i bogføringssystemet | | ✔ |
| Afstemning af bank og mellemregninger | | ✔ |
| Godkendelse af løn før udbetaling | ✔ | |
| Indberetning af løn til eIndkomst | | ✔ (hvis aftalt) |
| Momsangivelse | | ✔ (hvis aftalt) |
| Betaling af skat, moms og A-skat | ✔ | |
| Overholdelse af frister, når kunden ikke har leveret materiale rettidigt | ✔ | |

Kunden afleverer bilag og oplysninger senest {{ felt.materialefrist }} dage efter hver periodes udløb, normalt ved upload i bogføringsprogrammet. Hvis materialet ikke modtages rettidigt, kan vi ikke garantere, at frister overholdes, og vi hæfter ikke for renter, gebyrer eller skønsmæssige ansættelser, der skyldes forsinkelse fra kundens side. Vi orienterer kunden, hvis vi bliver opmærksomme på manglende eller usædvanlige bilag.

Vi træffer ikke ledelsesbeslutninger på kundens vegne. Hvis vi også er kundens revisor, tilrettelægges opgaverne, så kunden godkender alle væsentlige posteringer, og så vores uafhængighed ikke trues, jf. revisorlovens § 24.

## 3. Adgang til bogføringssystemet

Kunden får adgang til vores bogføringsprogram, der er et digitalt bogføringssystem efter bogføringsloven. Systemet opbevarer registreringer og bilag digitalt og sikrer automatisk sikkerhedskopiering. Kundens egne brugere (administrator, bogholder, læseadgang) oprettes af kunden. Vores medarbejdere har adgang til kundens bøger i aftalens løbetid. Adgangen afsluttes, når aftalen ophører. Kunden kan til enhver tid eksportere alle data, herunder SAF-T-fil, saldobalancer og bilag.

Kundens brugere skal acceptere systemets forretningsbetingelser og databehandleraftale ved første login.

## 4. Hvidvask

Vi er omfattet af hvidvaskloven (§ 1, stk. 1, nr. 14 og 16) og skal gennemføre kundekendskabsprocedurer og løbende overvåge kundeforholdet. Kunden skal give os legitimation og oplysninger om ejere, reelle ejere og ledelse og om formålet med samarbejdet. Vi har pligt til at undersøge usædvanlige transaktioner og underrette Hvidvasksekretariatet ved mistanke, og vi må ikke oplyse kunden om en underretning.{% if branche.kontantintensiv %} Da kunden har kontantomsætning, skal kontantsalg dokumenteres dagligt (kasseopgørelse), og vi gør opmærksom på hvidvasklovens kontantforbud, hvorefter erhvervsdrivende, der ikke er omfattet af hvidvaskloven, ikke må modtage kontantbetalinger på 15.000 kr. eller derover, hvad enten betalingen sker på én gang eller som flere betalinger, der er eller ser ud til at være indbyrdes forbundet (hvidvasklovens § 5).{% endif %}

## 5. Databehandleraftale (GDPR art. 28)

Når vi fører bogføring og løn, behandler vi personoplysninger på kundens vegne (bl.a. om ansatte, kunder og leverandører). Kunden er dataansvarlig, og vi er databehandler. Følgende vilkår gælder:

1. **Instruks:** Vi behandler alene personoplysninger efter kundens dokumenterede instruks, som er at levere ydelserne i denne aftale, medmindre EU-ret eller dansk ret kræver andet. Hvidvask- og revisorlovgivningen kan gøre os selvstændigt dataansvarlige for visse oplysninger.
2. **Kategorier:** Almindelige oplysninger (navn, adresse, kontaktoplysninger, bankoplysninger, løn- og ansættelsesforhold), CPR-numre og – ved løn – eventuelle oplysninger om sygdom og fagforeningsmedlemskab, i det omfang det er nødvendigt for lønberegningen.
3. **Registrerede:** Kundens ansatte, kunder, leverandører, kontaktpersoner og ejere.
4. **Fortrolighed:** Vores medarbejdere er underlagt tavshedspligt.
5. **Sikkerhed:** Vi træffer passende tekniske og organisatoriske foranstaltninger (art. 32), herunder adgangsstyring, to-faktor-login for medarbejdere, kryptering under transport, logning og sikkerhedskopiering.
6. **Underdatabehandlere:** Kunden giver generel godkendelse til brug af underdatabehandlere. Vi giver mindst 30 dages varsel om ændringer, så kunden kan gøre indsigelse. Aktuelle underdatabehandlere: {{ felt.underdatabehandlere }}
7. **Overførsel til tredjelande:** Sker kun med gyldigt overførselsgrundlag efter kapitel V.
8. **Bistand:** Vi bistår kunden med at besvare anmodninger fra de registrerede og med at overholde art. 32-36.
9. **Brud på persondatasikkerheden:** Vi underretter kunden uden unødig forsinkelse og senest 48 timer efter, at vi er blevet opmærksomme på bruddet.
10. **Tilsyn:** Kunden kan få adgang til de oplysninger, der er nødvendige for at påvise overholdelsen af art. 28.
11. **Ophør:** Ved aftalens ophør udleverer vi data til kunden (eksport) og sletter dem derefter, medmindre lovgivningen (fx bogføringslovens og hvidvasklovens opbevaringskrav) kræver, at vi opbevarer dem.

## 6. Pris og betaling

Pris: {{ felt.pris }} ekskl. moms.{% if felt.loen %} Lønadministration afregnes med {{ felt.loen_pris }} kr. pr. lønseddel ekskl. moms.{% endif %} Ekstraarbejde, fx på grund af mangelfuldt materiale, oprydning i tidligere perioder, myndighedshenvendelser eller ændrede forhold, afregnes med {{ felt.timepris }} kr. pr. time ekskl. moms. Priserne reguleres en gang årligt med virkning fra 1. januar.

## 7. Ansvar

Vores ansvar er begrænset til {{ felt.ansvarsbegraensning }}. Vi hæfter ikke for indirekte tab, herunder driftstab, tab af data eller renter og gebyrer som følge af kundens forsinkelse. Begrænsningen gælder ikke ved forsæt eller grov uagtsomhed. Krav skal fremsættes skriftligt senest {{ felt.reklamationsfrist }} efter, at kunden er blevet eller burde være blevet opmærksom på forholdet.

## 8. Ophør

Aftalen kan opsiges af begge parter med {{ felt.opsigelse }}. Vi kan ophæve aftalen med øjeblikkelig virkning ved væsentlig misligholdelse, herunder manglende betaling eller manglende medvirken til kundekendskab. Ved ophør færdiggør vi de perioder, der er betalt for, og giver kunden mulighed for at eksportere alle data.

## 9. Øvrige vilkår

Aftalen er underlagt dansk ret. Tvister afgøres ved vores hjemting. Vores almindelige forretningsbetingelser gælder i øvrigt. Ved uoverensstemmelse går denne aftale forud.

&nbsp;

| For {{ kunde.navn }} | For {{ firma.navn }} |
|---|---|
| Dato: | Dato: {{ dato.idag }} |
| &nbsp; | &nbsp; |
| ______________________________ | ______________________________ |
| {{ kunde.ledelsesorgan }} | {{ medarbejder.navn }}, {{ medarbejder.titel }} |
