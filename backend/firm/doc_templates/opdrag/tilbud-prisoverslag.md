---
{
  "title": "Tilbud og prisoverslag",
  "description": "Tilbud til ny eller eksisterende kunde på revision/erklæring, bogføring, løn, moms og skat med prisoverslag, forudsætninger og næste skridt.",
  "kind": "brev",
  "references": ["Revisorloven § 16 (god revisorskik)", "FSR – danske revisorers Etiske regler (honorarer, afsnit 330 og 410)", "Hvidvaskloven § 11"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "kontaktperson", "label": "Kontaktperson hos kunden", "type": "text"},
    {"name": "erklaeringstype", "label": "Erklæring på årsregnskabet", "type": "select", "options": ["Revision", "Udvidet gennemgang", "Review", "Opstilling", "Ingen erklæring"], "default": "Opstilling"},
    {"name": "pris_erklaering", "label": "Pris for årsregnskab og erklæring (kr. ekskl. moms)", "type": "number"},
    {"name": "pris_bogfoering", "label": "Pris for bogføring pr. måned (kr. ekskl. moms, 0 hvis ikke omfattet)", "type": "number"},
    {"name": "pris_loen", "label": "Pris pr. lønseddel (kr. ekskl. moms, 0 hvis ikke omfattet)", "type": "number"},
    {"name": "pris_moms", "label": "Pris pr. momsangivelse (kr. ekskl. moms, 0 hvis ikke omfattet)", "type": "number"},
    {"name": "pris_skat", "label": "Pris for selvangivelse (kr. ekskl. moms, 0 hvis ikke omfattet)", "type": "number"},
    {"name": "pris_opstart", "label": "Engangspris for opstart/overtagelse (kr. ekskl. moms)", "type": "number"},
    {"name": "timepris", "label": "Timepris for øvrigt arbejde (kr. ekskl. moms)", "type": "number"},
    {"name": "antal_bilag", "label": "Forudsat antal bilag pr. år", "type": "number"},
    {"name": "antal_ansatte", "label": "Forudsat antal ansatte", "type": "number"},
    {"name": "gyldighed", "label": "Tilbuddet gælder til", "type": "date"},
    {"name": "saerlige_forhold", "label": "Særlige forhold/forbehold", "type": "textarea"}
  ]
}
---
**{{ kunde.navn }}**
{% if felt.kontaktperson %}Att.: {{ felt.kontaktperson }}{% endif %}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Tilbud på regnskabs- og revisionsydelser

Tak for en god snak om {{ kunde.navn }}. Som aftalt sender vi her vores tilbud. Vi har lagt vægt på en fast pris, så I på forhånd ved, hvad det koster, og på et digitalt samarbejde, hvor I selv kan følge med i bogføringen i vores bogføringsprogram, som er gratis for vores kunder.

## 1. Vores forståelse af jeres virksomhed

{{ kunde.navn }} driver virksomhed inden for {{ kunde.branchetekst }}. Tilbuddet bygger på ca. {{ felt.antal_bilag }} bilag om året, ca. {{ felt.antal_ansatte }} ansatte og momsperiode: {{ kunde.momsperiode }}.

{% if branche.restauration %}Restaurationsbranchen har særlige krav til kassesystem, dagsopgørelser, drikkepenge og løn til timelønnede. Vi kender kravene og hjælper jer med at få styr på dem fra start.{% elif branche.byggeri %}I byggebranchen er der særlige regler om omvendt betalingspligt for moms, kontrol af underleverandører og opgørelse af igangværende arbejder. Vi har erfaring med branchen og hjælper jer med de faste rutiner.{% elif branche.ejendom %}Ved udlejning af fast ejendom har vi fokus på lejeregnskab, deposita, moms ved erhvervsudlejning og skattemæssige afskrivninger.{% elif branche.holding %}For holdingselskaber har vi fokus på kapitalandele, udbytter, sambeskatning og eventuelle mellemregninger med ejeren.{% elif branche.kontantintensiv %}Da I har kontantomsætning, sætter vi rutiner op for kasseafstemning og dagsopgørelser.{% endif %}

## 2. Ydelser og pris

| Ydelse | Pris ekskl. moms |
|---|---|
| Årsregnskab (erklæring: {{ felt.erklaeringstype }}){% if kunde.er_kapitalselskab %} og indberetning af årsrapport til Erhvervsstyrelsen{% endif %} | {{ felt.pris_erklaering }} kr. pr. år |
| Løbende bogføring og afstemning | {{ felt.pris_bogfoering }} kr. pr. måned |
| Lønadministration inkl. eIndkomst | {{ felt.pris_loen }} kr. pr. lønseddel |
| Momsangivelse | {{ felt.pris_moms }} kr. pr. angivelse |
| {% if kunde.er_kapitalselskab %}Selskabets selvangivelse{% else %}Selvangivelse for ejeren{% endif %} | {{ felt.pris_skat }} kr. pr. år |
| Opstart, overtagelse af data og opsætning af bogføringsprogram | {{ felt.pris_opstart }} kr. (engangsbeløb) |
| Øvrig rådgivning efter aftale | {{ felt.timepris }} kr. pr. time |

Ydelser med pris 0 er ikke omfattet af tilbuddet.

{% if branche.restauration or branche.rengoering or branche.transport or branche.it or branche.personlig_service or branche.bilhandel %}**Bemærk:** Jeres branche kan være en klassificeret risikobranche (årsregnskabslovens § 135, stk. 5). Har I en nettoomsætning over 5 mio. kr. i to år i træk, skal årsregnskabet mindst have en opstillingserklæring fra en uafhængig revisor. Det er indregnet i tilbuddet, hvis erklæringstypen ovenfor er opstilling eller derover.{% endif %}

## 3. Forudsætninger

- Bilag uploades løbende og senest 8 dage efter hver måneds udløb.
- Bankkonti tilknyttes bogføringsprogrammet, så kontoudtog hentes automatisk.
- Antal bilag og ansatte svarer nogenlunde til forudsætningerne ovenfor. Ved væsentlige ændringer tager vi en snak om prisen.
- Ekstraarbejde som følge af mangelfuldt materiale, oprydning i tidligere år eller myndighedssager afregnes efter tid efter forudgående aftale.
- Priserne reguleres en gang årligt pr. 1. januar.
{% if felt.saerlige_forhold %}- {{ felt.saerlige_forhold }}{% endif %}

## 4. Næste skridt

Hvis I vil tage imod tilbuddet, skal vi efter hvidvaskloven have legitimation og oplysninger om ejere og ledelse, før vi kan gå i gang. Vi sender et oplysningsskema og derefter et opdragsbrev/en aftale med de endelige vilkår til underskrift. Endelig accept forudsætter, at vores sædvanlige procedurer for kundeaccept og uafhængighed er gennemført{% if felt.erklaeringstype != "Ingen erklæring" and felt.erklaeringstype != "Opstilling" %}, og at vi har været i kontakt med jeres nuværende revisor, som vi efter revisorloven har pligt til at kontakte{% endif %}.

Tilbuddet gælder til {{ felt.gyldighed }}.

Vi glæder os til samarbejdet.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
{{ firma.telefon }} · {{ firma.email }}
