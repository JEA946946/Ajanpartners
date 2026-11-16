---
{
  "title": "Anbefaling af erklæringstype (revision, udvidet gennemgang, review, opstilling)",
  "description": "Brev til kunden med vurdering af revisionspligt og fravalgsmulighed efter årsregnskabslovens § 135 (størrelsesgrænser, 50 mio.-grænsen, holdingreglen, risikobrancher) og vores anbefaling af erklæringstype, inkl. hvordan fravalg besluttes.",
  "kind": "brev",
  "references": ["Årsregnskabsloven § 7 og § 135, stk. 1-6", "Årsregnskabsloven § 135 a", "Bekendtgørelse nr. 1488 af 27/11/2025 om klassificerede risikobrancher", "Erhvervsstyrelsens erklæringsstandard for små virksomheder (Udvidet gennemgang af årsregnskaber), bilag 1 til BEK nr. 518 af 24/05/2024", "ISRE 2400", "ISRS 4410", "Selskabsloven §§ 106 og 144-146"],
  "legal_forms": ["aps", "as", "ivs", "holding", "pmv", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "aar1", "label": "Første regnskabsår i vurderingen", "type": "text"},
    {"name": "aar2", "label": "Andet regnskabsår i vurderingen", "type": "text", "default": "{{ regnskab.aar }}"},
    {"name": "balance1", "label": "Balancesum år 1 (kr.)", "type": "text"},
    {"name": "balance2", "label": "Balancesum år 2 (kr.)", "type": "text", "default": "{{ regnskab.balancesum }}"},
    {"name": "omsaetning1", "label": "Nettoomsætning år 1 (kr.)", "type": "text"},
    {"name": "omsaetning2", "label": "Nettoomsætning år 2 (kr.)", "type": "text", "default": "{{ regnskab.omsaetning }}"},
    {"name": "ansatte1", "label": "Gns. antal heltidsansatte år 1", "type": "text"},
    {"name": "ansatte2", "label": "Gns. antal heltidsansatte år 2", "type": "text"},
    {"name": "kan_fravaelge", "label": "Vores vurdering af revisionspligt", "type": "select", "options": ["Selskabet kan fravælge revision", "Selskabet kan ikke fravælge revision, men kan vælge udvidet gennemgang", "Selskabet skal revideres (klasse C, holdingreglen efter klasse B-grænserne eller afgørelse efter § 135 a, stk. 3)"], "default": "Selskabet kan fravælge revision"},
    {"name": "risikobranche", "label": "Hovedbranchekoden er en klassificeret risikobranche (BEK 1488/2025 – udfyldes automatisk ud fra kundens branchekode)", "type": "checkbox", "default": "{% if branche.risikobranche %}true{% endif %}"},
    {"name": "koncern", "label": "Selskabet har dattervirksomheder/kapitalinteresser med betydelig indflydelse", "type": "checkbox", "default": false},
    {"name": "anbefaling", "label": "Vores anbefaling", "type": "select", "options": ["Revision", "Udvidet gennemgang", "Review", "Opstilling", "Ingen erklæring"], "default": "Opstilling"},
    {"name": "begrundelse", "label": "Begrundelse for anbefalingen (bank, kreditorer, ejere, intern kontrol)", "type": "textarea"},
    {"name": "pris_revision", "label": "Vejledende pris – revision (kr.)", "type": "number"},
    {"name": "pris_udvidet", "label": "Vejledende pris – udvidet gennemgang (kr.)", "type": "number"},
    {"name": "pris_review", "label": "Vejledende pris – review (kr.)", "type": "number"},
    {"name": "pris_opstilling", "label": "Vejledende pris – opstilling (kr.)", "type": "number"}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Valg af erklæring på årsregnskabet – vores anbefaling

I har bedt os vurdere, hvilken erklæring {{ kunde.navn }} skal eller bør have på årsregnskabet. Nedenfor gennemgår vi reglerne, jeres tal og vores anbefaling.

## 1. Reglerne i årsregnskabslovens § 135

**Hovedregel:** Virksomheder i regnskabsklasse B, C og D skal lade årsregnskabet revidere.

**Fravalg af revision:** En virksomhed i regnskabsklasse B kan fravælge revision, hvis den i to på hinanden følgende regnskabsår på balancedagen **ikke overskrider to** af følgende grænser (§ 135, stk. 1):

| Grænse | Beløb |
|---|---|
| Balancesum | 4 mio. kr. |
| Nettoomsætning | 8 mio. kr. |
| Gennemsnitligt antal heltidsbeskæftigede | 12 |

**Undtagelser – fravalg er ikke muligt, hvis:**

- balancesummen overstiger **50 mio. kr.** i to på hinanden følgende regnskabsår (§ 135, stk. 2) – udvidet gennemgang er dog fortsat mulig;
- virksomheden besidder kapitalinteresser i og udøver betydelig indflydelse på andre virksomheder, og virksomhederne tilsammen i to på hinanden følgende regnskabsår overskrider to af de tre fravalgsgrænser ovenfor (holdingreglen, § 135, stk. 4, jf. § 110). Overskrider de tilsammen to af størrelsesgrænserne for regnskabsklasse B (§ 7, stk. 2, nr. 1), er heller ikke udvidet gennemgang muligt;
- virksomheden er en erhvervsdrivende fond eller et medarbejderinvesteringsselskab (§ 135, stk. 3);
- virksomheden, en tilknyttet virksomhed eller den, der har bestemmende indflydelse over den, har vedtaget bødeforelæg eller er dømt for overtrædelse af selskabs-, regnskabs-, hvidvask- eller skatte- og afgiftslovgivningen – for det regnskabsår, hvor dommen/bødeforelægget er endeligt, og de 2 følgende år (§ 135 a, stk. 1);
- et nyt ledelsesmedlem har været pålagt konkurskarantæne inden for de seneste 2 år før sin indtræden (§ 135 a, stk. 2);
- Erhvervsstyrelsen har efter en kontrol truffet afgørelse om, at hverken fravalg eller udvidet gennemgang kan anvendes for det indeværende og de 2 følgende regnskabsår (§ 135 a, stk. 3).

**Udvidet gennemgang:** Revisionspligtige virksomheder i regnskabsklasse B kan i stedet for revision vælge udvidet gennemgang efter Erhvervsstyrelsens erklæringsstandard for små virksomheder (§ 135, stk. 1, 2. pkt.), medmindre undtagelserne i § 135, stk. 3 eller 4 (klasse B-grænserne), eller § 135 a, stk. 3, gælder.

**Risikobrancher:** Har virksomheden fravalgt revision, men har den en hovedbranchekode, der er klassificeret som risikobranche (bekendtgørelse nr. 1488 af 27. november 2025, gældende for regnskabsår, der begynder 1. januar 2025 eller senere), og overstiger nettoomsætningen **5 mio. kr.** i to på hinanden følgende år, skal årsregnskabet forsynes med en **erklæring om assistance med opstilling** fra en uafhængig revisor eller en revisorerklæring med sikkerhed (§ 135, stk. 5). Hovedbranchekoden i CVR på balancedagen er afgørende. Følgende branchekoder er klassificeret (BEK nr. 1488/2025, § 1): 494100 vejgodstransport, 494200 flytteaktiviteter, 561110 restauranter og caféer, 561190 øvrige spisesteder, 562100 event catering, 562200 catering på kontrakt m.v., 563010 og 563020 udskænkning af drikkevarer, 639100 drift af portaler til internettet, 811000 kombinerede hjælpetjenester i forbindelse med drift af fast ejendom, 812100 almindelig rengøring i bygninger, 812210 vinduespolering, 812290 anden rengøring af bygninger og erhvervslokaler, 812300 anden rengøring og 962200 skønhedspleje og anden skønhedsbehandling.

Virksomheder i regnskabsklasse C og D kan hverken fravælge revision eller vælge udvidet gennemgang (§ 135, stk. 1).

## 2. Jeres tal

| | {{ felt.aar1 }} | {{ felt.aar2 }} | Grænse |
|---|---|---|---|
| Balancesum | {{ felt.balance1 }} | {{ felt.balance2 }} | 4 mio. kr. (50 mio. kr.) |
| Nettoomsætning | {{ felt.omsaetning1 }} | {{ felt.omsaetning2 }} | 8 mio. kr. (5 mio. kr. for risikobrancher) |
| Heltidsansatte | {{ felt.ansatte1 }} | {{ felt.ansatte2 }} | 12 |

Regnskabsklasse: {{ kunde.regnskabsklasse }} · Branche: {{ kunde.branchekode }} {{ kunde.branchetekst }}

**Vores vurdering:** {{ felt.kan_fravaelge }}.

{% if felt.koncern %}Selskabet har kapitalinteresser i andre virksomheder. Vi har derfor også opgjort grænserne for selskabet og dets dattervirksomheder samlet efter § 135, stk. 4, og årsregnskabslovens § 110.{% endif %}

{% if felt.risikobranche %}Selskabets hovedbranchekode {{ kunde.branchekode }} er klassificeret som risikobranche. Overstiger nettoomsætningen 5 mio. kr. i to år i træk, skal årsregnskabet som minimum have en opstillingserklæring, selv om revisionen er fravalgt. Bemærk, at klassifikationen gælder for to år ad gangen og derefter opdateres.{% elif branche.restauration or branche.rengoering or branche.transport or branche.it or branche.personlig_service or branche.udlejning_service %}Selskabets branche kan være omfattet af listen over klassificerede risikobrancher ovenfor. Vi kontrollerer den præcise hovedbranchekode mod bekendtgørelsen, inden der træffes beslutning.{% endif %}

## 3. Erklæringstyperne

| Erklæring | Sikkerhed | Hvad får I | Vejledende pris |
|---|---|---|---|
| **Revision** (ISA) | Høj grad af sikkerhed | Den mest omfattende kontrol. Bedste signalværdi over for bank, kreditorer og investorer. Revisor er valgt til hvervet, indtil ny revisor tiltræder. | {{ felt.pris_revision }} kr. |
| **Udvidet gennemgang** | Begrænset sikkerhed og yderligere sikkerhed fra supplerende handlinger; konklusion i positiv form | Billigere end revision, men stadig en erklæring med sikkerhed, der opfylder revisionspligten for klasse B. | {{ felt.pris_udvidet }} kr. |
| **Review** (ISRE 2400) | Begrænset sikkerhed | Frivillig erklæring for virksomheder uden revisionspligt; forespørgsler og analyser. Opfylder risikobranchekravet. | {{ felt.pris_review }} kr. |
| **Opstilling** (ISRS 4410) | Ingen sikkerhed | Vi opstiller regnskabet efter loven på grundlag af jeres oplysninger. Opfylder risikobranchekravet, hvis revisor er uafhængig. | {{ felt.pris_opstilling }} kr. |
| **Ingen erklæring** | – | Ledelsen udarbejder selv årsrapporten. | – |

Uanset erklæringstype har ledelsen ansvaret for bogføring, regnskab og indsendelse af årsrapporten. Fravælges revisionen, falder den løbende kontrol bort, som revisor ellers udfører, og risikoen for fejl i bogføring og skatteopgørelse samt for uforsvarlige lån til kapitalejere (og deres skattemæssige konsekvenser efter LL § 16 E) opdages senere eller slet ikke.

## 4. Vores anbefaling

Vi anbefaler: **{{ felt.anbefaling }}**.

{{ felt.begrundelse }}

{% if felt.anbefaling == "Opstilling" or felt.anbefaling == "Review" or felt.anbefaling == "Ingen erklæring" %}
## 5. Sådan fravælger I revisionen

1. Beslutningen om fravalg træffes af generalforsamlingen{% if kunde.selskabsform_kode == "as" %} – i et A/S skal vedtægterne også gennemgås for bestemmelser om revision og revisionsudvalg{% endif %}. Indeholder vedtægterne krav om revision, skal de ændres med mindst 2/3 af de afgivne stemmer og af den repræsenterede kapital (selskabslovens § 106).
2. Beslutningen og fratræden af den nuværende revisor anmeldes til Erhvervsstyrelsen.
3. Fravalget gælder, indtil betingelserne ikke længere er opfyldt. Vi følger tallene hvert år og giver jer besked, hvis selskabet bliver revisionspligtigt igen, eller hvis risikobranchekravet indtræder.
4. Bemærk, at en bank eller andre kreditorer kan stille krav om en erklæring med sikkerhed i låneaftalen.

Vi udarbejder gerne referat af generalforsamlingen og anmeldelsen til Erhvervsstyrelsen.
{% endif %}

Kontakt os, hvis I vil drøfte anbefalingen.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
