---
{
  "title": "Kapitalafkastordningen (KAO) – opgørelse",
  "description": "Arbejdspapir for kapitalafkastordningen: kapitalafkastgrundlag, kapitalafkast (2 % i 2026), loft, konjunkturudligning og sammenligning med virksomhedsordningen.",
  "kind": "arbejdspapir",
  "references": ["Virksomhedsskatteloven §§ 22 a-22 d", "VSL § 22 a (kapitalafkast og -grundlag)", "VSL § 22 b (konjunkturudligning)", "SKM2026.414.SKTST", "Den juridiske vejledning C.C.5.3"],
  "legal_forms": ["enk", "is", "pmv"],
  "industry_aware": true,
  "fields": [
    {"name": "ejer", "label": "Virksomhedsejer", "type": "text"},
    {"name": "kapitalafkastsats", "label": "Kapitalafkastsats (%)", "type": "text", "default": "2"},
    {"name": "aktiver_primo", "label": "Erhvervsmæssige aktiver primo (kr.)", "type": "number"},
    {"name": "gaeld_primo", "label": "Erhvervsgæld primo (kr., til sammenligning med VSO)", "type": "number"},
    {"name": "overskud", "label": "Overskud af virksomhed (kr.)", "type": "text", "default": "{{ regnskab.resultat }}"},
    {"name": "konjunktur", "label": "Ønsket henlæggelse til konjunkturudligning (kr.)", "type": "number", "default": "0"}
  ]
}
---
# Kapitalafkastordningen {{ regnskab.aar }}

**Ejer:** {{ felt.ejer }} · **Virksomhed:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}
**Udarbejdet af:** {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Formål og betingelser
Kapitalafkastordningen giver mulighed for at overføre et beregnet kapitalafkast fra personlig indkomst til kapitalindkomst. Den er et enkelt alternativ til virksomhedsordningen, når der ikke ønskes opsparing i virksomheden, og når regnskabet ikke opfylder virksomhedsordningens krav om adskillelse af privat- og erhvervsøkonomi.

- [ ] Selvstændig erhvervsvirksomhed (personligt drevet, herunder udlejning af fast ejendom).
- [ ] Valget træffes i oplysningsskemaet for året.
- [ ] Ved satsen på {{ felt.kapitalafkastsats }} % (2026) er effekten begrænset; vurdér om ordningen giver fordel ift. personskattelovens almindelige regler.

## 2. Kapitalafkastgrundlag (VSL § 22 a, stk. 5-8)
| | Kr. |
|---|---|
| Erhvervsmæssige aktiver primo (samme værdiansættelse som i virksomhedsordningen; blandede aktiver kun med erhvervsmæssig andel, § 22 a, stk. 6) | {{ felt.aktiver_primo }} |
| Varelager, igangværende arbejder og varedebitorer medregnes kun med det beløb, der overstiger varekreditorerne | |
| Ikke medregnet: kontanter, likvide midler, andre tilgodehavender end varedebitorer, værdipapirer, anparter i anpartsvirksomhed og bolig udlejet til nærtstående (§ 22 a, stk. 7-8) | |
| **Kapitalafkastgrundlag** (gæld fradrages **ikke** – i modsætning til virksomhedsordningen; noteret gæld: {{ felt.gaeld_primo }} kr.) | |
| Kapitalafkast ({{ felt.kapitalafkastsats }} %) | |

Kapitalafkastet er begrænset af en maksimeringsregel og kan ikke overstige virksomhedens overskud ({{ felt.overskud }} kr.) – kontrollér beregningen mod Den juridiske vejledning C.C.5.3.1.2.2. Kapitalafkastet fradrages i den personlige indkomst og lægges til kapitalindkomsten.

## 3. Konjunkturudligning (VSL § 22 b)
- Op til 25 % af overskuddet kan henlægges, dog mindst 5.000 kr. Ønsket henlæggelse: {{ felt.konjunktur }} kr.
- Henlæggelsen beskattes med konjunkturudligningsskat (22 %), og 78 % af det henlagte beløb skal indsættes på en bunden konto senest ved fristen for oplysningsskemaet.
- Hævning af det henlagte beløb medregnes i den personlige indkomst med godskrivning af den betalte skat. Ophører brugen af kapitalafkastordningen, medregnes henlæggelserne i det sidste år.

## 4. Sammenligning
| | Personskattelov | Kapitalafkastordning | Virksomhedsordning |
|---|---|---|---|
| Renteudgifter | Kapitalindkomst | Kapitalindkomst | Fradrag i virksomhedens resultat (personlig indkomst) |
| Opsparing med 22 % skat | Nej | Delvis (konjunkturudligning) | Ja (opsparet overskud) |
| Krav til regnskab | Almindelige | Almindelige | Adskillelse privat/erhverv |
| Estimeret skat {{ regnskab.aar }} | | | |

{% if branche.landbrug or branche.ejendom %}*Branchebemærkning:* For {{ branche.navn }} med betydelig fremmedfinansiering er virksomhedsordningen ofte mest fordelagtig pga. fuldt fradrag for renter i personlig indkomst.{% endif %}

Anbefaling: \_\_\_\_\_\_
