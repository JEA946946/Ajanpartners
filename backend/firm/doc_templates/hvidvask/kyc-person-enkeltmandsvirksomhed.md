---
{
  "title": "Kundekendskab (KYC) – fysisk person og enkeltmandsvirksomhed",
  "description": "Skema til kundekendskabsprocedurer for personer, enkeltmandsvirksomheder, I/S og personligt ejede virksomheder: identitet, kontrol, PEP, sanktioner, formål, midlernes oprindelse og privatøkonomi.",
  "kind": "tjekliste",
  "references": ["Hvidvaskloven (LBK nr. 433 af 17/04/2026) §§ 10, 11, 14, 16, 17, 18 og 30", "Erhvervsstyrelsens vejledning om hvidvaskloven", "Erhvervsstyrelsens vejledning om vurdering af formål og tilsigtet beskaffenhed (oktober 2026)"],
  "legal_forms": ["enk", "is", "pmv", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "type", "label": "Anledning", "type": "select", "options": ["Etablering af ny forretningsforbindelse", "Periodisk opdatering", "Ændrede forhold", "Tvivl om tidligere oplysninger"], "default": "Etablering af ny forretningsforbindelse"},
    {"name": "personnavn", "label": "Kundens fulde navn (person)", "type": "text"},
    {"name": "foedselsdato", "label": "Fødselsdato", "type": "date"},
    {"name": "statsborgerskab", "label": "Statsborgerskab", "type": "text", "default": "Dansk"},
    {"name": "ydelser", "label": "Ydelser kunden modtager", "type": "text"},
    {"name": "legitimation", "label": "Legitimation", "type": "select", "options": ["MitID (digital identifikation)", "Pas", "Kørekort + sundhedskort", "Udenlandsk pas/ID-kort + opholdsdokument"], "default": "MitID (digital identifikation)"},
    {"name": "risiko", "label": "Risikoklassifikation", "type": "select", "options": ["Lav", "Normal", "Forhøjet", "Høj"], "default": "Normal"}
  ]
}
---
# Kundekendskab – fysisk person / personligt ejet virksomhed

| | |
|---|---|
| Kunde (person) | {{ felt.personnavn }} |
| Fødselsdato / statsborgerskab | {{ felt.foedselsdato }} / {{ felt.statsborgerskab }} |
| Virksomhed | {{ kunde.navn }} ({{ kunde.selskabsform }}), CVR-nr. {{ kunde.cvr }} |
| Adresse | {{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }} |
| Branche | {{ kunde.branchekode }} {{ kunde.branchetekst }} – brancherisiko: **{{ branche.hvidvask_risiko }}** |
| Anledning / ydelser | {{ felt.type }} / {{ felt.ydelser }} |
| Udfyldt af / dato | {{ medarbejder.navn }} / {{ dato.idag }} |

Procedurerne skal være gennemført, før forretningsforbindelsen etableres (§ 14). Kunden skal informeres om behandlingen af personoplysninger efter hvidvaskloven, før forbindelsen etableres (§ 16).

## 1. Identitetsoplysninger og kontrol (§ 11, stk. 1, nr. 1-2)

| Oplysning | Indhentet | Kontrolleret mod | ✔ |
|---|---|---|---|
| Fulde navn | | Legitimation: {{ felt.legitimation }} | ☐ |
| CPR-nr. (eller fødselsdato og nationalitet ved udenlandsk kunde) | | CPR/legitimation | ☐ |
| Adresse | | CPR-adresse, sundhedskort, offentlig post | ☐ |
| Virksomhedens CVR-nr. og status | | CVR-registret | ☐ |
| {% if kunde.selskabsform_kode == "is" %}Alle interessenter identificeret (hver interessent behandles som reel ejer){% else %}Ejer identisk med registreret indehaver i CVR{% endif %} | | CVR | ☐ |

Kopi af legitimation gemt sikkert (adgang begrænset): ☐  Gyldighedsdato: ________

{% if kunde.selskabsform_kode == "is" %}
| Interessent | Fødselsdato | Ejerandel | Legitimation kontrolleret | PEP? |
|---|---|---|---|---|
| | | % | ☐ | ☐ Ja ☐ Nej |
| | | % | ☐ | ☐ Ja ☐ Nej |
{% endif %}

## 2. Handler kunden på egne vegne?

- [ ] Kunden handler på egne vegne. Hvis nej: identificér den person, der handles for (reel ejer), og kontrollér fuldmagt.
- [ ] Ingen indikationer på stråmandsforhold (fx ejer uden branchekendskab, tredjemand fører samtalen, betaling fra andres konti).

## 3. PEP og sanktioner (§ 18)

- [ ] PEP-erklæring underskrevet
- [ ] Kontrolleret mod Finanstilsynets PEP-liste – dato: ________ resultat: ________
- [ ] Screening mod EU's og FN's sanktionslister – dato: ________ resultat: ________
- [ ] Negativ mediesøgning, Statstidende (konkurser, dødsboer, tvangsauktioner) – resultat: ________

## 4. Formål, tilsigtet beskaffenhed og privatøkonomi (§ 11, stk. 1, nr. 4)

| Emne | Kundens oplysninger og vores vurdering |
|---|---|
| Hvilke ydelser ønskes, og hvorfor? Hvorfor os? | |
| Virksomhedens aktivitet, kunder, leverandører, geografi | |
| Forventet omsætning og indtjening; står det mål med aktiviteten? | |
| Andre indkomstkilder (løn, pension, udlejning, investeringer) | |
| Midlernes oprindelse ved opstart og investeringer (opsparing, lån, arv, gave, salg) | |
| Privatforbrug og aktiver (bolig, biler, både) i forhold til indkomsten | |
| Kontanter i virksomheden eller privat | |
| Udenlandske konti, ejendomme eller indkomst | |
| Tidligere rådgiver og grunden til skiftet | |

{% if branche.kontantintensiv %}> **Kontantintensiv branche:** Beregn et sandsynligt privatforbrug og sammenhold det med virksomhedens overskud. Dokumentér kasserutiner og indsættelse af kontanter.{% endif %}
{% if branche.byggeri or branche.rengoering or branche.transport %}> **Arbejdskraftintensiv branche:** Vurdér omsætning pr. ansat og brug af underleverandører. Spørg til, hvem der udfører arbejdet, hvis der ikke er ansatte.{% endif %}
{% if branche.bilhandel %}> **Bilhandel:** Spørg til køb fra udlandet, kontant handel og opbevaring af biler.{% endif %}
{% if branche.personlig_service %}> **Personlig service (frisør, skønhed m.v.):** Kontantandel og antal stole/behandlere sammenholdt med omsætningen.{% endif %}

## 5. Konklusion

| | |
|---|---|
| Risikoklassifikation | **{{ felt.risiko }}** |
| Procedure | ☐ Lempet ☐ Normal ☐ Skærpet |
| Næste opdatering | ☐ 1 år ☐ 2 år ☐ 3 år ☐ ved ændrede forhold |
| Kundeforholdet kan etableres/fortsætte | ☐ Ja ☐ Ja, med betingelser ☐ Nej |
| Forhold, der kræver undersøgelse efter § 25 | ☐ Nej ☐ Ja – se notat |

Opbevares i mindst 5 år efter forretningsforbindelsens ophør (§ 30).

| Rolle | Navn | Dato | Underskrift |
|---|---|---|---|
| Udfyldt af | {{ medarbejder.navn }} | {{ dato.idag }} | |
| Godkendt (ved forhøjet/høj risiko eller PEP) | | | |
