---
{
  "title": "Opdragsbrev – revision af årsregnskab",
  "description": "Opdragsbrev for lovpligtig eller frivillig revision af årsregnskab efter ISA 210. Omfatter ledelsens og revisors ansvar, revisionsprotokol, hvidvask, databeskyttelse, honorar og ansvarsbegrænsning.",
  "kind": "brev",
  "references": ["ISA 210", "ISA 200", "ISA 580", "ISA 260", "ISA 265", "Revisorloven §§ 16, 18, 20, 22 og 24 (LBK nr. 206 af 20/02/2025)", "Årsregnskabsloven § 135", "Selskabsloven §§ 129 og 144-146", "Hvidvaskloven"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "pmv", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "revisor_titel", "label": "Underskrivende revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "valgt_dato", "label": "Dato for valg som revisor (generalforsamling)", "type": "text"},
    {"name": "lovpligtig", "label": "Revisionen er lovpligtig", "type": "checkbox", "default": true},
    {"name": "har_bestyrelse", "label": "Selskabet har en bestyrelse (ApS)", "type": "checkbox", "default": false},
    {"name": "koncernregnskab", "label": "Der udarbejdes koncernregnskab", "type": "checkbox", "default": false},
    {"name": "regnskabspraksis", "label": "Regnskabsgrundlag", "type": "select", "options": ["årsregnskabslovens bestemmelser for regnskabsklasse B", "årsregnskabslovens bestemmelser for regnskabsklasse B med tilvalg fra regnskabsklasse C", "årsregnskabslovens bestemmelser for regnskabsklasse C (mellemstor virksomhed)", "IFRS som godkendt af EU og yderligere krav i årsregnskabsloven"], "default": "årsregnskabslovens bestemmelser for regnskabsklasse B"},
    {"name": "materiale_dato", "label": "Seneste dato for aflevering af regnskabsmateriale", "type": "date"},
    {"name": "honorar", "label": "Honorar for revision (kr. ekskl. moms)", "type": "number"},
    {"name": "honorar_type", "label": "Honorarform", "type": "select", "options": ["fast honorar", "overslag", "medgået tid"], "default": "overslag"},
    {"name": "timepris", "label": "Timepris for ekstraarbejde (kr. ekskl. moms)", "type": "number"},
    {"name": "fakturering", "label": "Fakturering", "type": "select", "options": ["løbende", "ved afslutning", "aconto månedligt", "aconto kvartalsvis"], "default": "løbende"},
    {"name": "betalingsfrist", "label": "Betalingsfrist (dage)", "type": "number", "default": "14"},
    {"name": "ansvarsbegraensning", "label": "Ansvarsbegrænsning – beløb/formulering (udfyldes af revisor)", "type": "text"},
    {"name": "andre_ydelser", "label": "Andre aftalte ydelser (fx skattebistand, opstilling)", "type": "textarea"}
  ]
}
---
**{{ kunde.navn }}**
{% if kunde.ledelsesorgan %}Att.: {{ kunde.ledelsesorgan }}{% endif %}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

CVR-nr. {{ kunde.cvr }}

{{ dato.idag }}

# Opdragsbrev – revision af årsregnskabet for {{ regnskab.aar }}

{% if felt.valgt_dato %}På generalforsamlingen den {{ felt.valgt_dato }} blev {{ firma.navn }} valgt som revisor for {{ kunde.navn }}.{% else %}{{ firma.navn }} er valgt som revisor for {{ kunde.navn }}.{% endif %} Vi takker for tilliden. Formålet med dette brev er at bekræfte vores forståelse af opgavens mål og omfang, af ledelsens og vores ansvar samt af de øvrige vilkår for samarbejdet, jf. den internationale standard om revision ISA 210 og revisorlovens krav. Opdragsbrevet gælder også for de efterfølgende regnskabsår, indtil det ændres, erstattes eller opsiges.

## 1. Opgavens formål og omfang

Vi reviderer årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}{% if felt.koncernregnskab %} samt koncernregnskabet{% endif %}, der udarbejdes efter {{ felt.regnskabspraksis }}.

{% if felt.lovpligtig %}Revisionen er lovpligtig efter årsregnskabslovens § 135.{% else %}Selskabet er ikke revisionspligtigt efter årsregnskabslovens § 135, men har valgt at lade årsregnskabet revidere. Revisionen udføres på samme vilkår som en lovpligtig revision, og vi afgiver en revisionspåtegning.{% endif %}

