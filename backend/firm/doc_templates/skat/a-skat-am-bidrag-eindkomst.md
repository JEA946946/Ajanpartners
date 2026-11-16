---
{
  "title": "A-skat, AM-bidrag og eIndkomst – afstemning",
  "description": "Årlig afstemning af løn, A-skat, AM-bidrag, ATP, feriepenge og personalegoder mellem bogføring, lønsystem og eIndkomst. Med frister, personalegoder og hovedaktionær-særregler.",
  "kind": "tjekliste",
  "references": ["Kildeskatteloven §§ 43-49", "Arbejdsmarkedsbidragsloven", "Skatteindberetningsloven §§ 1 og 6", "Ligningsloven § 16 og § 16 A", "Ferieloven", "ATP-loven", "Lov om Arbejdsmarkedets Erhvervssikring (AES)"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "loenbogfoert", "label": "Bruttoløn iflg. bogføring (kr.)", "type": "number"},
    {"name": "loen_eindkomst", "label": "A-indkomst iflg. eIndkomst (kr.)", "type": "number"},
    {"name": "askat_bogfoert", "label": "A-skat iflg. bogføring (kr.)", "type": "number"},
    {"name": "askat_eindkomst", "label": "A-skat iflg. eIndkomst (kr.)", "type": "number"},
    {"name": "am_bogfoert", "label": "AM-bidrag iflg. bogføring (kr.)", "type": "number"},
    {"name": "am_eindkomst", "label": "AM-bidrag iflg. eIndkomst (kr.)", "type": "number"},
    {"name": "virksomhedsstoerrelse", "label": "Arbejdsgiver-kategori", "type": "select", "options": ["Lille (betaling den 10. i måneden efter)", "Stor (betaling sidste bankdag i måneden)"], "default": "Lille (betaling den 10. i måneden efter)"},
    {"name": "hovedaktionaer", "label": "Der er ansatte hovedaktionærer/direktører", "type": "checkbox"}
  ]
}
---
# A-skat, AM-bidrag og eIndkomst {{ regnskab.aar }}

**Kunde:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}
**Udarbejdet af:** {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Afstemning bogføring ↔ eIndkomst
| | Bogføring | eIndkomst | Difference | Forklaring |
|---|---|---|---|---|
| Bruttoløn / A-indkomst | {{ felt.loenbogfoert }} | {{ felt.loen_eindkomst }} | | |
| AM-bidrag (8 %) | {{ felt.am_bogfoert }} | {{ felt.am_eindkomst }} | | |
| A-skat | {{ felt.askat_bogfoert }} | {{ felt.askat_eindkomst }} | | |
| Personalegoder (felt 19/20 m.fl.) | | | | |
| B-indkomst (honorarer) | | | | |
| ATP | | | | |
| Pension (arbejdsgiver/medarbejder) | | | | |

Typiske afstemningsposter: periodisering af løn (fx løn for december udbetalt i januar), feriepenge (indbetaling til FerieKonto/feriepengeforpligtelse), refusioner (sygedagpenge, barsel), skattefri godtgørelser (rejse, kørsel), og korrektioner indberettet i det efterfølgende år.

## 2. Frister og betaling
- [ ] Kategori: **{{ felt.virksomhedsstoerrelse }}**. Små arbejdsgivere (samlet A-skat og AM-bidrag under ca. 250.000 kr. årligt) betaler senest den 10. i måneden efter lønmåneden; store arbejdsgivere senest sidste bankdag i lønmåneden. Indberetning til eIndkomst skal ske senest samtidig med betalingsfristen.
- [ ] Ingen for sene eller manglende indberetninger; renter og gebyrer på skattekontoen gennemgået.
- [ ] Korrektioner for tidligere perioder er indberettet som rettelser (ikke lagt i senere perioder).

## 3. Personalegoder og godtgørelser
- [ ] Fri bil: værdi beregnet af bilens nyvogns-/handelsværdi efter LL § 16, stk. 4 (inkl. miljøtillæg); indberettet månedligt. Kørselsregnskab, hvis det gøres gældende, at bilen ikke er til rådighed privat.
- [ ] Fri telefon/datakommunikation (3.500 kr. i 2026), fri sommerbolig, lystbåd, helårsbolig, sundhedsforsikring (skattefri hvis omfatter alle), kantineordning.
- [ ] Bagatelgrænser efter LL § 16 (2026: 7.600 kr. og 1.400 kr. – kontrollér, hvilken grænse der gælder for det konkrete gode; overskrides grænsen, beskattes hele beløbet); julegaver op til 1.000 kr. (2026) skattefrie.
- [ ] Skattefri rejse- og kørselsgodtgørelse: satser (2026: kørsel 3,94 kr./km op til 20.000 km og 2,28 kr. herover; kost 625 kr./døgn, logi 268 kr./nat) og dokumentationskrav (formål, dato, km, rute) opfyldt – ellers skattepligtig løn.
- [ ] Hjemmearbejdsplads, uddannelse og andre personalegoder vurderet efter LL § 16.

{% if felt.hovedaktionaer %}
## 4. Hovedaktionærer og direktører
- [ ] Løn til hovedaktionær er indberettet og afstemt; tantieme og bonus periodiseret korrekt (beskattes ved udbetaling/retserhvervelse).
- [ ] Fri bil, fri bolig (særlige regler for hovedaktionærer, LL § 16, stk. 9), fri telefon m.v. indberettet.
- [ ] Mellemregning med selskabet: hævninger behandles som løn eller udbytte (LL § 16 E); private udgifter afholdt af selskabet er beskattet.
- [ ] Løn er markedskonform og forretningsmæssigt begrundet (fradragsret i selskabet).
- [ ] Afvejning løn/udbytte for året udarbejdet (se særskilt arbejdspapir).
{% endif %}

## 5. Øvrige lønafledte forpligtelser
- [ ] ATP indbetalt efter timesatser; AES, barsel.dk (Barselsfonden) og Arbejdsmarkedets Tillægspension afstemt.
- [ ] Feriepenge: forpligtelse efter ferieloven (samtidighedsferie) opgjort og bogført; 5. ferieuge og feriefridage.
- [ ] Ansatte med skattekort: A-skat beregnet efter seneste skattekort; ansatte uden skattekort trækkes 55 %.
{% if branche.byggeri or branche.rengoering or branche.vikar %}- [ ] **Branche:** Udenlandsk arbejdskraft og underentreprenører: RUT, arbejdsudlejning (skat ved arbejdsudleje, KSL § 2, stk. 1, nr. 3) og kædeansvar vurderet.
{% endif %}{% if branche.restauration or branche.hotel %}- [ ] **Branche:** Drikkepenge, fri kost og personalemad indberettet korrekt; timeregistrering afstemt til løn (Skattestyrelsens kontrolindsats).
{% endif %}{% if branche.momsfritaget %}- [ ] Lønsummen anvendes også til lønsumsafgift – afstem lønsum til lønsumsafgiftsangivelsen.
{% endif %}

## 6. Konklusion
- [ ] Afstemt uden væsentlige differencer.
- [ ] Fejl korrigeret i eIndkomst den \_\_\_\_\_\_.
