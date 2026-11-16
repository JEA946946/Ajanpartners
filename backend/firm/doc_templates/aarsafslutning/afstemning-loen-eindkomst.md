---
{
  "title": "Afstemning af løn til eIndkomst",
  "description": "Arbejdspapir til afstemning af bogført løn, A-skat, AM-bidrag, ATP, pension, feriepenge og personalegoder til indberetninger i eIndkomst og betalinger på skattekontoen.",
  "kind": "arbejdspapir",
  "references": ["Kildeskatteloven §§ 46, 48", "Arbejdsmarkedsbidragsloven", "Lov om indkomstregistret (eIndkomst)", "Ferieloven", "Ligningsloven § 16 (personalegoder)", "Årsregnskabsloven (gennemsnitligt antal ansatte)"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "antal_ansatte", "label": "Gennemsnitligt antal heltidsansatte (beregnet)", "type": "number"},
    {"name": "beregning_ansatte", "label": "Beregningsmetode antal ansatte", "type": "select", "options": ["ATP-bidrag", "Timer i eIndkomst / 1.924", "Månedlige opgørelser"], "default": "Timer i eIndkomst / 1.924"},
    {"name": "bemaerkninger", "label": "Bemærkninger og forklaring af differencer", "type": "textarea"}
  ]
}
---
# Afstemning af løn {{ regnskab.aar }} – {{ kunde.navn }}

Periode: {{ regnskab.start }} – {{ regnskab.slut }}  Udarbejdet af: {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Afstemning af bruttoløn
| Post | Bogført (finans) | eIndkomst | Difference | Forklaring |
|---|---|---|---|---|
| A-indkomst | | | | |
| B-indkomst/honorarer | | | | |
| Personalegoder (fri bil, telefon, sundhedsforsikring m.m.) | | | | |
| Skattefri rejse-/befordringsgodtgørelse | | | | |
| Arbejdsgiverbetalt pension | | | | |
| ATP | | | | |
| **I alt** | | | | |

Typiske forskelle: periodeforskydning (løn for december udbetalt i januar), feriepengeforpligtelse, bonus hensat ikke udbetalt, løn bogført på andre konti (fx igangværende arbejder, aktiveret udvikling), lønrefusion (sygedagpenge, barsel, flexjob).

## 2. Afstemning af A-skat og AM-bidrag
| Måned | A-skat indberettet | AM-bidrag indberettet | Betalt via skattekonto | Saldo på skyldig konto | Difference |
|---|---|---|---|---|---|
| Januar | | | | | |
| Februar | | | | | |
| Marts | | | | | |
| April | | | | | |
| Maj | | | | | |
| Juni | | | | | |
| Juli | | | | | |
| August | | | | | |
| September | | | | | |
| Oktober | | | | | |
| November | | | | | |
| December | | | | | |
| **I alt** | | | | | |

- [ ] Skyldig A-skat og AM-bidrag pr. {{ regnskab.slut }} svarer til sidste periodes indberetning og er betalt rettidigt efter statusdagen
- [ ] Skattekontoen er gennemgået for renter og restancer

## 3. Øvrige lønrelaterede forpligtelser
- [ ] **Feriepengeforpligtelse** pr. {{ regnskab.slut }} (samtidighedsferie: optjent, ikke afholdt ferie + ferietillæg 1 %) – timelønnede/FerieKonto; overførte feriedage
- [ ] Skyldig pension og ATP er afstemt til pensionsselskabets opgørelse
- [ ] Bonus, provision og overtid optjent, men ikke udbetalt, er hensat
- [ ] Lønsumsafgift er opgjort og afstemt, hvis virksomheden er momsfritaget{% if branche.momsfritaget %} (relevant for denne kunde){% endif %}
- [ ] Arbejdsgiverbidrag (AUB, AES, Barsel.dk, FIB) er afstemt til opkrævninger
- [ ] Personalegoder er indberettet korrekt (fri bil, fri telefon, sundhedsforsikring, gaver)
{% if branche.transport %}- [ ] Skattefri rejse- og udetillæg til chauffører er dokumenteret med tachografdata/kørebog og overholder satserne for indkomståret
{% endif %}{% if branche.restauration or branche.hotel %}- [ ] Personaleforplejning og drikkepenge er behandlet korrekt (A-indkomst/kostfradrag)
{% endif %}{% if branche.byggeri %}- [ ] Skattefri befordringsgodtgørelse og rejsegodtgørelse til montører er dokumenteret; kost og logi ved arbejde på midlertidige arbejdssteder
{% endif %}{% if kunde.er_kapitalselskab %}- [ ] Løn til hovedanpartshaver/direktion er afstemt til eventuel beslutning og er indberettet som A-indkomst; fri bil og andre goder til ejer
{% else %}- [ ] Medarbejdende ægtefælle: løn/overførsel er behandlet efter kildeskattelovens regler
{% endif %}

## 4. Gennemsnitligt antal ansatte
Gennemsnitligt antal heltidsansatte: **{{ felt.antal_ansatte }}** (metode: {{ felt.beregning_ansatte }}). Tallet oplyses i noterne og bruges ved vurdering af størrelsesgrænser (regnskabsklasse, fravalg af revision).

## 5. Bemærkninger
{{ felt.bemaerkninger }}

- [ ] Lønomkostninger og lønrelaterede forpligtelser er fuldstændige og korrekt periodiseret.

Udført: ______________________  Gennemgået: ______________________