Formålet med revisionen er at opnå høj grad af sikkerhed for, om årsregnskabet som helhed er uden væsentlig fejlinformation, uanset om denne skyldes besvigelser eller fejl, og at afgive en revisionspåtegning med en konklusion. Høj grad af sikkerhed er et højt niveau af sikkerhed, men ikke en garanti for, at en revision altid vil afdække væsentlig fejlinformation, når sådan findes.

Vi udfører revisionen i overensstemmelse med internationale standarder om revision og de yderligere krav, der er gældende i Danmark (ISA). Det kræver, at vi overholder etiske krav, herunder kravene til uafhængighed i revisorloven og FSR – danske revisorers Etiske regler for revisorer, og at vi planlægger og udfører revisionen med professionel skepsis.

Revisionen omfatter bl.a.:

- identifikation og vurdering af risikoen for væsentlig fejlinformation, uanset om den skyldes besvigelser eller fejl, og udformning og udførelse af revisionshandlinger som reaktion på disse risici;
- opnåelse af forståelse af den interne kontrol med relevans for revisionen – ikke med det formål at udtrykke en konklusion om effektiviteten af selskabets interne kontrol;
- vurdering af, om den anvendte regnskabspraksis er passende, og om ledelsens regnskabsmæssige skøn og tilknyttede oplysninger er rimelige;
- konklusion på, om ledelsens udarbejdelse af årsregnskabet på grundlag af regnskabsprincippet om fortsat drift er passende;
- vurdering af den samlede præsentation, struktur og indhold af årsregnskabet, herunder noteoplysningerne.

Revisionen omfatter ikke ledelsesberetningen, men vi læser ledelsesberetningen og afgiver en udtalelse om, hvorvidt den er i overensstemmelse med årsregnskabet og er udarbejdet i overensstemmelse med årsregnskabslovens krav, jf. årsregnskabslovens § 135, stk. 7.

På grund af de iboende begrænsninger ved en revision og ved intern kontrol er der en uundgåelig risiko for, at visse væsentlige fejlinformationer ikke opdages, selv om revisionen er planlagt og udført korrekt. Revisionen tilrettelægges ikke med henblik på at afdække uvæsentlige fejl eller alle besvigelser, og den kan ikke erstatte ledelsens eget tilsyn.

### Særlige forhold i jeres virksomhed

Vi tilrettelægger revisionen ud fra vores forståelse af selskabet og branchen ({{ kunde.branchetekst }}). Vi forventer på det foreliggende grundlag at have særligt fokus på:

{% if branche.lager %}- **Varelager:** Vi vil normalt deltage i eller observere lageroptællingen pr. {{ regnskab.slut }} (ISA 501) og teste opgørelse, kostpris og nedskrivning for ukurante varer. Giv os besked om tidspunktet for optællingen senest en måned før.
{% endif %}{% if branche.igangvaerende_arbejder %}- **Igangværende arbejder og kontraktaktiver:** Opgørelse af færdiggørelsesgrad, forventede tab på kontrakter, periodisering af omsætning og ubehandlede ekstraarbejder.
{% endif %}{% if branche.byggeri %}- **Entreprisekontrakter:** Garantiforpligtelser, sikkerhedsstillelser, tvister og brug af underentreprenører, herunder kontrol af, at fakturaer fra underleverandører svarer til udført arbejde.
{% endif %}{% if branche.investeringsejendomme %}- **Investeringsejendomme:** Grundlaget for måling til dagsværdi eller kostpris, herunder afkastkrav, lejeindtægter, vedligeholdelsesforpligtelser og eventuelle valuarvurderinger.
{% endif %}{% if branche.kontantintensiv %}- **Kontantsalg og kasse:** Fuldstændighed af omsætningen, kasseafstemninger, kasseapparat/kassesystem og sammenhæng mellem indkøb, svind og salg. Kontantintensive brancher har en forhøjet risiko for fejl og besvigelser i omsætningen.
{% endif %}{% if branche.momsfritaget %}- **Moms og lønsumsafgift:** Delvis momsfradrag (pro rata), korrekt opgørelse af lønsumsafgift og afgrænsning mellem momspligtige og momsfritagne aktiviteter.
{% endif %}{% if branche.holding %}- **Kapitalandele og koncerninterne mellemværender:** Måling af kapitalandele i dattervirksomheder, nedskrivningstest, udbytter og eventuelle lån til kapitalejere eller ledelse (forsvarlighed og selskabets interesse, selskabslovens §§ 115 og 127; skattemæssigt ligningslovens § 16 E. De særlige regler i §§ 210-212 er ophævet pr. 1. januar 2025).
{% endif %}{% if branche.finans %}- **Finansielle aktiver:** Værdiansættelse af værdipapirer og andre finansielle instrumenter samt særlige regulatoriske forhold.
{% endif %}{% if branche.forening %}- **Foreningsforhold:** Tilskud, indsamlede midler og vedtægtsbestemte krav til anvendelse af midler.
{% endif %}- Omsætningens fuldstændighed og periodisering, nærtstående parter, ledelsens skøn samt efterfølgende begivenheder.

