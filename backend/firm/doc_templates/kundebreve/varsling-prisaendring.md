---
{
  "title": "Varsling af prisændring",
  "description": "Varsel til kunden om ændrede honorarer/timepriser med ikrafttræden, begrundelse, nye priser og kundens ret til at opsige efter aftalen.",
  "kind": "brev",
  "references": ["Kundeaftalen/opdragsbrevet", "Aftaleloven", "Markedsføringsloven § 3 (god skik)"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "ikrafttraedelse", "label": "Ny pris gælder fra", "type": "date"},
    {"name": "varsel", "label": "Varsel efter aftalen", "type": "select", "options": ["1 måned", "2 måneder", "3 måneder"], "default": "3 måneder"},
    {"name": "begrundelse", "label": "Begrundelse", "type": "textarea", "default": "Prisændringen afspejler den almindelige pris- og lønudvikling samt øgede krav fra myndighederne til dokumentation og kvalitetssikring."},
    {"name": "prisoversigt", "label": "Prisoversigt (ydelse – nuværende – ny pris)", "type": "textarea"},
    {"name": "procent", "label": "Gennemsnitlig ændring (%)", "type": "number"},
    {"name": "fast_honorar", "label": "Kunden har fast honorar", "type": "checkbox"},
    {"name": "nyt_fast_honorar", "label": "Nyt fast honorar (kr. pr. måned/år ekskl. moms)", "type": "text"}
  ]
}
---
{{ kunde.navn }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Varsling af prisændring pr. {{ felt.ikrafttraedelse }}

Kære {{ kunde.navn }}

Med dette brev varsler vi, at vores priser ændres med virkning fra den **{{ felt.ikrafttraedelse }}**, jf. vores aftale{% if kunde.aftalereference %} ({{ kunde.aftalereference }}){% endif %}, der giver os ret til at regulere priserne med et skriftligt varsel på {{ felt.varsel }}.

{{ felt.begrundelse }}

{% if felt.fast_honorar %}## Jeres faste honorar
Jeres faste honorar ændres fra {{ felt.ikrafttraedelse }} til **{{ felt.nyt_fast_honorar }}** ekskl. moms. Honoraret dækker fortsat de ydelser, der er beskrevet i aftalen. Ydelser uden for aftalen faktureres efter medgået tid til de nye timepriser.
{% else %}## Nye priser
{{ felt.prisoversigt }}

Den gennemsnitlige ændring udgør ca. {{ felt.procent }} %. Alle priser er ekskl. moms.
{% endif %}
Brugen af vores bogføringsprogram er fortsat gratis for jer.

Opgaver, der er påbegyndt før {{ felt.ikrafttraedelse }}, og opgaver med en skriftligt aftalt fast pris, afregnes efter de hidtidige priser.

Ønsker I ikke at fortsætte samarbejdet på de nye vilkår, kan I opsige aftalen efter dens bestemmelser. Hører vi ikke fra jer, fortsætter samarbejdet på de nye priser.

Vi sætter stor pris på samarbejdet og fortæller gerne mere om, hvordan I kan holde omkostningerne nede – fx ved at uploade bilag løbende og bruge bankintegrationen i bogføringsprogrammet. Kontakt {{ kunde.ansvarlig }}, hvis I har spørgsmål.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
