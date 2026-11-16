---
{
  "title": "Udbytte – indeholdelse og indberetning af udbytteskat (tjekliste)",
  "description": "Tjekliste for unoterede selskabers udlodning: selskabsretlig kontrol, satser for indeholdelse (27/22/0 %), angivelse og betaling senest den 10. i måneden efter (december: 17. januar), indberetning af modtagere, udenlandske modtagere og bogføring.",
  "kind": "tjekliste",
  "references": ["Kildeskatteloven §§ 65 og 66", "Selskabsskatteloven §§ 2, stk. 1, litra c, og 13", "Ligningsloven § 16 A", "Personskatteloven § 8 a", "Skatteindberetningsloven", "Selskabsloven §§ 179-183"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "beslutningsdato", "label": "Dato for vedtagelse af udbytte", "type": "date"},
    {"name": "udbytte", "label": "Samlet udbytte (kr.)", "type": "number"},
    {"name": "type", "label": "Type", "type": "select", "options": ["Ordinært udbytte", "Ekstraordinært udbytte", "Maskeret udlodning/LL § 16 E", "Udlodning ved kapitalnedsættelse/likvidation"], "default": "Ordinært udbytte"},
    {"name": "modtagere", "label": "Modtagere (navn, CPR/CVR, land, ejerandel, beløb)", "type": "textarea"},
    {"name": "frist", "label": "Frist for angivelse og betaling", "type": "date"},
    {"name": "udenlandsk", "label": "Der er udenlandske modtagere", "type": "checkbox"}
  ]
}
---
# Udbytte og udbytteskat

**Selskab:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}
**Vedtaget:** {{ felt.beslutningsdato }} · **Type:** {{ felt.type }} · **Beløb:** {{ felt.udbytte }} kr.
**Ansvarlig:** {{ medarbejder.navn }}

## 1. Selskabsretlig kontrol
- [ ] Udbyttet er vedtaget af generalforsamlingen (eller ledelsen efter bemyndigelse til ekstraordinært udbytte) og ligger inden for ledelsens forslag.
- [ ] Udbyttet overstiger ikke de frie reserver (SL § 180, stk. 2 / § 182, stk. 3) og er forsvarligt (§ 179, stk. 2).
- [ ] Ekstraordinært udbytte: balancekrav i § 183 er opfyldt (mellembalance ved beslutning mere end 6 måneder efter balancedagen; i A/S altid en balance).
- [ ] Beslutningen er protokolleret.

## 2. Indeholdelse af udbytteskat
| Modtager | Indeholdelse | Note |
|---|---|---|
| Person, fuldt skattepligtig i Danmark | 27 % | Udbyttet er aktieindkomst: 27 % op til 79.400 kr. (2026; 158.800 kr. for samlevende ægtefæller), 42 % herover. Indeholdelsen er endelig for 27 %; resten opkræves via årsopgørelsen. |
| Dansk selskab – datterselskabsaktier (≥ 10 %) eller koncernselskabsaktier | 0 % | Skattefrit udbytte (SEL § 13, stk. 1, nr. 2). Indberettes alligevel. |
| Dansk selskab – porteføljeaktier (< 10 %) | 22 % | Unoterede porteføljeaktier: 70 % af udbyttet er skattepligtigt; kontrollér indeholdelsessatsen ved indberetningen. |
| Udenlandsk person | 27 % | Modtager kan søge refusion af overskydende skat efter dobbeltbeskatningsoverenskomst (typisk ned til 15 %). Reduceret sats direkte kun efter særlig ordning. |
| Udenlandsk selskab – datterselskabsaktier, EU/DBO-land | 0 % | Kun hvis beskatning frafaldes eller nedsættes efter moder-/datterselskabsdirektivet eller DBO, og modtageren er retmæssig ejer (beneficial owner) – vurdér misbrugsreglen (LL § 3). |

{% if felt.udenlandsk %}- [ ] **Udenlandske modtagere:** retmæssig ejer dokumenteret, hjemlandets skattepligt og DBO kontrolleret; ved 0 % dokumentation for direktivets betingelser (ejerandel, ejertid ≥ 1 år, ingen kunstige arrangementer). Overvej at indhente rådgivning før udbetaling.
{% endif %}

Modtagere:
{{ felt.modtagere }}

## 3. Angivelse og betaling
- [ ] Udbytteskatten angives og betales i TastSelv Erhverv (udbytteangivelse) senest den **10. i måneden efter** vedtagelsen. For udbytte vedtaget i december er fristen **17. januar** (kildeskattelovens § 66). Frist for dette udbytte: **{{ felt.frist }}**.
- [ ] Angivelse sker, uanset om udbyttet endnu ikke er udbetalt; også 0-indeholdelse angives.
- [ ] Indberetning af udbyttet pr. modtager (CPR/CVR, beløb, indeholdt skat) sker samtidig og senest ved samme frist.
- [ ] Selskabet hæfter for manglende indeholdelse, medmindre det godtgør, at der ikke er udvist forsømmelighed. Skattestyrelsen fører aktiv kontrol (rykkerbreve til selskaber, der har udloddet uden angivelse).

## 4. Bogføring
| Dato | Konto | Debet | Kredit |
|---|---|---|---|
| Vedtagelse | Overført resultat / foreslået udbytte | Udbytte | |
| Vedtagelse | Skyldigt udbytte | | Netto udbytte |
| Vedtagelse | Skyldig udbytteskat | | Udbytteskat |
| Betaling | Bank | | Netto + skat |

## 5. Særlige situationer
{% if felt.type == "Maskeret udlodning/LL § 16 E" %}- [ ] Hævninger/lån omklassificeret til udbytte: udbytteskat angives og betales; der beregnes renter ved for sen betaling. Generalforsamlingsbeslutning dokumenteres efterfølgende.
{% endif %}{% if felt.type == "Udlodning ved kapitalnedsættelse/likvidation" %}- [ ] Vurdér om udlodningen er afståelse (LL § 16 A, stk. 3) – ved afståelsesbeskatning indeholdes ikke udbytteskat. Likvidationsprovenu i opløsningsåret beskattes som afståelse.
{% endif %}- [ ] Udbytte i andre værdier end kontanter: handelsværdi og vurderingsberetning (SL § 181/§ 183, stk. 5).
- [ ] Holdingselskaber: udbyttet indgår ikke i den skattepligtige indkomst, hvis det er skattefrit; kontrollér at ejertid og ejerandel er opfyldt på udlodningstidspunktet.
- [ ] Modtager er personlig ejer: planlæg udbytte i forhold til progressionsgrænsen for aktieindkomst (ægtefællers udnyttelse af hinandens grænse).
