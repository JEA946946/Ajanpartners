---
{
  "title": "PEP-erklæring (politisk eksponeret person)",
  "description": "Erklæring, som kunden, ledelsen og reelle ejere udfylder om, hvorvidt de er politisk eksponerede personer, nærtstående eller nære samarbejdspartnere til en PEP (hvidvasklovens § 2, nr. 6-8, og § 18).",
  "kind": "brev",
  "references": ["Hvidvaskloven (LBK nr. 433 af 17/04/2026) § 2, nr. 6-8, og § 18", "PEP-bekendtgørelsen (BEK nr. 658 af 30/05/2023)", "Finanstilsynets PEP-liste", "Finanstilsynets vejledning til reglerne om politisk eksponerede personer"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "antal_personer", "label": "Antal personer der skal erklære (vises som rækker)", "type": "select", "options": ["1", "2", "3", "4"], "default": "2"}
  ]
}
---
# Erklæring om politisk eksponerede personer (PEP)

**Kunde:** {{ kunde.navn }}{% if kunde.cvr %}, CVR-nr. {{ kunde.cvr }}{% endif %}

{{ firma.navn }} er omfattet af hvidvaskloven og skal derfor undersøge, om vores kunder, deres ledelse og reelle ejere er politisk eksponerede personer (PEP), nærtstående til en PEP eller nære samarbejdspartnere til en PEP (§ 18). Vi beder derfor hver af de nævnte personer udfylde og underskrive denne erklæring. Er svaret "ja", betyder det ikke, at vi ikke kan samarbejde med jer, men vi skal indhente yderligere oplysninger, bl.a. om midlernes og formuens oprindelse.

## Hvem er PEP?

En **politisk eksponeret person** er en person, der har eller har haft et af følgende hverv (hvidvasklovens § 2, nr. 8), i Danmark eller i udlandet:

1. statschef, regeringschef, minister, viceminister eller assisterende minister og særlig rådgiver for en minister;
2. parlamentsmedlem eller medlem af et tilsvarende lovgivende organ;
3. medlem af et politisk partis styrelsesorgan;
4. højesteretsdommer, medlem af forfatningsdomstolen og af anden højtstående retsinstans, hvis afgørelser kun er genstand for yderligere prøvelse under ekstraordinære omstændigheder;
5. medlem af revisionsret og øverste ledelsesorgan for en centralbank;
6. ambassadør, chargé d'affaires eller højtstående officer i de væbnede styrker;
7. medlem af en statsejet virksomheds eller en statslig styrelses administrative, ledende eller kontrollerende organ;
8. direktør, vicedirektør, medlem af bestyrelsen eller person med tilsvarende hverv i en international organisation.

I Danmark omfatter det bl.a. ministre, særlige rådgivere, departementschefer, folketingsmedlemmer, danske medlemmer af Europa-Parlamentet, medlemmer af partiernes styrelsesorganer, højesteretsdommere, nationalbankdirektører, ambassadører, officerer med tjenestegraden generalmajor/kontreadmiral eller højere samt direktion og bestyrelse i statsejede virksomheder. Finanstilsynet fører og offentliggør en liste over indenlandske PEP'er (PEP-bekendtgørelsen, BEK nr. 658 af 30/05/2023).

Når en person ophører med hvervet, skal vi i mindst 12 måneder derefter vurdere, om personen fortsat udgør en øget risiko, og anvende skærpede procedurer, indtil det ikke længere vurderes at være tilfældet (§ 18, stk. 6).

**Nærtstående** (§ 2, nr. 6) er en PEP's ægtefælle, registrerede partner eller samlever, børn og deres ægtefæller, registrerede partnere eller samlevere samt forældre.

**Nær samarbejdspartner** (§ 2, nr. 7) er en person, der sammen med en PEP er reel ejer af en virksomhed eller har en anden nær forretningsforbindelse til en PEP, eller som er eneste reelle ejer af en virksomhed, som det vides er oprettet til fordel for en PEP.

