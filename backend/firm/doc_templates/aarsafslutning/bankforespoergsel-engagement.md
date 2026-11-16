---
{
  "title": "Engagementsforespørgsel til pengeinstitut (bankforespørgsel)",
  "description": "Anmodning til kundens pengeinstitut om bekræftelse af hele engagementet pr. statusdagen, med kundens fuldmagt. Struktur svarer til den fælles standardblanket mellem Finans Danmark og FSR – danske revisorer.",
  "kind": "brev",
  "references": ["ISA 505", "ISA 500", "Lov om finansiel virksomhed § 117 (tavshedspligt – kundens samtykke)"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "bank_navn", "label": "Pengeinstitut", "type": "text"},
    {"name": "bank_adresse", "label": "Pengeinstituttets adresse/afdeling", "type": "text"},
    {"name": "statusdag", "label": "Statusdag", "type": "text", "default": "{{ regnskab.slut }}"},
    {"name": "svarfrist", "label": "Ønsket svar senest", "type": "date"},
    {"name": "kontonumre", "label": "Kendte konti/kundenumre", "type": "textarea"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["Statsautoriseret revisor", "Registreret revisor", "Revisor"], "default": "Statsautoriseret revisor"}
  ]
}
---
{{ felt.bank_navn }}
{{ felt.bank_adresse }}

{{ dato.idag }}

# Engagementsforespørgsel pr. {{ felt.statusdag }}

**Kunde:** {{ kunde.navn }}, CVR {{ kunde.cvr }}
**Kendte konti/kundenumre:** {{ felt.kontonumre }}

Som revisor for ovennævnte kunde beder vi om oplysning om kundens samlede engagement med pengeinstituttet pr. {{ felt.statusdag }}. Kundens fuldmagt til, at pengeinstituttet kan udlevere oplysningerne til os, er vedlagt nedenfor.

Vi beder om, at svaret sendes direkte til {{ firma.navn }} – ikke via kunden – senest {{ felt.svarfrist }} til {{ firma.email }} eller med post til {{ firma.adresse }}. Hvis et punkt ikke er relevant, bedes det anført med "ingen".

Vi beder om oplysning om:

1. **Konti** – alle indlåns- og udlånskonti, også konti i fremmed valuta, opsparings-, deponerings- og spærrede konti: kontonummer, valuta, saldo, påløbne renter og evt. disponeringsbegrænsninger.
2. **Kreditter og lån** – kassekreditter, byggelån, lån og leasing: bevilget maksimum, udnyttet beløb, rentesats, løbetid/udløbsdato og afdragsvilkår.
3. **Sikkerheder stillet af kunden** – ejerpantebreve, virksomhedspant, transport i fordringer, pant i værdipapirer, indlån eller andre aktiver, med angivelse af beløb og hvilke forpligtelser sikkerheden dækker.
4. **Sikkerheder stillet af tredjemand** til fordel for kundens engagement (fx kautioner fra ejer eller koncernselskaber).
5. **Garantier og kautioner** stillet af pengeinstituttet på kundens vegne (fx arbejdsgarantier, betalingsgarantier, huslejegarantier) og af kunden for tredjemand.
6. **Afledte finansielle instrumenter** – renteswaps, valutaterminsforretninger, optioner: type, hovedstol, udløb og markedsværdi pr. statusdagen.
7. **Værdipapirer i depot** – depotnummer, beholdning og kursværdi; evt. pantsætning.
8. **Remburser, inkassoer og andre åbne forretninger**.
9. **Covenants** og andre særlige vilkår, herunder om de er overholdt pr. statusdagen.
10. **Fuldmagter** – hvem der har fuldmagt eller tegningsret til kontiene.
11. **Andre forhold**, som pengeinstituttet finder relevante for vores bedømmelse af engagementet.

Oplysningerne bruges alene i forbindelse med vores revision/gennemgang af kundens årsregnskab.

Med venlig hilsen

{{ firma.navn }}
{{ firma.adresse }} · CVR {{ firma.cvr }} · {{ firma.telefon }}

______________________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}

---

## Fuldmagt og samtykke

{{ kunde.navn }}, CVR {{ kunde.cvr }}, giver hermed {{ felt.bank_navn }} fuldmagt til og samtykke til at give {{ firma.navn }} oplysninger om vores samlede engagement pr. {{ felt.statusdag }} som beskrevet ovenfor, og til at besvare opfølgende spørgsmål fra {{ firma.navn }} om engagementet i forbindelse med revisionen. Pengeinstituttet fritages i det omfang fra sin tavshedspligt.

Fuldmagten gælder, indtil den tilbagekaldes skriftligt.

Dato: ______________________

______________________________________
{{ kunde.navn }} – tegningsberettiget for {{ kunde.ledelsesorgan }}
Navn med blokbogstaver: ______________________
