---
{
  "title": "Rykker for manglende materiale",
  "description": "Venlig, men tydelig rykker for materiale, med liste over manglende punkter, ny frist og konsekvenser ved fortsat manglende levering. Tre trin.",
  "kind": "brev",
  "references": ["Årsregnskabsloven §§ 138, 150-151", "Skatteforvaltningsloven/skattekontrolloven (skønsmæssig ansættelse)"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "trin", "label": "Rykkertrin", "type": "select", "options": ["1. rykker", "2. rykker", "Sidste rykker"], "default": "1. rykker"},
    {"name": "oprindelig_frist", "label": "Oprindelig frist", "type": "date"},
    {"name": "ny_frist", "label": "Ny frist", "type": "date"},
    {"name": "mangler", "label": "Manglende materiale (ét punkt pr. linje)", "type": "textarea"},
    {"name": "ekstra_honorar", "label": "Oplys om ekstra honorar ved forsinkelse", "type": "checkbox"}
  ]
}
---
{{ kunde.navn }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# {{ felt.trin }}: Manglende materiale til årsafslutning {{ regnskab.aar }}

Kære {{ kunde.navn }}

{% if felt.trin == "1. rykker" %}Vi skrev tidligere til jer om materiale til årsafslutningen med frist den {{ felt.oprindelig_frist }}. Vi har endnu ikke modtaget alt, og vi vil gerne sikre, at vi kan nå arbejdet i god tid.{% elif felt.trin == "2. rykker" %}Vi har tidligere rykket for materiale til årsafslutningen (oprindelig frist {{ felt.oprindelig_frist }}). Vi mangler fortsat nedenstående, og tidsplanen er nu presset.{% else %}Trods tidligere henvendelser mangler vi fortsat materiale til årsafslutningen (oprindelig frist {{ felt.oprindelig_frist }}). Dette er vores sidste rykker, før fristerne kommer i fare.{% endif %}

## Vi mangler
{{ felt.mangler }}

Vi beder jer sende materialet senest **{{ felt.ny_frist }}** – helst ved upload i bogføringsprogrammet.

{% if felt.trin != "1. rykker" %}## Hvad sker der, hvis fristen ikke nås?
{% if kunde.er_kapitalselskab %}- Årsrapporten skal være modtaget i Erhvervsstyrelsen senest **{{ regnskab.frist_aarsrapport }}**. Ved overskridelse sender Erhvervsstyrelsen et påkrav, og derefter pålægges hvert ledelsesmedlem en personlig afgift. Indsendes årsrapporten fortsat ikke, kan styrelsen anmode skifteretten om tvangsopløsning af selskabet.
- Selskabets selvangivelse skal indberettes senest 6 måneder efter regnskabsårets udløb. Ellers kan Skattestyrelsen pålægge skattetillæg og ansætte indkomsten skønsmæssigt.
{% else %}- Den udvidede selvangivelse skal være indberettet senest 1. juli. Ved overskridelse kan Skattestyrelsen pålægge skattetillæg og ansætte indkomsten skønsmæssigt.
{% endif %}- Vi kan ikke afgive vores erklæring, før vi har modtaget tilstrækkeligt materiale.
{% endif %}{% if felt.ekstra_honorar %}
Bemærk, at ekstraarbejde som følge af forsinket eller ufuldstændigt materiale faktureres efter medgået tid, jf. vores aftale.
{% endif %}
Er der forhold, der gør det svært at fremskaffe materialet, så ring til {{ kunde.ansvarlig }} – så finder vi en løsning sammen.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
