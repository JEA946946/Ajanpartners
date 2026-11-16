---
{
  "title": "Kundekendskab (KYC) – juridisk person",
  "description": "Skema til kundekendskabsprocedurer for selskaber, foreninger, fonde og andre juridiske personer efter hvidvasklovens §§ 10-18: identitet, kontrol, ejerstruktur, reelle ejere, ledelse, PEP, sanktionsscreening, formål og tilsigtet beskaffenhed.",
  "kind": "tjekliste",
  "references": ["Hvidvaskloven (LBK nr. 433 af 17/04/2026) §§ 2 nr. 6-9, 10, 11, 14, 17, 18, 21 og 30", "Erhvervsstyrelsens vejledning om hvidvaskloven", "Erhvervsstyrelsens vejledning om vurdering af formål og tilsigtet beskaffenhed (oktober 2026)", "EU-forordning 2024/1624 (AMLR) – anvendes fra 10. juli 2027"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "forening", "is", "pmv", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "type", "label": "Anledning", "type": "select", "options": ["Etablering af ny forretningsforbindelse", "Periodisk opdatering", "Ændrede forhold", "Tvivl om tidligere oplysninger"], "default": "Etablering af ny forretningsforbindelse"},
    {"name": "ydelser", "label": "Ydelser kunden modtager", "type": "text"},
    {"name": "kontaktperson", "label": "Kundens kontaktperson (navn og rolle)", "type": "text"},
    {"name": "henvist_af", "label": "Hvordan er kunden kommet til os (henvisning m.v.)", "type": "text"},
    {"name": "risiko", "label": "Risikoklassifikation (fra risikovurdering)", "type": "select", "options": ["Lav", "Normal", "Forhøjet", "Høj"], "default": "Normal"},
    {"name": "fysisk_moede", "label": "Kunden/kontaktperson er mødt fysisk eller identificeret via MitID", "type": "checkbox", "default": true}
  ]
}
---
# Kundekendskab – juridisk person

| | |
|---|---|
| Kunde | {{ kunde.navn }} |
| CVR-nr. | {{ kunde.cvr }} |
| Selskabsform | {{ kunde.selskabsform }} |
| Hjemsted/adresse | {{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }} |
| Branche (CVR) | {{ kunde.branchekode }} {{ kunde.branchetekst }} – brancherisiko: **{{ branche.hvidvask_risiko }}** |
| Anledning | {{ felt.type }} |
| Ydelser | {{ felt.ydelser }} |
| Kontaktperson | {{ felt.kontaktperson }} |
| Kundeansvarlig | {{ kunde.ansvarlig }} |
| Udfyldt af / dato | {{ medarbejder.navn }} / {{ dato.idag }} |

Kundekendskabsprocedurerne skal være gennemført, **før** forretningsforbindelsen etableres (hvidvasklovens § 14). Kan procedurerne ikke gennemføres, må forbindelsen ikke etableres, og en eksisterende forbindelse skal afsluttes. Det skal samtidig vurderes, om der skal ske underretning til Hvidvasksekretariatet.

## 1. Identitetsoplysninger (§ 11, stk. 1, nr. 1)

- [ ] Navn og CVR-nr. indhentet
- [ ] Udskrift fra CVR (virk.dk/datacvr.virk.dk) gemt – dato: ________
- [ ] Vedtægter/stiftelsesdokument gemt (for foreninger: vedtægter og referat fra seneste generalforsamling)
- [ ] Seneste årsrapport gennemgået (hvis eksisterende virksomhed)
- [ ] Udenlandsk juridisk person: registreringsbevis fra hjemlandets register, oversat hvis nødvendigt

## 2. Kontrol af identitet (§ 11, stk. 1, nr. 2)

Oplysningerne kontrolleres på grundlag af dokumenter, data eller oplysninger fra en pålidelig og uafhængig kilde.

| Oplysning | Kilde | Kontrolleret | Bemærkning |
|---|---|---|---|
| Navn, CVR-nr., adresse | CVR-registret | ☐ | |
| Status (aktiv, under tvangsopløsning, konkurs) | CVR / Statstidende | ☐ | |
| Tegningsregel | CVR | ☐ | |
| Revisor/tidligere revisor | CVR | ☐ | |
| Adressen eksisterer og er ikke en "skuffeadresse" | Søgning, besøg | ☐ | |

## 3. Ledelse og tegningsberettigede

| Navn | Rolle | Fødselsdato | Legitimation (pas/kørekort/MitID) | Kontrolleret | PEP? |
|---|---|---|---|---|---|
| | {% if kunde.selskabsform_kode == "as" %}Bestyrelsesformand{% else %}Direktør{% endif %} | | | ☐ | ☐ Ja ☐ Nej |
| | | | | ☐ | ☐ Ja ☐ Nej |
| | | | | ☐ | ☐ Ja ☐ Nej |

Personen, der handler på kundens vegne (kontaktpersonen), er identificeret, og dennes fuldmagt/bemyndigelse er kontrolleret: ☐

{% if not felt.fysisk_moede %}> **Kunden er ikke mødt fysisk og ikke identificeret via MitID.** Det er en risikofaktor. Anvend supplerende kontrol (fx videomøde med fremvisning af legitimation, kopi af pas med selfie, første betaling fra konto i kundens navn i et EU-pengeinstitut).{% endif %}

## 4. Ejerstruktur og reelle ejere (§ 11, stk. 1, nr. 3, og § 2, nr. 9)

Reel ejer er den eller de fysiske personer, der i sidste ende direkte eller indirekte ejer eller kontrollerer kunden. Ejerskab af mere end 25 % af kapitalen eller stemmerne er en indikation af ejerskab, men kontrol kan også udøves på anden måde (aftaler, vetoret, ret til at udpege ledelse, nærtstående, der handler sammen).

