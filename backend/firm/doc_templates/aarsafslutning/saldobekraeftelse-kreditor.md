---
{
  "title": "Saldobekræftelse – kreditor",
  "description": "Anmodning til en leverandør (kreditor) om kontoudtog/bekræftelse pr. statusdagen. Normalt blank anmodning for at teste fuldstændigheden af gælden (ISA 505).",
  "kind": "brev",
  "references": ["ISA 505", "ISA 500"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "modtager_navn", "label": "Kreditor (navn)", "type": "text"},
    {"name": "modtager_adresse", "label": "Kreditors adresse", "type": "textarea"},
    {"name": "kundenummer", "label": "Vores kundenummer hos kreditor", "type": "text"},
    {"name": "statusdag", "label": "Statusdag", "type": "text", "default": "{{ regnskab.slut }}"},
    {"name": "svarfrist", "label": "Svar senest", "type": "date"}
  ]
}
---
**{{ kunde.navn }}**
{{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }} · CVR {{ kunde.cvr }}

{{ felt.modtager_navn }}
{{ felt.modtager_adresse }}

{{ dato.idag }}

# Anmodning om kontoudtog pr. {{ felt.statusdag }}

Vores kundenummer: {{ felt.kundenummer }}

I forbindelse med revisionen af vores årsregnskab for {{ regnskab.aar }} beder vi jer sende et kontoudtog, der viser vores mellemværende med jer pr. {{ felt.statusdag }}, til vores revisor, {{ firma.navn }}.

Vi beder om, at kontoudtoget indeholder:
- alle åbne fakturaer og kreditnotaer pr. {{ felt.statusdag }} med fakturanummer, dato og beløb
- evt. forudbetalinger, deposita, bonus- og rabatopgørelser
- varer leveret før {{ felt.statusdag }}, som endnu ikke er faktureret
- evt. sikkerheder, ejendomsforbehold eller andre aftaler, der vedrører mellemværendet

Send venligst kontoudtoget **direkte til vores revisor** senest {{ felt.svarfrist }}:
{{ firma.navn }}, {{ firma.adresse }} · {{ firma.email }}

Tak for hjælpen.

Med venlig hilsen
{{ kunde.navn }}

______________________________________
for {{ kunde.ledelsesorgan }}

---

## Svar til {{ firma.navn }}

Vedrørende {{ kunde.navn }} (kundenr. {{ felt.kundenummer }}) pr. {{ felt.statusdag }}:

Saldo til gode hos {{ kunde.navn }}: __________________ kr. (specifikation vedlagt)

- [ ] Vi har ejendomsforbehold eller anden sikkerhed for tilgodehavendet: ______________________

Firma: ______________________ Dato: ______________

Underskrift: ______________________ Navn/stilling: ______________________
