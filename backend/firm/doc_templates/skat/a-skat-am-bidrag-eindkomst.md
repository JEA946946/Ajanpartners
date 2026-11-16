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
    {"name": "virksomhedsstoerrelse", "label": "Arbejdsgiver-kategori (jf. registreringsbevis i TastSelv Erhverv)", "type": "select", "options": ["Små og mellemstore virksomheder (SMV)", "Fremrykket betaling – stor virksomhed"], "default": "Små og mellemstore virksomheder (SMV)"},
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
| AM-bidrag (8 % i 2026) | {{ felt.am_bogfoert }} | {{ felt.am_eindkomst }} | | |
| A-skat | {{ felt.askat_bogfoert }} | {{ felt.askat_eindkomst }} | | |
| Personalegoder (felt 19/20 m.fl.) | | | | |
| B-indkomst (honorarer) | | | | |
| ATP | | | | |
| Pension (arbejdsgiver/medarbejder) | | | | |

Typiske afstemningsposter: periodisering af løn (fx løn for december udbetalt i januar), feriepenge (indbetaling til FerieKonto/feriepengeforpligtelse), refusioner (sygedagpenge, barsel), skattefri godtgørelser (rejse, kørsel), og korrektioner indberettet i det efterfølgende år.

## 2. Frister og betaling
- [ ] Kategori: **{{ felt.virksomhedsstoerrelse }}** (fremgår af virksomhedens registreringsbevis i TastSelv Erhverv). Frister for indberetning til eIndkomst og betaling af A-skat og AM-bidrag kontrolleres for kategorien i Skattestyrelsens fristkalender (skat.dk »Betaling og frister«).
- [ ] Ingen for sene eller manglende indberetninger; renter og gebyrer på skattekontoen gennemgået.
- [ ] Korrektioner for tidligere perioder er indberettet som rettelser (ikke lagt i senere perioder).

## 3. Personalegoder og godtgørelser
- [ ] Fri bil: værdi beregnet af bilens nyvogns-/handelsværdi efter LL § 16, stk. 4 (inkl. miljøtillæg); indberettet månedligt. Kørselsregnskab, hvis det gøres gældende, at bilen ikke er til rådighed privat.
- [ ] Fri telefon (skattepligtig værdi 3.500 kr. i 2026, LL § 16, stk. 12), fri sommerbolig, lystbåd, helårsbolig, sundhedsforsikring (skattefri hvis omfatter alle), kantineordning.
- [ ] Bagatelgrænser efter LL § 16, stk. 3 (2026): 1.400 kr. for mindre personalegoder i alt pr. år og 7.300 kr. for goder stillet til rådighed overvejende af hensyn til arbejdet; overstiger godernes samlede værdi grænsen, beskattes hele værdien. Julegaver op til 1.000 kr. (2026) skattefrie.
- [ ] Skattefri rejse- og kørselsgodtgørelse: satser (2026: kørsel 3,94 kr./km op til 20.000 km og 2,28 kr. herover; kost 625 kr./døgn, logi 268 kr./nat) og dokumentationskrav (formål, dato, km, rute) opfyldt – ellers skattepligtig løn.
- [ ] Hjemmearbejdsplads, uddannelse og andre personalegoder vurderet efter LL § 16.

{% if felt.hovedaktionaer %}
## 4. Hovedaktionærer og direktører
- [ ] Løn til hovedaktionær er indberettet og afstemt; tantieme og bonus periodiseret korrekt (beskattes ved udbetaling/retserhvervelse).
- [ ] Fri bil, fri bolig (særlige regler for hovedaktionærer og direktører efter LL § 16), fri telefon m.v. indberettet.
- [ ] Mellemregning med selskabet: hævninger behandles som løn eller udbytte (LL § 16 E); private udgifter afholdt af selskabet er beskattet.
- [ ] Løn er markedskonform og forretningsmæssigt begrundet (fradragsret i selskabet).
- [ ] Afvejning løn/udbytte for året udarbejdet (se særskilt arbejdspapir).
{% endif %}

## 5. Øvrige lønafledte forpligtelser
- [ ] ATP indbetalt efter timesatser; AES, barsel.dk (Barselsfonden) og Arbejdsmarkedets Tillægspension afstemt.
- [ ] Feriepenge: forpligtelse efter ferieloven (samtidighedsferie) opgjort og bogført; 5. ferieuge og feriefridage.
- [ ] Ansatte med skattekort: A-skat beregnet efter seneste skattekort; ved manglende skattekort indeholdes 55 % (kildeskattelovens § 48, stk. 8).
{% if branche.byggeri or branche.rengoering or branche.vikar %}- [ ] **Branche:** Udenlandsk arbejdskraft og underentreprenører: RUT, skattepligt for udenlandsk arbejdskraft efter kildeskatteloven (herunder arbejdsudleje) og kædeansvar vurderet.
{% endif %}{% if branche.restauration or branche.hotel %}- [ ] **Branche:** Drikkepenge, fri kost og personalemad indberettet korrekt; timeregistrering afstemt til løn (Skattestyrelsens kontrolindsats).
{% endif %}{% if branche.momsfritaget %}- [ ] Lønsummen anvendes også til lønsumsafgift – afstem lønsum til lønsumsafgiftsangivelsen.
{% endif %}

## 6. Konklusion
- [ ] Afstemt uden væsentlige differencer.
- [ ] Fejl korrigeret i eIndkomst den \_\_\_\_\_\_.