## 2. Ledelsens ansvar

Revisionen udføres på det grundlag, at {{ kunde.ledelsesorgan }} anerkender og forstår at have ansvaret for:

1. at udarbejde et årsregnskab, der giver et retvisende billede i overensstemmelse med årsregnskabsloven, samt en ledelsesberetning, der opfylder lovens krav;
2. den interne kontrol, som ledelsen anser for nødvendig for at udarbejde et årsregnskab uden væsentlig fejlinformation, uanset om denne skyldes besvigelser eller fejl;
3. at bogføringen sker i overensstemmelse med bogføringsloven, herunder at transaktioner registreres løbende, at regnskabsmateriale opbevares i 5 år fra udgangen af regnskabsåret (bogføringslovens § 12), og at der anvendes et digitalt bogføringssystem, når loven kræver det;
4. at vurdere selskabets evne til at fortsætte driften og oplyse om forhold herom;
5. at give os:
   - adgang til alle oplysninger, som ledelsen er bekendt med, og som er relevante for udarbejdelsen af årsregnskabet, fx bogføring, bilag, kontrakter, protokoller og korrespondance;
   - de yderligere oplysninger, som vi måtte anmode om til brug for revisionen;
   - ubegrænset adgang til personer i selskabet, som vi finder det nødvendigt at indhente revisionsbevis fra.

Som en del af revisionen vil vi bede {{ kunde.ledelsesorgan }} om en skriftlig bekræftelse (ledelseserklæring) af de oplysninger, der er givet til os, jf. ISA 580. Ledelseserklæringen er et nødvendigt revisionsbevis.

Ledelsen skal oplyse os om alle kendte eller formodede besvigelser, overtrædelser af love og regler, transaktioner med nærtstående parter og begivenheder efter balancedagen, der kan have betydning for årsregnskabet.

## 3. Rapportering

Vi afgiver en revisionspåtegning på årsregnskabet. Formen og indholdet af påtegningen kan blive ændret, hvis vi under revisionen finder forhold, der giver anledning til det, fx forbehold, supplerende oplysninger eller fremhævelse af forhold.

{% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %}Vi rapporterer skriftligt til bestyrelsen om den udførte revision, vores konklusioner og væsentlige forhold konstateret under revisionen, herunder betydelige mangler i den interne kontrol (ISA 260 og ISA 265). Fører vi revisionsprotokol, skal den underskrives af medlemmerne af det øverste ledelsesorgan, jf. selskabslovens § 129. For virksomheder af interesse for offentligheden forelægges revisionsprotokollatet efter forordning (EU) nr. 537/2014, artikel 11, også for bestyrelsen, jf. revisorlovens § 20.{% else %}Væsentlige forhold konstateret under revisionen, herunder betydelige mangler i den interne kontrol (ISA 265), meddeler vi skriftligt til {{ kunde.ledelsesorgan }}.{% endif %}

Vi kommunikerer med den øverste ledelse om planlagt omfang og tidsplan for revisionen samt betydelige revisionsmæssige forhold, jf. ISA 260.

## 4. Revisors særlige pligter

Indser vi under revisionen, at et eller flere medlemmer af ledelsen begår eller har begået økonomiske forbrydelser i tilknytning til udførelsen af deres hverv, og har vi en begrundet formodning om, at forbrydelsen vedrører betydelige beløb eller i øvrigt er af grov karakter, skal vi straks underrette hvert enkelt medlem af ledelsen. Har ledelsen ikke senest 14 dage herefter over for os dokumenteret at have taget de fornødne skridt til at standse igangværende kriminalitet og rette op på skaderne, skal vi straks underrette National Enhed for Særlig Kriminalitet, jf. revisorlovens § 22. Bestemmelsen gælder ikke forhold, der er omfattet af hvidvaskloven.

Vi er omfattet af hvidvaskloven og skal derfor gennemføre kundekendskabsprocedurer og løbende overvåge kundeforholdet. Vi vil derfor bede om legitimation og oplysninger om selskabets ejere, reelle ejere, ledelse og forretningsforbindelsens formål. Hvis vi får mistanke om hvidvask eller finansiering af terrorisme, har vi pligt til at underrette Hvidvasksekretariatet, og vi må ikke oplyse om underretningen.

