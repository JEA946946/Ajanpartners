---
{
  "title": "Afstemning af moms",
  "description": "Arbejdspapir til afstemning af momsangivelser mod bogføring og skattekonto, samt årsafstemning af momspligtig omsætning, med branchespecifikke momsforhold.",
  "kind": "arbejdspapir",
  "references": ["Momsloven §§ 4, 37-38, 42-44, 46, 51, 57 (LBK nr. 209 af 27. februar 2024 med senere ændringer)", "Momsbekendtgørelsen", "Opkrævningsloven (skattekontoen)", "Lønsumsafgiftsloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "bemaerkninger", "label": "Bemærkninger og forklaring af differencer", "type": "textarea"}
  ]
}
---
# Afstemning af moms {{ regnskab.aar }} – {{ kunde.navn }}

Momsperiode: **{{ kunde.momsperiode }}**  Regnskabsperiode: {{ regnskab.start }} – {{ regnskab.slut }}
Udarbejdet af: {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Periodeafstemning
| Periode | Salgsmoms | Købsmoms | Moms af EU-køb/omvendt betalingspligt | Afgifter (energi m.m.) | Angivet tilsvar | Bogført tilsvar | Difference | Betalt/frist |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
| **I alt** | | | | | | | | |

- [ ] Skyldig moms pr. {{ regnskab.slut }} svarer til tilsvaret for den/de perioder, der ikke var forfaldne på statusdagen
- [ ] Skattekontoen er afstemt; renter og evt. restancer er bogført
- [ ] Rettelser til tidligere perioder er indberettet via TastSelv (efterangivelse) – ikke blot modregnet i næste periode uden registrering

## 2. Årsafstemning (sammenhæng mellem omsætning og salgsmoms)
| | Beløb |
|---|---|
| Omsætning ifølge årsregnskab | {{ regnskab.omsaetning }} |
| ÷ momsfri omsætning (eksport, EU-salg, momsfritaget) | |
| ÷/+ periodeforskydninger, igangværende arbejder | |
| = Momspligtig omsætning | |
| × 25 % = beregnet salgsmoms | |
| Angivet salgsmoms i året | |
| Difference (forklares) | |

- [ ] Rubrik A (EU-køb), rubrik B (EU-salg varer/ydelser) og rubrik C er afstemt til bogføringen og EU-salgsangivelsen
- [ ] Købsmoms: stikprøver på fradragsbegrænsninger (momsloven § 42) – restaurationsydelser af strengt erhvervsmæssig karakter (25 %, § 42, stk. 2), hotelovernatning (fradragsbegrænsningen ophævet fra 1. januar 2015), øvrig repræsentation, personbiler og private udgifter
- [ ] Fradrag for moms af tab på debitorer er korrekt (konstateret tab)

## 3. Branchespecifikke forhold
{% if branche.byggeri %}- [ ] **Omvendt betalingspligt** ved køb/salg af byggeydelser mellem momsregistrerede (momsloven § 46) og ved salg af byggegrunde/nye bygninger (momspligtigt salg af fast ejendom)
{% endif %}{% if branche.bilhandel %}- [ ] **Brugtmomsordningen** (momsloven kap. 17): beregning af avance pr. bil, krav til bogføring, demobiler og leasingbiler; registreringsafgift og eksport
{% endif %}{% if branche.ejendom %}- [ ] **Udlejning af fast ejendom** er momsfritaget, medmindre der er frivillig registrering for erhvervsudlejning (momsloven § 51); regulering af købsmoms på investeringsgoder (regulering med en tiendedel pr. år for fast ejendom, momsloven § 44)
{% endif %}{% if branche.momsfritaget %}- [ ] **Delvis fradragsret**: pro rata-sats (momsloven § 38) beregnet på årsbasis og efterreguleret; **lønsumsafgift** er opgjort og angivet{% if branche.sundhed %} (sundhedsydelser){% endif %}{% if branche.undervisning %} (undervisning){% endif %}{% if branche.finans %} (finansielle ydelser){% endif %}
{% endif %}{% if branche.restauration or branche.hotel %}- [ ] Fradrag for moms af hotelophold og restaurationsydelser hos kunder er korrekt; ingen fradragsbegrænsning på egne varekøb; moms af personaleforplejning og egetforbrug
{% endif %}{% if branche.transport %}- [ ] Persontransport er momsfritaget (fx taxi, bus); godstransport momspligtig. Udenlandsk moms og energiafgift på brændstof søgt tilbage; moms af vejafgifter
{% endif %}{% if branche.landbrug %}- [ ] Salg til andelsselskaber, EU-støtte (uden for momsområdet), blandet anvendelse af ejendom (privat bolig) og energiafgifter (godtgørelse)
{% endif %}{% if branche.it or branche.medier %}- [ ] Salg af elektroniske ydelser til forbrugere i andre EU-lande (OSS-ordningen) og køb af ydelser fra udlandet (omvendt betalingspligt, rubrik A ydelser)
{% endif %}{% if branche.kontantintensiv %}- [ ] Momspligtig omsætning er afstemt til Z-rapporter og kortindløsning
{% endif %}- [ ] Energiafgifter og andre afgifter (godtgørelse af elafgift m.m.) er korrekt opgjort

## 4. Bemærkninger og konklusion
{{ felt.bemaerkninger }}

- [ ] Momstilsvar og momsforpligtelse pr. {{ regnskab.slut }} er korrekte; evt. fejl er rettet via efterangivelse og kunden er orienteret.

Udført: ______________________  Gennemgået: ______________________