## Erklæring

Jeg erklærer på tro og love, at oplysningerne nedenfor er korrekte, og at jeg straks vil give {{ firma.navn }} besked, hvis forholdene ændrer sig.

{% if felt.antal_personer == "1" or felt.antal_personer == "2" or felt.antal_personer == "3" or felt.antal_personer == "4" %}
### Person 1

| | |
|---|---|
| Navn | |
| Fødselsdato | |
| Rolle hos kunden (ejer, direktør, bestyrelsesmedlem, reel ejer) | |
| Er du selv PEP, eller har du været det inden for de seneste 12 måneder? | ☐ Nej ☐ Ja – hverv og land: |
| Er du nærtstående til en PEP? | ☐ Nej ☐ Ja – navn, relation og hverv: |
| Er du nær samarbejdspartner til en PEP? | ☐ Nej ☐ Ja – navn og forbindelse: |

Dato: ____________ Underskrift: ______________________________
{% endif %}
{% if felt.antal_personer == "2" or felt.antal_personer == "3" or felt.antal_personer == "4" %}
### Person 2

| | |
|---|---|
| Navn | |
| Fødselsdato | |
| Rolle hos kunden | |
| Er du selv PEP, eller har du været det inden for de seneste 12 måneder? | ☐ Nej ☐ Ja – hverv og land: |
| Er du nærtstående til en PEP? | ☐ Nej ☐ Ja – navn, relation og hverv: |
| Er du nær samarbejdspartner til en PEP? | ☐ Nej ☐ Ja – navn og forbindelse: |

Dato: ____________ Underskrift: ______________________________
{% endif %}
{% if felt.antal_personer == "3" or felt.antal_personer == "4" %}
### Person 3

| | |
|---|---|
| Navn | |
| Fødselsdato | |
| Rolle hos kunden | |
| Er du selv PEP, eller har du været det inden for de seneste 12 måneder? | ☐ Nej ☐ Ja – hverv og land: |
| Er du nærtstående til en PEP? | ☐ Nej ☐ Ja – navn, relation og hverv: |
| Er du nær samarbejdspartner til en PEP? | ☐ Nej ☐ Ja – navn og forbindelse: |

Dato: ____________ Underskrift: ______________________________
{% endif %}
{% if felt.antal_personer == "4" %}
### Person 4

| | |
|---|---|
| Navn | |
| Fødselsdato | |
| Rolle hos kunden | |
| Er du selv PEP, eller har du været det inden for de seneste 12 måneder? | ☐ Nej ☐ Ja – hverv og land: |
| Er du nærtstående til en PEP? | ☐ Nej ☐ Ja – navn, relation og hverv: |
| Er du nær samarbejdspartner til en PEP? | ☐ Nej ☐ Ja – navn og forbindelse: |

Dato: ____________ Underskrift: ______________________________
{% endif %}

## Hvis svaret er "ja"

Vi vil bede om oplysninger om midlernes og formuens oprindelse (fx lønsedler, årsopgørelser, dokumentation for arv eller salg), og kundeforholdet skal godkendes af vores ledelse (§ 18, stk. 2-3). Vi overvåger kundeforholdet tættere (§ 18, stk. 4). Efter ophør af hvervet vurderer vi i mindst 12 måneder, om der fortsat er en øget risiko (§ 18, stk. 6).

Oplysningerne behandles fortroligt og alene til brug for at overholde hvidvaskloven. De opbevares i 5 år efter kundeforholdets ophør (hvidvasklovens § 30, stk. 2).

* * *

*Internt ({{ firma.navn }}): Kontrolleret mod Finanstilsynets PEP-liste og offentlige kilder den ________ af ________. Resultat: ☐ Ingen PEP ☐ PEP/nærtstående/nær samarbejdspartner – skærpede procedurer iværksat, godkendt af ________.*
