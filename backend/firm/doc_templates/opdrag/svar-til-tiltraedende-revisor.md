---
{
  "title": "Svar til tiltrædende revisor",
  "description": "Fratrædende revisors svar på henvendelse efter revisorlovens § 18, stk. 2: grunde til fratræden, relevante forhold og udlevering af oplysninger.",
  "kind": "brev",
  "references": ["Revisorloven § 18, stk. 2", "FSR – danske revisorers Etiske regler (afsnit 320)", "Hvidvaskloven § 38"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "revisor_titel", "label": "Underskrivende revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "ny_firma", "label": "Tiltrædende revisionsvirksomhed", "type": "text"},
    {"name": "ny_revisor", "label": "Tiltrædende revisor (navn)", "type": "text"},
    {"name": "henvendelse_dato", "label": "Dato for henvendelsen", "type": "date"},
    {"name": "grund", "label": "Grund til fratræden", "type": "select", "options": ["Selskabet har valgt en anden revisor (ingen faglige grunde)", "Selskabet har fravalgt revision", "Vi har valgt at fratræde – se forhold nedenfor", "Uenighed om regnskabsmæssige forhold – se nedenfor", "Ubetalte honorarer"], "default": "Selskabet har valgt en anden revisor (ingen faglige grunde)"},
    {"name": "forhold", "label": "Forhold af betydning for den tiltrædende revisor", "type": "textarea"},
    {"name": "materiale", "label": "Materiale der udleveres", "type": "textarea", "default": "Seneste årsrapport med erklæring\nRevisionsprotokol/ledelsesbreve\nSpecifikationer til åbningsbalancen\nSkatteopgørelse og udskudt skat"}
  ]
}
---
**{{ felt.ny_firma }}**
Att.: {{ felt.ny_revisor }}

{{ dato.idag }}

# Revisorskifte – {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}

Vi bekræfter modtagelsen af jeres henvendelse af {{ felt.henvendelse_dato }} efter revisorlovens § 18, stk. 2.

**Grunde til vores fratræden:** {{ felt.grund }}.

{% if felt.forhold %}**Forhold, som vi finder relevante for jeres overvejelser om at acceptere hvervet:**

{{ felt.forhold }}{% else %}Vi er ikke bekendt med faglige forhold, uenigheder med ledelsen eller andre forhold, som efter vores opfattelse bør indgå i jeres overvejelser om at acceptere hvervet.{% endif %}

Svaret er afgivet på grundlag af vores kendskab til selskabet frem til fratrædelsen. Det udgør ikke en erklæring om selskabets regnskaber eller forhold i øvrigt.

**Adgang til oplysninger:** Med selskabets samtykke stiller vi følgende til rådighed:

{{ felt.materiale }}

Arbejdspapirer kan gennemgås hos os efter aftale. Kopi udleveres i det omfang, det er relevant for jeres arbejde med åbningsbalancen.

Med venlig hilsen

{{ firma.navn }}

&nbsp;

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
