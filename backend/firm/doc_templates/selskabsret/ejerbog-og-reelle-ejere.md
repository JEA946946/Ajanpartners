---
{
  "title": "Ejerbog og register over reelle ejere",
  "description": "Fortegnelse over kapitalejere (ejerbog, SL § 50-52), registrering i det offentlige ejerregister (§§ 55-58) og dokumentation for identifikation af reelle ejere (§ 58 a) inkl. årlig undersøgelse.",
  "kind": "arbejdspapir",
  "references": ["Selskabsloven §§ 50-58", "Selskabsloven § 58 a og § 58 b", "Selskabsloven § 225, stk. 1, nr. 3-5", "Hvidvaskloven § 2, nr. 9", "Bekendtgørelse om registrering af reelle ejere"],
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
Det centrale ledelsesorgan skal føre en fortegnelse over samtlige {{ kunde.kapitalejere }} (selskabslovens § 50). For hver kapitalejer noteres navn og adresse (for virksomheder CVR-nr.), kapitalandelenes størrelse og stemmeret, klasse, erhvervelses- og afståelsestidspunkt, samt eventuel pantsætning eller rettighedsbegrænsning. Ejerbogen skal være tilgængelig for {% if kunde.selskabsform_kode == "as" %}Erhvervsstyrelsen og myndigheder; aktionærerne har adgang efter vedtægterne{% else %}enhver anpartshaver, Erhvervsstyrelsen og myndigheder{% endif %}.

| Kapitalejer | Adresse | CPR/CVR | Nominel kapital | Andel | Stemmer | Erhvervet | Bemærkning |
|---|---|---|---|---|---|---|---|
{{ felt.ejere }}

*Kapitalejere kan ikke udøve rettigheder (stemmeret, udbytte) for kapitalandele, før de er noteret i ejerbogen eller har anmeldt og dokumenteret erhvervelsen.*

## 2. Offentligt ejerregister (selskabslovens §§ 55-58)
- Enhver, der besidder mindst 5 % af stemmerne eller kapitalen, skal give selskabet meddelelse, og ændringer skal meddeles, når grænserne 5, 10, 15, 20, 25, 50, 90 eller 100 % og 1/3 eller 2/3 nås eller ikke længere nås (§ 55).
- Meddelelse gives senest 2 uger efter, at besiddelsen er opnået eller ændret.
- Selskabet registrerer oplysningerne i Erhvervsstyrelsens it-system hurtigst muligt (§ 58, stk. 2). Har ingen 5 % eller mere, registreres dette.

- [ ] Registreringen i CVR svarer til ejerbogen pr. {{ felt.undersoegelse_dato }}.

## 3. Reelle ejere (selskabslovens § 58 a)
**Definition** (hvidvaskloven § 2, nr. 9): den eller de fysiske personer, der i sidste ende ejer eller kontrollerer selskabet – direkte eller indirekte mere end 25 % af kapitalen eller stemmerne, eller som på anden måde udøver kontrol (fx aftaler om udpegning af ledelse, vetoret, ejeraftaler, fuldmagter, nominee-arrangementer). Indirekte ejerskab opgøres gennem kæden af selskaber; ved kontrol (> 50 %) i et mellemliggende led medregnes hele mellemled­sejerandelen.

**Oplysninger, der registreres for hver reel ejer:** navn, adresse, bopælsland, statsborgerskab, fødselsdato/CPR-nr. (CPR offentliggøres ikke), samt art og omfang af ejerskab/kontrol (procentinterval for ejer- og stemmeandel, særlige ejerforhold) og dato for, hvornår personen blev reel ejer.

| Reel ejer | Adresse/bopælsland | Statsborgerskab | Fødselsdato/CPR | Ejerandel | Stemmer | Art af kontrol | Dokumentation |
|---|---|---|---|---|---|---|---|
{{ felt.reelle_ejere }}

{% if felt.ingen_reel_ejer %}Selskabet har udtømt alle muligheder for at identificere reelle ejere, og ingen person ejer eller kontrollerer mere end 25 %. Den registrerede direktion registreres derfor som reelle ejere (§ 58 a, stk. 3, 3. pkt.). Forsøgene på identifikation er dokumenteret nedenfor.{% endif %}

## 4. Årlig undersøgelse (§ 58 a, stk. 4)
Selskabet skal mindst én gang årligt undersøge, om der er ændringer i de registrerede reelle ejere. Resultatet fremlægges på det møde, hvor {{ kunde.ledelsesorgan }} godkender årsrapporten.

Undersøgelse foretaget: {{ felt.undersoegelse_dato }}
Resultat: {{ felt.aendringer }}

- [ ] Kapitalejerne er anmodet om oplysninger om ejer- og kontrolforhold (§ 58 a, stk. 2), herunder ejeraftaler.
- [ ] Ændringer registreret i CVR hurtigst muligt efter, at selskabet blev bekendt med dem.
- [ ] Dokumentation (anmodninger, svar, organisationsdiagram, ejeraftaler) opbevares i 5 år efter det reelle ejerskabs ophør (§ 58 a, stk. 5).
- [ ] Uoverensstemmelser indberettet af banker/revisorer efter hvidvaskloven er besvaret.

Manglende eller mangelfuld registrering kan medføre tvangsopløsning (selskabslovens § 225, stk. 1, nr. 3-5) og bødestraf.

Udarbejdet af {{ medarbejder.navn }}, {{ firma.navn }}, {{ dato.idag }}.
