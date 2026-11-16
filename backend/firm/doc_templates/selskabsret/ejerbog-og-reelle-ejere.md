---
{
  "title": "Ejerbog og register over reelle ejere",
  "description": "Fortegnelse over kapitalejere (ejerbog, SL § 50-52), registrering i det offentlige ejerregister (§§ 55-58) og dokumentation for identifikation af reelle ejere (§ 58 a) inkl. årlig undersøgelse.",
  "kind": "arbejdspapir",
  "references": ["Selskabsloven §§ 49-58", "Selskabsloven § 58 a og § 58 b", "Selskabsloven § 225, stk. 1, nr. 3-5", "Hvidvaskloven § 2, nr. 9", "Bekendtgørelse om registrering af reelle ejere"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "ejerbogsfoerer", "label": "Ejerbogen føres af", "type": "select", "options": ["Selskabet selv", "Ejerbogsfører valgt efter vedtægterne", "Erhvervsstyrelsens it-system (SL § 50, stk. 2)"], "default": "Selskabet selv"},
    {"name": "kapital", "label": "Selskabskapital (nominelt kr.)", "type": "number"},
    {"name": "ejere", "label": "Kapitalejere: navn | adresse | CPR/CVR | nominel kapital | stemmer | erhvervet dato | evt. pant/klasse", "type": "textarea"},
    {"name": "reelle_ejere", "label": "Reelle ejere: navn | adresse | bopælsland | statsborgerskab | fødselsdato/CPR | ejerandel/stemmer | art af kontrol | kilde", "type": "textarea"},
    {"name": "ingen_reel_ejer", "label": "Ingen fysisk person ejer/kontrollerer > 25 % – direktionen registreres", "type": "checkbox"},
    {"name": "undersoegelse_dato", "label": "Dato for årlig undersøgelse", "type": "date", "default": "{{ dato.idag }}"},
    {"name": "aendringer", "label": "Konstaterede ændringer", "type": "textarea", "default": "Ingen ændringer."}
  ]
}
---
# Ejerbog og register over reelle ejere

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }} · Selskabskapital nominelt {{ felt.kapital }} kr.
Ejerbogen føres af: {{ felt.ejerbogsfoerer }}

## 1. Ejerbog (fortegnelse over samtlige kapitalejere)
Det centrale ledelsesorgan skal føre en fortegnelse over samtlige {{ kunde.kapitalejere }} (selskabslovens § 50). For hver kapitalejer noteres navn og adresse (for virksomheder CVR-nr.), kapitalandelenes størrelse og stemmeret, klasse, erhvervelses- og afståelsestidspunkt, samt eventuel pantsætning eller rettighedsbegrænsning. Ejerbogen skal være tilgængelig for offentlige myndigheder og føres inden for EU/EØS (§ 51, stk. 1){% if kunde.selskabsform_kode != "as" %}; i anpartsselskaber skal den tillige være tilgængelig for enhver anpartshaver (§ 51, stk. 6){% endif %}.

| Kapitalejer | Adresse | CPR/CVR | Nominel kapital | Andel | Stemmer | Erhvervet | Bemærkning |
|---|---|---|---|---|---|---|---|
{{ felt.ejere }}

*Erhververen af en navnekapitalandel kan ikke udøve kapitalejerrettigheder (fx stemmeret), før erhververen er noteret i ejerbogen eller har anmeldt og dokumenteret erhvervelsen. Det gælder dog ikke retten til udbytte og andre udbetalinger og retten til nye andele ved kapitalforhøjelse (§ 49, stk. 1).*

## 2. Offentligt ejerregister (selskabslovens §§ 55-58)
- Enhver, der besidder mindst 5 % af stemmerne eller kapitalen, skal give selskabet meddelelse, og ændringer skal meddeles, når grænserne 5, 10, 15, 20, 25, 50, 90 eller 100 % og 1/3 eller 2/3 nås eller ikke længere nås (§ 55).
- Meddelelse gives senest 2 uger efter, at en af grænserne nås eller ikke længere er nået (§ 56, stk. 1).
- Selskabet registrerer ændringer i Erhvervsstyrelsens it-system hurtigst muligt (§ 58, stk. 2). Har ingen kapitalejer betydelige kapitalandele, registreres dette (§ 58, stk. 1).

- [ ] Registreringen i CVR svarer til ejerbogen pr. {{ felt.undersoegelse_dato }}.

## 3. Reelle ejere (selskabslovens § 58 a)
**Definition** (hvidvaskloven § 2, nr. 9): den eller de fysiske personer, der i sidste ende ejer eller kontrollerer selskabet – direkte eller indirekte mere end 25 % af kapitalen eller stemmerne, eller som på anden måde udøver kontrol (fx aftaler om udpegning af ledelse, vetoret, ejeraftaler, fuldmagter, nominee-arrangementer). Indirekte ejerskab opgøres gennem kæden af selskaber.

**Oplysninger, der registreres for hver reel ejer:** oplysningerne om de reelle ejere og deres rettigheder (§ 58 a, stk. 3) – de konkrete datafelter følger af bekendtgørelsen om registrering af reelle ejere og Erhvervsstyrelsens it-system (kontrollér aktuelle krav).

| Reel ejer | Adresse/bopælsland | Statsborgerskab | Fødselsdato/CPR | Ejerandel | Stemmer | Art af kontrol | Dokumentation |
|---|---|---|---|---|---|---|---|
{{ felt.reelle_ejere }}

{% if felt.ingen_reel_ejer %}Selskabet har udtømt alle muligheder for at identificere reelle ejere, og ingen person ejer eller kontrollerer mere end 25 %. De registrerede medlemmer af direktionen registreres derfor som reelle ejere (§ 58 a, stk. 3, 3. pkt.). Forsøgene på identifikation er dokumenteret nedenfor.{% endif %}

## 4. Årlig undersøgelse (§ 58 a, stk. 4)
Selskabet skal mindst én gang årligt undersøge, om der er ændringer i de registrerede reelle ejere. Resultatet fremlægges på det møde, hvor {{ kunde.ledelsesorgan }} godkender årsrapporten.

Undersøgelse foretaget: {{ felt.undersoegelse_dato }}
Resultat: {{ felt.aendringer }}

- [ ] Kapitalejerne er anmodet om oplysninger om ejer- og kontrolforhold (§ 58 a, stk. 2), herunder ejeraftaler.
- [ ] Ændringer registreret i CVR hurtigst muligt efter, at selskabet blev bekendt med dem.
- [ ] Dokumentation (anmodninger, svar, organisationsdiagram, ejeraftaler) opbevares i 5 år efter det reelle ejerskabs ophør; dokumentation for identifikationsforsøg i 5 år efter forsøget (§ 58 a, stk. 5).
- [ ] Uoverensstemmelser indberettet af banker/revisorer efter hvidvaskloven er besvaret.

Manglende eller mangelfuld registrering eller dokumentation kan medføre tvangsopløsning (selskabslovens § 225, stk. 1, nr. 3-5).

Udarbejdet af {{ medarbejder.navn }}, {{ firma.navn }}, {{ dato.idag }}.