- [ ] Ejerstruktur kortlagt helt op til fysiske personer (vedlæg organisationsdiagram ved flere led)
- [ ] Reelle ejere registreret i CVR sammenholdt med kundens egne oplysninger (erklæring om reelle ejere)
- [ ] Uoverensstemmelser mellem CVR og vores oplysninger håndteret og indberettet til Erhvervsstyrelsen
- [ ] Ejerbog/aktiebog eller ejerfortegnelse set (for {{ kunde.selskabsform }})

| Reel ejer | Fødselsdato/land | Ejerandel/stemmer (direkte/indirekte) | Grundlag for kontrol | Identitet kontrolleret (kilde) | PEP? |
|---|---|---|---|---|---|
| | | % | | | ☐ Ja ☐ Nej |
| | | % | | | ☐ Ja ☐ Nej |
| | | % | | | ☐ Ja ☐ Nej |

Kan der ikke identificeres en reel ejer, eller er der tvivl, registreres personerne i den daglige ledelse som reelle ejere. Det skal dokumenteres, hvilke skridt der er taget for at identificere de reelle ejere: ________________________________________

{% if branche.holding or kunde.selskabsform_kode == "holding" %}> **Holdingstruktur:** Kortlæg alle mellemliggende selskaber. Udenlandske led, trusts, fonde eller nominee-aktionærer kræver skærpet kontrol og forklaring af strukturens formål.{% endif %}
{% if kunde.selskabsform_kode == "forening" or branche.forening %}> **Forening/NPO:** Bestyrelsen og eventuelle personer med reel kontrol registreres som reelle ejere. Vurdér også, hvem der modtager foreningens midler (særligt indsamlinger og overførsler til udlandet – risiko for terrorfinansiering).{% endif %}

## 5. PEP og sanktioner (§ 18)

- [ ] Ledelse, reelle ejere og kontaktperson screenet mod Finanstilsynets PEP-liste (danske PEP'er) og offentlige kilder (udenlandske PEP'er) – dato: ________
- [ ] Underskrevet PEP-erklæring modtaget
- [ ] Screening mod EU's konsoliderede sanktionsliste og FN's sanktionsliste – dato: ________ – resultat: ________
- [ ] Negativ mediesøgning (navn + "svindel", "dom", "konkurs", "hvidvask") – resultat: ________

Er en person PEP, nærtstående eller nær samarbejdspartner: ledelsens/den ansvarliges godkendelse, fastlæggelse af midlernes og formuens oprindelse og skærpet løbende overvågning (§ 18).

## 6. Formål og tilsigtet beskaffenhed (§ 11, stk. 1, nr. 4)

Standardformuleringer er ikke tilstrækkelige – beskriv den konkrete kunde.

| Emne | Kundens oplysninger og vores vurdering |
|---|---|
| Hvilke ydelser ønskes, og hvorfor? Passer de til kundens behov og branche? | |
| Hvorfor har kunden valgt os (henvisning, geografi, tidligere relation)? {{ felt.henvist_af }} | |
| Forretningsmodel og indtjening: produkter, kunder, leverandører, geografi | |
| Forventet omsætning, antal ansatte og lønudgift – står det mål med aktiviteten? | |
| Kontanter: andel af omsætningen, kontant betaling til leverandører | |
| Import/eksport, handel med højrisikolande eller sanktionerede lande | |
| Midlernes oprindelse: stiftelseskapital, kapitalforhøjelser, apportindskud, lån fra ejere, finansiering af aktiver | |
| Forbrug og aktiver hos ejere i forhold til virksomhedens indtjening | |
| Tidligere revisor/bogholder og grunden til skiftet | |

{% if branche.kontantintensiv %}> **Kontantintensiv branche:** Dokumentér kassesystem, kasseafstemning og hvor kontanterne indsættes. Er kontantandelen atypisk høj eller lav for branchen?{% endif %}
{% if branche.byggeri or branche.rengoering or branche.vikar or branche.transport %}> **Arbejdskraftintensiv branche:** Kontrollér antal ansatte og lønsum mod omsætningen, brug af underleverandører (CVR-alder, adresse, ledelse), udenlandsk arbejdskraft og RUT-registrering. Risiko for sort løn og fakturafabrikker.{% endif %}
{% if branche.ejendom %}> **Fast ejendom:** Dokumentér finansieringen af ejendomskøb (bank, egne midler, udenlandske lån) og lejeindtægternes realisme.{% endif %}
{% if branche.bilhandel %}> **Bilhandel:** Dokumentér køb/salg til og fra udlandet, kontant handel, eksport af biler og brugtmomsordning.{% endif %}

## 7. Konklusion

| | |
|---|---|
| Risikoklassifikation | **{{ felt.risiko }}** (se særskilt risikovurdering) |
| Procedure | ☐ Lempet (§ 21) ☐ Normal (§ 11) ☐ Skærpet (§ 17/§ 18) |
| Næste opdatering af kundekendskab | ☐ 1 år ☐ 2 år ☐ 3 år ☐ ved ændrede forhold |
| Kundeforholdet kan etableres/fortsætte | ☐ Ja ☐ Ja, med betingelser ☐ Nej |
| Usædvanlige forhold, der kræver undersøgelse efter § 25 | ☐ Nej ☐ Ja – se notat |

Dokumentationen opbevares i mindst 5 år efter forretningsforbindelsens ophør (§ 30).

| Rolle | Navn | Dato | Underskrift |
|---|---|---|---|
| Udfyldt af | {{ medarbejder.navn }} | {{ dato.idag }} | |
| Godkendt (partner/hvidvaskansvarlig ved forhøjet/høj risiko eller PEP) | | | |
