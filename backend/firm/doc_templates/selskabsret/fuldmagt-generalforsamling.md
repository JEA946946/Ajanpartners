---
{
  "title": "Fuldmagt til generalforsamling",
  "description": "Skriftlig og dateret fuldmagt for kapitalejer til at møde og stemme på en ordinær eller ekstraordinær generalforsamling, med valgfri stemmeinstruks.",
  "kind": "beslutning",
  "references": ["Selskabsloven § 80", "Selskabsloven § 76"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "fuldmagtsgiver", "label": "Fuldmagtsgiver (kapitalejer – navn, evt. CVR/fødselsdato)", "type": "text"},
    {"name": "fuldmagtsgiver_adresse", "label": "Fuldmagtsgivers adresse", "type": "text"},
    {"name": "kapitalandele", "label": "Kapitalandele (nominelt beløb og stemmer)", "type": "text"},
    {"name": "fuldmaegtig", "label": "Fuldmægtig (navn)", "type": "text"},
    {"name": "fuldmaegtig_til_ledelsen", "label": "Fuldmagten gives til selskabets ledelse/bestyrelsesformand", "type": "checkbox"},
    {"name": "gf_type", "label": "Generalforsamling", "type": "select", "options": ["ordinær", "ekstraordinær"], "default": "ordinær"},
    {"name": "gf_dato", "label": "Dato for generalforsamlingen", "type": "date"},
    {"name": "omfang", "label": "Omfang", "type": "select", "options": ["Efter fuldmægtigens skøn", "Efter stemmeinstruks nedenfor"], "default": "Efter fuldmægtigens skøn"},
    {"name": "stemmeinstruks", "label": "Stemmeinstruks pr. dagsordenspunkt (for/imod/undlader)", "type": "textarea"}
  ]
}
---
# Fuldmagt

Undertegnede

**{{ felt.fuldmagtsgiver }}**
{{ felt.fuldmagtsgiver_adresse }}

der ejer kapitalandele i **{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}, nominelt {{ felt.kapitalandele }},

giver hermed fuldmagt til

**{% if felt.fuldmaegtig_til_ledelsen %}{% if kunde.selskabsform_kode == "as" %}bestyrelsens formand{% else %}selskabets direktion{% endif %} ({{ felt.fuldmaegtig }}){% else %}{{ felt.fuldmaegtig }}{% endif %}**

til at møde og afgive stemme på mine/vores vegne på selskabets {{ felt.gf_type }}e generalforsamling den {{ felt.gf_dato }} og på enhver udsat eller fortsat generalforsamling med samme dagsorden.

{% if felt.omfang == "Efter stemmeinstruks nedenfor" %}
## Stemmeinstruks
Fuldmægtigen skal stemme som følger:

{{ felt.stemmeinstruks }}

For forslag, der ikke er omfattet af instruksen, eller som ændres på generalforsamlingen, stemmer fuldmægtigen efter sit skøn.
{% else %}
Fuldmægtigen er berettiget til at stemme efter sit skøn om alle forslag på dagsordenen, herunder ændringsforslag fremsat på generalforsamlingen, samt til at give afkald på form- og fristkrav til indkaldelsen, jf. selskabslovens § 76, stk. 2.
{% endif %}

Fuldmagten kan til enhver tid tilbagekaldes skriftligt over for selskabet, jf. selskabslovens § 80, stk. 2. Fuldmagten gælder kun for den ovennævnte generalforsamling.

Fuldmægtigen skal fremlægge denne fuldmagt på generalforsamlingen, jf. selskabslovens § 80, stk. 1. Fuldmægtigen kan møde sammen med en rådgiver, jf. § 81.

Sted og dato: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.fuldmagtsgiver }}
*(Er kapitalejeren en juridisk person, underskrives fuldmagten i overensstemmelse med dennes tegningsregel.)*
