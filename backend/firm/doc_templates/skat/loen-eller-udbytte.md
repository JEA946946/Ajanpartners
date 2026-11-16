---
{
  "title": "Løn eller udbytte – aflønning af hovedaktionær",
  "description": "Arbejdspapir til sammenligning af løn og udbytte for ejeren af et ApS/A/S med 2026-satser (selskabsskat 22 %, aktieindkomst 27/42 % over 79.400 kr., AM-bidrag 8 %, mellem- og topskat), pension og ikke-skattemæssige hensyn.",
  "kind": "arbejdspapir",
  "references": ["Personskatteloven §§ 5-8 a", "Selskabsskatteloven § 17", "Arbejdsmarkedsbidragsloven", "Ligningsloven § 16 E", "Selskabsloven §§ 179-182", "Pensionsbeskatningsloven"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "ejer", "label": "Hovedaktionær", "type": "text"},
    {"name": "overskud_foer_loen", "label": "Selskabets overskud før ejerløn (kr.)", "type": "number"},
    {"name": "oensket_netto", "label": "Ønsket rådighedsbeløb efter skat (kr.)", "type": "number"},
    {"name": "anden_indkomst", "label": "Ejerens øvrige personlige indkomst (kr.)", "type": "number", "default": "0"},
    {"name": "gift", "label": "Gift/samlevende ægtefælle (dobbelt aktieindkomstgrænse)", "type": "checkbox"},
    {"name": "kommuneskat", "label": "Kommuneskat inkl. evt. kirkeskat (%)", "type": "text", "default": "25,0"}
  ]
}
---
# Løn eller udbytte {{ regnskab.aar }}

**Selskab:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }} · **Ejer:** {{ felt.ejer }}
**Udarbejdet af:** {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Satser 2026 (kontrollér ved årsskifte)
| Skat | Sats/grænse |
|---|---|
| Selskabsskat | 22 % |
| AM-bidrag | 8 % |
| Bundskat | 12,01 % |
| Kommuneskat (+ kirkeskat) | {{ felt.kommuneskat }} % |
| Personfradrag | 54.100 kr. |
| Mellemskat 7,5 % | over 641.200 kr. (efter AM-bidrag) |
| Topskat 7,5 % | over 777.900 kr. (efter AM-bidrag) |
| Toptopskat 5 % | over ca. 2,59 mio. kr. (efter AM-bidrag) |
| Skatteloft (personlig indkomst) | 44,57 % / 52,07 % / 57,07 % |
| Aktieindkomst | 27 % op til 79.400 kr.{% if felt.gift %} (158.800 kr. for ægtefæller){% endif %}, 42 % herover |
| Beskæftigelsesfradrag | Indgår ved løn (ikke ved udbytte) |

Samlet skat på udbytte (selskabsskat + udbytteskat): 22 % + 78 % × 27 % = **43,06 %** inden for progressionsgrænsen; 22 % + 78 % × 42 % = **54,76 %** herover.

## 2. Beregning
| | Løn | Udbytte | Kombination |
|---|---|---|---|
| Selskabets overskud før ejerløn | {{ felt.overskud_foer_loen }} | {{ felt.overskud_foer_loen }} | {{ felt.overskud_foer_loen }} |
| Løn (fradrag i selskabet) | | 0 | |
| Selskabsskat 22 % | | | |
| Udbytte | 0 | | |
| AM-bidrag 8 % af løn | | 0 | |
| Personlig indkomstskat | | 0 | |
| Skat af aktieindkomst | 0 | | |
| **Ejerens rådighedsbeløb** | | | |
| **Samlet skat (selskab + ejer)** | | | |
| Effektiv skatteprocent | | | |

Ønsket rådighedsbeløb: {{ felt.oensket_netto }} kr. Ejerens øvrige personlige indkomst: {{ felt.anden_indkomst }} kr.

**Tommelfingerregel:** Løn op til mellemskattegrænsen er typisk billigere end udbytte over aktieindkomstgrænsen, mens udbytte inden for progressionsgrænsen (27 %) er konkurrencedygtigt med løn i mellem-/topskattelaget. Den optimale fordeling beregnes konkret.

## 3. Andre hensyn
- [ ] **Pension:** Arbejdsgiverbetalt pension (ratepension op til loftet) og livrente via løn giver fradrag med nuværende marginalskat; udbytte kan ikke indbetales med fradrag.
- [ ] **Sociale ydelser og forsikringer:** Dagpenge, sygedagpenge, barsel og visse forsikringer forudsætter lønindkomst.
- [ ] **Lån og boligkøb:** Banker vægter fast lønindkomst.
- [ ] **Selskabsretligt:** Udbytte forudsætter frie reserver og forsvarlighed (SL §§ 179-180); ekstraordinært udbytte kræver første årsrapport aflagt (§ 182).
- [ ] **Likviditet og konsolidering:** Opsparing i selskabet beskattes kun med 22 % indtil udlodning; vurdér behov for kapitalberedskab.
- [ ] **Hævninger uden beslutning:** Må ikke ske – beskattes som løn/udbytte efter LL § 16 E.
- [ ] **Markedsløn:** Løn skal være forretningsmæssigt begrundet for fradrag; ved meget høj løn kan fradrag nægtes.
- [ ] **Ægtefælle:** Udnyttelse af ægtefællens progressionsgrænse for aktieindkomst og ansættelse af ægtefælle til markedsløn.
- [ ] **Varslede ændringer:** Regeringen har varslet nedsat selskabsskat (19 %) og forhøjet aktieindkomstgrænse (lovforslag ventes i februar 2027) – ikke vedtaget pr. {{ dato.idag }}. Opdatér beregningen, når lovforslaget foreligger.

Anbefaling: \_\_\_\_\_\_
