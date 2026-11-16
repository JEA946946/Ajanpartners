---
{
  "title": "Anmodning om materiale til årsafslutning",
  "description": "Følgebrev til materialelisten med frist, tidsplan og forklaring af, hvorfor fristen er vigtig.",
  "kind": "brev",
  "references": ["Årsregnskabsloven §§ 138, 150-151", "Skattekontrolloven § 12", "Bogføringsloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "frist_materiale", "label": "Frist for materiale", "type": "date"},
    {"name": "moede_dato", "label": "Forslag til afslutningsmøde", "type": "text"},
    {"name": "lageroptaelling", "label": "Dato for lageroptælling", "type": "text"}
  ]
}
---
{{ kunde.navn }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Årsafslutning {{ regnskab.aar }} – vi skal bruge jeres materiale

Kære {{ kunde.navn }}

Regnskabsåret slutter den {{ regnskab.slut }}, og vi går nu i gang med at planlægge {% if kunde.er_kapitalselskab %}årsrapporten{% else %}årsregnskabet og selvangivelsen{% endif %} for {{ regnskab.aar }}.

Vedlagt er en **materialeliste**, der er tilpasset jeres virksomhed. Vi beder jer gennemgå listen og sende materialet senest **{{ felt.frist_materiale }}** – helst ved upload i bogføringsprogrammet, så det ligger samlet ved bogføringen.

## Hvorfor fristen er vigtig
{% if kunde.er_kapitalselskab %}Årsrapporten skal godkendes på generalforsamlingen og være modtaget i Erhvervsstyrelsen senest **{{ regnskab.frist_aarsrapport }}**. Overskrides fristen, kan hvert medlem af den øverste ledelse blive pålagt en afgift, og i sidste ende kan Erhvervsstyrelsen anmode skifteretten om at opløse selskabet (ÅRL §§ 150-151). Selskabets selvangivelse skal desuden være indberettet til Skattestyrelsen senest 6 måneder efter indkomstårets udløb – for indkomstår, der udløber i perioden 1. – 31. marts, senest 1. september samme år (skattekontrolloven § 12).{% else %}Oplysningerne skal bruges til jeres udvidede selvangivelse (oplysningsskema), der skal være indberettet senest 1. juli. Ved for sen indberetning kan Skattestyrelsen ansætte indkomsten skønsmæssigt.{% endif %} Jo tidligere vi får materialet, jo bedre tid har vi til at rådgive jer om skat og eventuelle dispositioner.

## Tidsplan
| | Dato |
|---|---|
| Statusdag | {{ regnskab.slut }} |
{% if branche.lager %}| Lageroptælling | {{ felt.lageroptaelling }} |
{% endif %}| Frist for materiale | {{ felt.frist_materiale }} |
| Afslutningsmøde (forslag) | {{ felt.moede_dato }} |
{% if kunde.er_kapitalselskab %}| Senest modtaget i Erhvervsstyrelsen | {{ regnskab.frist_aarsrapport }} |
{% endif %}

## Gode råd
- Upload alle bilag for året, også dem fra regnskabsårets sidste måned, og afstem bankkontiene
{% if branche.lager %}- Planlæg lageroptællingen nu – instruks er vedlagt
{% endif %}{% if branche.kontantintensiv %}- Tæl kassen op på statusdagen og gem Z-rapporten for årets sidste dag
{% endif %}{% if branche.igangvaerende_arbejder %}- Gør tidsregistreringen færdig for alle sager pr. statusdagen
{% endif %}- Oplys os om alt usædvanligt i året: nye lån, køb/salg af aktiver, tvister, ændringer i ejerkredsen

Har I spørgsmål til listen, så kontakt {{ kunde.ansvarlig }}.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}

Bilag: Materialeliste til årsafslutning {{ regnskab.aar }}{% if branche.lager %}, instruks for lageroptælling{% endif %}
