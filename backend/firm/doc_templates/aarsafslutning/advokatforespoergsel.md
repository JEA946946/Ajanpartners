---
{
  "title": "Advokatforespørgsel (ISA 501)",
  "description": "Brev fra kunden til dennes advokat med anmodning om at oplyse revisor om verserende og truende retssager, krav og tvister. Svar direkte til revisor.",
  "kind": "brev",
  "references": ["ISA 501, pkt. 9-12", "ISA 505", "Årsregnskabsloven §§ 33, 64 (hensatte forpligtelser og eventualforpligtelser)"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "advokat_navn", "label": "Advokatfirma og ansvarlig advokat", "type": "text"},
    {"name": "advokat_adresse", "label": "Advokatens adresse", "type": "textarea"},
    {"name": "sager", "label": "Sager kendt af ledelsen (beskrivelse, ledelsens vurdering)", "type": "textarea"},
    {"name": "periode_fra", "label": "Periode fra", "type": "text", "default": "{{ regnskab.start }}"},
    {"name": "svarfrist", "label": "Svar senest", "type": "date"}
  ]
}
---
**{{ kunde.navn }}**
{{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }} · CVR {{ kunde.cvr }}

{{ felt.advokat_navn }}
{{ felt.advokat_adresse }}

{{ dato.idag }}

# Anmodning om oplysninger til vores revisor

I forbindelse med revisionen af vores årsregnskab for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} beder vi jer give vores revisor, {{ firma.navn }}, oplysning om sager, I har behandlet for os i perioden fra {{ felt.periode_fra }} og frem til datoen for jeres svar. Vi fritager jer for tavshedspligt i det omfang, det er nødvendigt for at besvare denne forespørgsel.

## Sager, vi har kendskab til
{{ felt.sager }}

For hver af ovenstående sager – og for andre sager, I har behandlet for os – beder vi jer oplyse:
1. en kort beskrivelse af sagen og dens stade (verserende, truende, afsluttet)
2. jeres vurdering af det sandsynlige udfald
3. et skøn over det økonomiske omfang (krav, mulige omkostninger, sagsomkostninger), eller oplysning om, at beløbet ikke kan skønnes
4. evt. forhold, hvor vi ifølge jeres vurdering har en forpligtelse, som ikke er nævnt ovenfor{% if branche.byggeri %}, herunder mangelsager, voldgiftssager (Voldgiftsnævnet for byggeri og anlæg) og krav fra bygherrer eller underentreprenører{% endif %}{% if branche.ejendom %}, herunder sager ved huslejenævn/boligret og tvister med lejere{% endif %}
5. jeres tilgodehavende honorar hos os pr. {{ regnskab.slut }}, herunder udført, men ikke faktureret arbejde

Bekræft venligst også, hvis I ikke har behandlet andre sager for os end de nævnte.

Svaret bedes sendt **direkte til vores revisor** senest {{ felt.svarfrist }}:
{{ firma.navn }}, {{ firma.adresse }} · {{ firma.email }}

Med venlig hilsen
{{ kunde.navn }}

______________________________________
for {{ kunde.ledelsesorgan }}

Kopi: {{ firma.navn }}
