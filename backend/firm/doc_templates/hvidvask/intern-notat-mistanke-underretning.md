---
{
  "title": "Internt notat – undersøgelse af mistanke og underretning til Hvidvasksekretariatet",
  "description": "Fortroligt internt notat om undersøgelse efter hvidvasklovens § 25 og beslutning om underretning efter § 26 til Hvidvasksekretariatet (goAML), med tavshedspligt efter § 38 – kunden må ikke advares.",
  "kind": "arbejdspapir",
  "references": ["Hvidvaskloven (LBK nr. 433 af 17/04/2026) §§ 25, 26, 27, 30, 37 og 38", "Hvidvaskloven § 3 (definition af hvidvask)", "Revisorloven § 22, stk. 1, 4. pkt.", "Hvidvasksekretariatets brugervejledning til goAML"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "sagsnr", "label": "Internt sagsnr.", "type": "text"},
    {"name": "opdaget_af", "label": "Forholdet er konstateret af", "type": "text", "default": "{{ medarbejder.navn }}"},
    {"name": "opdaget_dato", "label": "Dato for konstatering", "type": "date"},
    {"name": "beskrivelse", "label": "Beskrivelse af transaktion/aktivitet (hvem, hvad, hvornår, beløb, konti)", "type": "textarea"},
    {"name": "indikatorer", "label": "Hvorfor er forholdet usædvanligt/mistænkeligt?", "type": "textarea"},
    {"name": "undersoegelse", "label": "Udførte undersøgelser og resultat (§ 25)", "type": "textarea"},
    {"name": "beslutning", "label": "Beslutning", "type": "select", "options": ["Mistanken er afkræftet – ingen underretning", "Underretning til Hvidvasksekretariatet (SAR – mistænkelig aktivitet)", "Underretning til Hvidvasksekretariatet (STR – mistænkelig transaktion)", "Underretning om mulig terrorfinansiering – straks"], "default": "Underretning til Hvidvasksekretariatet (SAR – mistænkelig aktivitet)"},
    {"name": "begrundelse", "label": "Begrundelse for beslutningen", "type": "textarea"},
    {"name": "hvidvaskansvarlig", "label": "Hvidvaskansvarlig", "type": "text"},
    {"name": "underretning_dato", "label": "Dato for underretning", "type": "date"},
    {"name": "goaml_ref", "label": "goAML-referencenummer", "type": "text"},
    {"name": "kundeforhold_fremover", "label": "Kundeforholdet fremover", "type": "select", "options": ["Fortsætter med skærpet overvågning", "Afvikles (efter drøftelse med Hvidvasksekretariatet)", "Afventer"], "default": "Fortsætter med skærpet overvågning"}
  ]
}
---
# FORTROLIGT – internt notat om mistanke om hvidvask/terrorfinansiering

> **Må ikke lægges i den almindelige kundemappe, deles med kunden eller nævnes over for kunden.** Notatet opbevares i hvidvaskmappen med adgang begrænset til hvidvaskansvarlig og partner. Der er pligt til at hemmeligholde, at der er givet underretning, eller at det overvejes, eller at der er eller vil blive iværksat en undersøgelse (hvidvasklovens § 38, stk. 1).

| | |
|---|---|
| Sagsnr. | {{ felt.sagsnr }} |
| Kunde | {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }} |
| Kundeansvarlig | {{ kunde.ansvarlig }} |
| Konstateret af / dato | {{ felt.opdaget_af }} / {{ felt.opdaget_dato }} |
| Hvidvaskansvarlig | {{ felt.hvidvaskansvarlig }} |
| Notat udarbejdet | {{ medarbejder.navn }}, {{ dato.idag }} |

## 1. Hvad er konstateret

{{ felt.beskrivelse }}

## 2. Hvorfor er forholdet usædvanligt

{{ felt.indikatorer }}

Typiske indikatorer: transaktioner uden åbenbart økonomisk eller lovligt formål; beløb eller mønstre, der ikke passer til kundens forretning; kontantindsætninger uden forklaring; fakturaer fra leverandører uden reel aktivitet; betalinger fra/til tredjemand eller højrisikolande; kunden vil ikke forklare eller dokumentere; ændringer i ejerskab, der skjuler reelle ejere; privatforbrug, der ikke står mål med indtjeningen.

## 3. Undersøgelse (§ 25)