Vores arbejdspapirer tilhører {{ firma.navn }}, opbevares i 5 år (revisorlovens § 23) og kan indgå i den kvalitetskontrol, som revisionsvirksomheden har pligt til at underkaste sig (revisorlovens § 29), og i Erhvervsstyrelsens tilsyn med revisorer.

## 5. Revisors hverv og fratræden

Revisors hverv består, indtil en ny revisor er tiltrådt, jf. revisorlovens § 18, stk. 1. Vi kan fratræde hvervet, hvis fratræden ikke strider mod god revisorskik, jf. revisorlovens § 18, stk. 2. Fratræder vi før valgperiodens udløb, giver vi meddelelse herom til Erhvervsstyrelsen med en fyldestgørende forklaring, jf. selskabslovens § 146, stk. 2. Ved revisorskifte har en ny revisor pligt til at rette henvendelse til os, og vi har pligt til at oplyse grundene til vores fratræden og give adgang til alle relevante oplysninger, jf. revisorlovens § 18, stk. 2.

## 6. Tidsplan og materiale

Vi forventer at modtage det samlede regnskabsmateriale, herunder afstemt bogføring, saldobalance og specifikationer, senest {{ felt.materiale_dato }}. Årsrapporten skal være modtaget i Erhvervsstyrelsen senest {{ regnskab.frist_aarsrapport }}. Vi fremsender en materialeliste forud for årsafslutningen.

## 7. Honorar og fakturering

Honoraret for revisionen udgør {{ felt.honorar }} kr. ekskl. moms ({{ felt.honorar_type }}). Honoraret forudsætter, at materialet foreligger rettidigt og i aftalt kvalitet, og at der ikke konstateres usædvanlige forhold. Ekstraarbejde, som skyldes mangelfuldt materiale, væsentlige fejl, ændrede forhold eller ønsker om yderligere ydelser, afregnes efter medgået tid til {{ felt.timepris }} kr. pr. time ekskl. moms. Vi orienterer jer, inden ekstraarbejde af væsentligt omfang igangsættes.

Fakturering sker {{ felt.fakturering }} med betalingsfrist {{ felt.betalingsfrist }} dage.

{% if felt.andre_ydelser %}Ud over revisionen er der aftalt følgende ydelser, som er omfattet af særskilte vilkår eller afregnes særskilt:

{{ felt.andre_ydelser }}

Vi har vurderet, at ydelserne kan leveres uden at true vores uafhængighed, jf. revisorlovens § 24.{% endif %}

## 8. Ansvar og øvrige vilkår

Vores ansvar er begrænset til {{ felt.ansvarsbegraensning }} pr. opgave. Ansvarsbegrænsningen gælder ikke ved forsæt eller grov uagtsomhed. Vi er ikke ansvarlige for indirekte tab, herunder driftstab, tab af data, avance eller goodwill. Revisorerne i {{ firma.navn }} er forsikret mod økonomiske krav i forbindelse med erklæringsopgaver, som revisorloven kræver (revisorlovens § 3, stk. 1, nr. 7).

Krav mod {{ firma.navn }} kan alene rettes mod revisionsvirksomheden og ikke mod den enkelte medarbejder eller revisor personligt, i det omfang lovgivningen tillader det.

Vi behandler personoplysninger som selvstændig dataansvarlig til brug for revisionen og for at opfylde vores lovpligtige forpligtelser (revisorloven, hvidvaskloven, bogføringsloven). Læs mere i vores privatlivspolitik.

Klager over, at revisor har tilsidesat sine pligter ved erklæringsopgaver, kan indbringes for Revisornævnet (revisorlovens § 43, stk. 3). Tvister afgøres efter dansk ret ved de almindelige domstole med vores hjemting som værneting.

Opgaven udføres i øvrigt efter vores almindelige forretningsbetingelser, som er vedlagt. Ved uoverensstemmelse går dette opdragsbrev forud.

## 9. Accept

Vi beder jer bekræfte opdragsbrevet ved at underskrive og returnere en kopi. Kontakt os gerne, hvis noget er uklart.

Med venlig hilsen

{{ firma.navn }}

&nbsp;

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}

&nbsp;

**Accepteret på vegne af {{ kunde.navn }}**

Dato: ________________

______________________________ ______________________________
{% if kunde.selskabsform_kode == "as" %}Bestyrelsens formand Administrerende direktør{% else %}Direktion{% endif %}
