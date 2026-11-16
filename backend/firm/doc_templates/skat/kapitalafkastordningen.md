---
{
  "title": "Kapitalafkastordningen (KAO) – opgørelse",
  "description": "Arbejdspapir for kapitalafkastordningen: kapitalafkastgrundlag, kapitalafkast (2 % i 2026), loft, konjunkturudligning og sammenligning med virksomhedsordningen.",
  "kind": "arbejdspapir",
  "references": ["Virksomhedsskatteloven §§ 22 a-22 b", "VSL § 22 a (kapitalafkast og -grundlag)", "VSL § 22 b (konjunkturudligning)", "SKM2026.414.SKTST (kapitalafkastsats 2026)", "Den juridiske vejledning C.C.5.3"],
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

## 2. Kapitalafkastgrundlag (VSL § 22 a)
| | Kr. |
|---|---|
| Erhvervsmæssige aktiver primo (opgøres efter VSL § 22 a – kontrollér mod Den juridiske vejledning C.C.5.3, hvilke aktiver der medregnes, og med hvilke værdier) | {{ felt.aktiver_primo }} |
| Reguleringer efter VSL § 22 a (fx varelager, debitorer/kreditorer, likvider, værdipapirer, blandede aktiver – kontrollér) | |
| **Kapitalafkastgrundlag** (kontrollér behandlingen af gæld efter VSL § 22 a; noteret erhvervsgæld: {{ felt.gaeld_primo }} kr.) | |
| Kapitalafkast ({{ felt.kapitalafkastsats }} %) | |

Kapitalafkastet er begrænset af en maksimeringsregel og kan ikke overstige virksomhedens overskud ({{ felt.overskud }} kr.) – kontrollér beregningen mod Den juridiske vejledning C.C.5.3.1.2.2. Kapitalafkastet fradrages i den personlige indkomst og lægges til kapitalindkomsten.

## 3. Konjunkturudligning (VSL § 22 b)
- Op til 25 % af årets overskud kan henlægges; mindste henlæggelse er 5.000 kr. (2026). Ønsket henlæggelse: {{ felt.konjunktur }} kr.
- Henlæggelsen beskattes med konjunkturudligningsskat (22 % i 2026), og 78 % af henlæggelsen skal indsættes på en bunden konto (VSL § 22 b, stk. 1-3; Skatte- og Vækstministeriets satsoversigt 2026). Frist for indsættelse kontrolleres i VSL § 22 b.
- Hævning af henlagte beløb og ophør med ordningen: behandles efter VSL § 22 b – kontrollér reglerne i det konkrete tilfælde.

## 4. Sammenligning
| | Personskattelov | Kapitalafkastordning | Virksomhedsordning |
|---|---|---|---|
| Renteudgifter | Kapitalindkomst | Kapitalindkomst | Fradrag i virksomhedens resultat (personlig indkomst) |
| Opsparing med 22 % skat | Nej | Delvis (konjunkturudligning) | Ja (opsparet overskud) |
| Krav til regnskab | Almindelige | Almindelige | Adskillelse privat/erhverv |
| Estimeret skat {{ regnskab.aar }} | | | |

{% if branche.landbrug or branche.ejendom %}*Branchebemærkning:* For {{ branche.navn }} med betydelig fremmedfinansiering er virksomhedsordningen ofte mest fordelagtig pga. fuldt fradrag for renter i personlig indkomst.{% endif %}

Anbefaling: \_\_\_\_\_\_