Baggrunden for og formålet med alle transaktioner, der er komplekse, usædvanligt store, foretages i et usædvanligt mønster eller ikke har et åbenbart økonomisk eller lovligt formål, og alle usædvanlige aktiviteter uden åbenbart økonomisk eller lovligt formål skal undersøges. Overvågningen skal om nødvendigt udvides, og resultatet skal noteres og opbevares (§ 25, stk. 1-3).

Undersøgelsen kan omfatte gennemgang af bilag, kontoudtog, kontrakter, CVR-oplysninger om modparter og offentlige kilder. Spørgsmål til kunden må stilles som en del af det almindelige arbejde, men **må ikke afsløre, at der er mistanke** eller undersøgelse.

{{ felt.undersoegelse }}

## 4. Vurdering og beslutning (§ 26)

Virksomheden skal **omgående** underrette Hvidvasksekretariatet, hvis den er vidende om, har mistanke om eller rimelig grund til at formode, at en transaktion, midler eller en aktivitet har eller har haft tilknytning til hvidvask eller finansiering af terrorisme (§ 26, stk. 1). Der kræves ikke vished. Hvidvask omfatter også dispositioner foretaget af den, der selv har begået den strafbare lovovertrædelse, som udbyttet hidrører fra (§ 3, stk. 2), fx udbytte af skatte- eller momssvig.

- [ ] Mistanken kan afkræftes fuldstændigt – begrundelse noteret
- [ ] Mistanken kan ikke afkræftes – underretning skal ske
- [ ] Oplysningerne er modtaget, mens vi repræsenterer kunden i Landsskatteretten (§ 27, stk. 2), eller mens vi bistår en advokat med at fastslå kundens retsstilling eller i en retssag (§ 27, stk. 3) – drøftes med hvidvaskansvarlig. Undtagelsen gælder ikke, hvis vi ved eller burde vide, at kunden søger bistand til hvidvask eller terrorfinansiering (§ 27, stk. 4)
- [ ] Revisorlovens § 22 (ledelsens økonomiske kriminalitet) gælder ikke forhold, der er omfattet af hvidvaskloven (§ 22, stk. 1, 4. pkt.). Vurdér særskilt, om der er andre forhold hos ledelsen, der er omfattet af § 22

**Beslutning:** {{ felt.beslutning }}

**Begrundelse:** {{ felt.begrundelse }}

## 5. Underretning

- [ ] Underretning indsendt via goAML (hvidvask.politi.dk) den {{ felt.underretning_dato }} – reference: {{ felt.goaml_ref }}
- [ ] Underretningen indeholder: kundens identitetsoplysninger, beskrivelse af aktivitet/transaktioner, hvorfor de er mistænkelige, og relevante bilag
- [ ] Ved transaktioner, som vi selv skal medvirke til (fx betalinger via klientkonto): transaktionen er standset, indtil underretning er sket (§ 26, stk. 3). Ved mistanke om terrorfinansiering må transaktionen ikke gennemføres, før Hvidvasksekretariatet har givet godkendelse (§ 26, stk. 6)
- [ ] Kvittering fra goAML gemt
- [ ] Eventuel henvendelse fra Hvidvasksekretariatet besvaret inden for fristen

Underretning i god tro medfører ikke ansvar for virksomheden eller medarbejderne og er ikke brud på tavshedspligten (§ 37).

## 6. Kundeforholdet fremover

**{{ felt.kundeforhold_fremover }}**

- Fortsæt som udgangspunkt arbejdet som normalt, så kunden ikke advares.
- Skærpet overvågning: nye usædvanlige forhold registreres og kan føre til ny underretning.
- Afvikling af kundeforholdet skal ske på en måde, der ikke afslører underretningen. Begrundelsen over for kunden formuleres neutralt. Overvej at drøfte afviklingen med Hvidvasksekretariatet.
- Afgiver vi erklæring på regnskabet, vurderes konsekvenserne for erklæringen (ISA 250/ISA 240) uden at nævne underretningen.

## 7. Opbevaring

Notat, undersøgelsesmateriale og kopi af underretningen opbevares i mindst 5 år efter forretningsforbindelsens ophør (§ 30, stk. 1, nr. 3, og stk. 2) adskilt fra kundemappen.

| Rolle | Navn | Dato | Underskrift |
|---|---|---|---|
| Udarbejdet af | {{ medarbejder.navn }} | {{ dato.idag }} | |
| Hvidvaskansvarlig | {{ felt.hvidvaskansvarlig }} | | |
