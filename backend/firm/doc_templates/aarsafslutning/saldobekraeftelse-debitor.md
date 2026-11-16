---
{
  "title": "Saldobekræftelse – debitor",
  "description": "Anmodning til en kunde (debitor) om bekræftelse af mellemværendet pr. statusdagen. Sendes i kundens navn; svaret går direkte til revisor (ISA 505).",
  "kind": "brev",
  "references": ["ISA 505", "ISA 500"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "modtager_navn", "label": "Debitor (navn)", "type": "text"},
    {"name": "modtager_adresse", "label": "Debitors adresse", "type": "textarea"},
    {"name": "debitornummer", "label": "Debitornummer", "type": "text"},
    {"name": "saldo", "label": "Saldo ifølge vores bøger (kr.)", "type": "number"},
    {"name": "statusdag", "label": "Statusdag", "type": "text", "default": "{{ regnskab.slut }}"},
    {"name": "form", "label": "Bekræftelsesform", "type": "select", "options": ["Positiv – saldo oplyst", "Positiv – blank (modtager oplyser saldo)"], "default": "Positiv – saldo oplyst"},
    {"name": "svarfrist", "label": "Svar senest", "type": "date"}
  ]
}
---
**{{ kunde.navn }}**
{{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }} · CVR {{ kunde.cvr }}

{{ felt.modtager_navn }}
{{ felt.modtager_adresse }}

{{ dato.idag }}

# Bekræftelse af mellemværende pr. {{ felt.statusdag }}

Debitornummer: {{ felt.debitornummer }}

Vores revisor, {{ firma.navn }}, er i gang med at revidere vores årsregnskab for {{ regnskab.aar }}. I den forbindelse beder vi jer bekræfte jeres mellemværende med os pr. {{ felt.statusdag }}.

{% if felt.form == "Positiv – saldo oplyst" %}Ifølge vores bogføring skyldte I os pr. {{ felt.statusdag }} **{{ felt.saldo }} kr.**

Vi beder jer bekræfte saldoen eller oplyse den saldo, der fremgår af jeres bogføring, og specificere evt. forskelle (fx betalinger undervejs, kreditnotaer, omtvistede fakturaer).
{% else %}Vi beder jer oplyse den saldo, der ifølge jeres bogføring var mellem os pr. {{ felt.statusdag }}, gerne med en kontoudskrift.
{% endif %}
Dette er ikke en betalingsanmodning. Betalinger skal ikke sendes til revisor.

Send venligst svaret **direkte til vores revisor** senest {{ felt.svarfrist }}:
{{ firma.navn }}, {{ firma.adresse }} · {{ firma.email }}

Tak for hjælpen.

Med venlig hilsen
{{ kunde.navn }}

______________________________________
for {{ kunde.ledelsesorgan }}

---

## Svar til {{ firma.navn }}

Vedrørende {{ kunde.navn }}, debitornummer {{ felt.debitornummer }}, pr. {{ felt.statusdag }}:

- [ ] Saldoen på {{ felt.saldo }} kr. er korrekt (skyldig til {{ kunde.navn }})
- [ ] Saldoen er ikke korrekt. Vores saldo er __________________ kr. Forskellen skyldes:

____________________________________________________________

Firma: ______________________ Dato: ______________

Underskrift: ______________________ Navn/stilling: ______________________
