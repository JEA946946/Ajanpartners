---
{
  "title": "Følgebrev – selvangivelse og årsopgørelse",
  "description": "Følgebrev ved indberetning af selskabets selvangivelse eller den personlige udvidede selvangivelse, med skatteberegning, betaling af restskat og kontrol af årsopgørelsen.",
  "kind": "brev",
  "references": ["Skattekontrolloven (selvangivelse og oplysningsskema)", "Skatteforvaltningsloven § 26 (genoptagelse)", "Selskabsskatteloven §§ 29 A ff.", "Virksomhedsskatteloven"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "indkomstaar", "label": "Indkomstår", "type": "text", "default": "{{ regnskab.aar }}"},
    {"name": "skattepligtig_indkomst", "label": "Skattepligtig indkomst (kr.)", "type": "number"},
    {"name": "skat", "label": "Beregnet skat (kr.)", "type": "number"},
    {"name": "indbetalt", "label": "Indbetalt aconto/B-skat (kr.)", "type": "number"},
    {"name": "rest_eller_overskydende", "label": "Restskat (+) / overskydende skat (-) (kr.)", "type": "number"},
    {"name": "betalingsfrist", "label": "Betalingsfrist for restskat", "type": "text"},
    {"name": "indberettet_dato", "label": "Indberettet den", "type": "date"},
    {"name": "virksomhedsordning", "label": "Virksomhedsordningen er anvendt", "type": "checkbox"},
    {"name": "opsparet_overskud", "label": "Opsparet overskud ultimo (kr.)", "type": "number"},
    {"name": "bemaerkninger", "label": "Særlige forhold/rådgivning", "type": "textarea"}
  ]
}
---
{{ kunde.navn }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# {% if kunde.er_kapitalselskab %}Selvangivelse for selskabet{% else %}Selvangivelse og årsopgørelse{% endif %} – indkomståret {{ felt.indkomstaar }}

Kære {{ kunde.navn }}

{% if felt.indberettet_dato %}Vi har den {{ felt.indberettet_dato }} indberettet {% else %}Vi har udarbejdet {% endif %}{% if kunde.er_kapitalselskab %}selskabets selvangivelse{% else %}jeres oplysningsskema (udvidet selvangivelse){% endif %} for indkomståret {{ felt.indkomstaar }} på grundlag af {% if kunde.er_kapitalselskab %}årsrapporten{% else %}årsregnskabet{% endif %} og de oplysninger, I har givet os.

## Skatteberegning
| | Beløb |
|---|---|
| Skattepligtig indkomst | {{ felt.skattepligtig_indkomst }} |
| Beregnet skat | {{ felt.skat }} |
| Indbetalt {% if kunde.er_kapitalselskab %}acontoskat{% else %}B-skat/forskudsskat{% endif %} | {{ felt.indbetalt }} |
| **Restskat (+) / overskydende skat (−)** | **{{ felt.rest_eller_overskydende }}** |

{% if kunde.er_kapitalselskab %}Restskat betales via skattekontoen senest **{{ felt.betalingsfrist }}** og tillægges et restskattetillæg. Overskydende skat udbetales med godtgørelse. Indgår selskabet i en sambeskatning, afregnes skatten via administrationsselskabet.{% else %}Restskat betales via jeres personlige skat. Mindre restskatter indregnes automatisk i forskudsskatten for et senere år; større restskatter opkræves i rater. Betalingsfrist: {{ felt.betalingsfrist }}.
{% if felt.virksomhedsordning %}
**Virksomhedsordningen:** Der er anvendt virksomhedsordningen. Opsparet overskud ultimo udgør {{ felt.opsparet_overskud }} kr. Husk, at hævninger følger den lovbestemte hæverækkefølge, og at private udgifter betalt af virksomhedens midler behandles som hævninger.
{% endif %}{% endif %}

## Det skal I gøre
1. **Kontrollér årsopgørelsen,** når den kommer i TastSelv/e-Boks. Sammenhold den med beregningen ovenfor og giv os besked, hvis der er afvigelser.
2. {% if kunde.er_kapitalselskab %}Kontrollér acontoskatten for det kommende år og overvej frivillig indbetaling, hvis resultatet forventes at blive højere end gennemsnittet.{% else %}Tilret forskudsopgørelsen for indeværende år, hvis jeres indkomst ændrer sig væsentligt.{% endif %}
3. **Gem dokumentationen.** Skattestyrelsen kan som udgangspunkt genoptage en ansættelse indtil 1. maj i det 4. år efter indkomstårets udløb (for personer med enkle forhold kortere frist), og regnskabsmaterialet skal opbevares i 5 år.

{% if felt.bemaerkninger %}## Særlige forhold
{{ felt.bemaerkninger }}
{% endif %}
Kontakt {{ kunde.ansvarlig }}, hvis I har spørgsmål.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
