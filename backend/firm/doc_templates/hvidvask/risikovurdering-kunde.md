---
{
  "title": "Risikovurdering af kunden (hvidvask og terrorfinansiering)",
  "description": "Konkret risikovurdering af kundeforholdet efter hvidvasklovens § 11, stk. 2, med kunde-, produkt-, kanal- og geografiske risikofaktorer, branchespecifikke risici (byggeri, restauration, bilhandel, ejendom, transport, vikar, rengøring, spil m.fl.) og konklusion om procedureniveau.",
  "kind": "arbejdspapir",
  "references": ["Hvidvaskloven (LBK nr. 433 af 17/04/2026) §§ 7, 11, stk. 2, 17, 18 og 21 samt bilag 2 og 3", "Erhvervsstyrelsens vejledning om hvidvaskloven og om vurdering af formål og tilsigtet beskaffenhed (oktober 2026)", "National risikovurdering af hvidvask og terrorfinansiering (Hvidvasksekretariatet)", "Erhvervsstyrelsens sektorrisikovurdering for revisorer, bogholdere og skatterådgivere", "Virksomhedens egen risikovurdering efter § 7"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "ydelser", "label": "Ydelser til kunden", "type": "text"},
    {"name": "kontantandel", "label": "Skønnet kontantandel af omsætningen (%)", "type": "number"},
    {"name": "lande", "label": "Lande kunden handler med/har ejere i (uden for EU/EØS)", "type": "text"},
    {"name": "samlet", "label": "Samlet risiko (din konklusion)", "type": "select", "options": ["Lav", "Normal", "Forhøjet", "Høj"], "default": "Normal"},
    {"name": "begrundelse", "label": "Begrundelse for samlet risiko", "type": "textarea"},
    {"name": "tiltag", "label": "Tiltag (skærpede procedurer, overvågning)", "type": "textarea"}
  ]
}
---
# Risikovurdering af kunden – {{ kunde.navn }}

| | |
|---|---|
| Kunde | {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }} ({{ kunde.selskabsform }}) |
| Branche | {{ kunde.branchekode }} {{ kunde.branchetekst }} |
| Brancherisiko efter vores risikovurdering | **{{ branche.hvidvask_risiko }}**{% if branche.kontantintensiv %} – kontantintensiv{% endif %} |
| Ydelser | {{ felt.ydelser }} |
| Nøgletal | Omsætning {{ regnskab.omsaetning }} · Balance {{ regnskab.balancesum }} · Egenkapital {{ regnskab.egenkapital }} |
| Udarbejdet af / dato | {{ medarbejder.navn }} / {{ dato.idag }} |

Risikovurderingen skal bygge på konkrete oplysninger om kunden og skal sammenholdes med revisionsvirksomhedens egen risikovurdering (§ 7) og de risikofaktorer, der fremgår af hvidvasklovens bilag 2 (lav risiko) og bilag 3 (høj risiko). Vurderingen bestemmer omfanget af kundekendskabsprocedurerne og den løbende overvågning (§ 11, stk. 2).

Skala: **1 = lav · 2 = normal · 3 = forhøjet · 4 = høj**

## 1. Kunderisiko

| Faktor | Forhold hos kunden | Score 1-4 |
|---|---|---|
| Ejerstruktur: kompleks, mange led, udenlandske selskaber, trusts, nominee-ejere | | |
| Reelle ejere uklare, eller ejerskifte uden forklaring | | |
| PEP, nærtstående eller nær samarbejdspartner | | |
| Negativ omtale, straffedomme, konkurser, karantæne for ledelse/ejere | | |
| Ny virksomhed uden historik, eller hyppige skift af ledelse, adresse, revisor | | |
| Ledelse/kontaktperson uden branchekendskab (stråmand), eller tredjemand styrer kontakten | | |
| Kapitalforhold: store indskud, apport, lån fra ejere uden dokumenteret oprindelse | | |
| Ejeres forbrug/aktiver står ikke mål med indtjeningen | | |

## 2. Produkt- og ydelsesrisiko

| Faktor | Forhold | Score 1-4 |
|---|---|---|
| Ydelser, der kan misbruges: selskabsstiftelse, omstrukturering, kapitalforhøjelse, kapitalejerlån, betalinger på kundens vegne, klientkonto | | |
| Kunden ønsker selv at indberette moms/løn, eller kun at få regnskab "pyntet" | | |
| Ydelser atypiske for branchen eller for kundens størrelse | | |
| Hastende opgaver uden forklaring, fx ved salg af selskab | | |

## 3. Leverings- og kanalrisiko

| Faktor | Forhold | Score 1-4 |
|---|---|---|
| Kunden er ikke mødt fysisk og ikke identificeret via MitID | | |
| Kunden er henvist af ukendt mellemmand, eller geografisk langt væk uden tilknytning | | |
| Kommunikation via tredjemand | | |

## 4. Geografisk risiko

| Faktor | Forhold | Score 1-4 |
|---|---|---|
| Ejere, ledelse eller aktiviteter i højrisikotredjelande (EU-Kommissionens liste) – kræver skærpede procedurer (§ 17, stk. 2) | {{ felt.lande }} | |
| Handel med lande under sanktioner, eller lande med høj korruption/skatteunddragelse (EU's liste over ikke-samarbejdsvillige jurisdiktioner) | | |
| Betalinger til/fra udlandet, der ikke passer til forretningsmodellen | | |

## 5. Brancherisiko

Kontantandel: {{ felt.kontantandel }} %.

{% if branche.byggeri %}### Byggeri
- Fakturafabrikker: fakturaer fra underleverandører uden reel aktivitet, nystartede CVR-numre, skiftende ledelse, adresser hos "skuffeselskaber".
- Sort løn og social dumping: lav lønsum i forhold til omsætning, udenlandsk arbejdskraft uden RUT-registrering, kontante lønudbetalinger.
- Kædesvig med moms og omvendt betalingspligt.
- Kontrollér: omsætning pr. ansat, top-10 underleverandører (CVR-alder, ansatte, ledelse), kontanthævninger.
{% endif %}{% if branche.restauration or branche.hotel %}### Restauration og hotel
- Kontantomsætning der ikke registreres, eller omvendt – indsættelse af kontanter fra kriminalitet som "omsætning" (hvidvask via kasse).
- Sort løn til køkkenpersonale og udbringere, udenlandsk arbejdskraft.
- Bruttoavance og omsætning pr. kuvert sammenlignet med branchen.
- Hyppige ejerskifter, stråmænd og konkurser (restauration er klassificeret risikobranche efter årsregnskabslovens § 135, stk. 5).
{% endif %}{% if branche.bilhandel %}### Handel med motorkøretøjer
- Højværdivarer, der let kan bruges til at placere kontanter; kontantforbuddet ved betalinger på 20.000 kr. eller derover.
- Import/eksport af brugte biler (momskarruseller, falske eksportpapirer, registreringsafgift).
- Køb af biler for tredjemand, finansiering via ukendte lån.
- Kontrollér lagerbog, brugtmomsordning og betalingsmåder.
{% endif %}{% if branche.ejendom or branche.investeringsejendomme %}### Fast ejendom
- Køb af ejendomme finansieret med midler af ukendt oprindelse, udenlandske lån eller indskud fra ejere.
- Køb og salg til over- eller underpris, hurtige videresalg, transaktioner mellem nærtstående.
- Lejeindtægter i kontanter eller fra ukendte lejere; tomme lejemål med uforklarlig indtjening.
{% endif %}{% if branche.transport %}### Transport
- Vejgodstransport og flytning har været klassificeret som risikobranche (§ 135, stk. 5).
- Udenlandske chauffører, cabotage, sort løn og falske underleverandørfakturaer.
- Risiko for brug til smugling og transport af kontanter eller varer.
- Taxa: kontantomsætning og omsætning, der ikke registreres i taxameter.
{% endif %}{% if branche.vikar %}### Vikar- og bemandingsvirksomhed
- Fakturafabrikker, sort løn og misbrug af udenlandsk arbejdskraft.
- Hurtig vækst uden kapital, mange korte ansættelser, løn udbetalt til andres konti.
- Kontrollér: lønsum, A-skat og AM-bidrag sammenholdt med fakturering; kundeportefølje.
{% endif %}{% if branche.rengoering %}### Rengøring
- Klassificeret risikobranche (§ 135, stk. 5). Arbejdskraftintensiv, lav kapital, mange underleverandører.
- Sort løn, fakturafabrikker, udenlandsk arbejdskraft, kontant betaling fra private kunder.
{% endif %}{% if branche.spil %}### Spil og lotteri
- Spil er en af de mest anvendte metoder til at hvidvaske kontanter (gevinster som "dokumentation" for midler).
- Kontrollér tilladelse fra Spillemyndigheden, kontanthåndtering og udbetalinger.
{% endif %}{% if branche.personlig_service %}### Personlig service (frisør, skønhed, neglesaloner m.v.)
- Kontantomsætning, sort løn og "lejede stole". Skønhedspleje er klassificeret risikobranche (§ 135, stk. 5).
- Omsætning, der ikke står mål med antal behandlere og åbningstider (for høj eller for lav).
{% endif %}{% if branche.detail %}### Detailhandel og kiosker
- Kontantomsætning; risiko for at kriminelle midler blandes med omsætningen.
- Salg af tobak, gavekort, telefonkort og pengeoverførsler (agent for betalingsinstitut).
{% endif %}{% if branche.engros %}### Engroshandel og import/eksport
- Handelsbaseret hvidvask: over-/underfakturering, fiktive leverancer, betalinger fra tredjeparter.
- Handel med højrisikolande og sanktionerede varer (dual use).
{% endif %}{% if branche.holding or branche.finans %}### Holding og finansielle aktiviteter
- Komplekse strukturer, der skjuler reelle ejere; udenlandske led.
- Lån mellem koncernselskaber og til ejere, investeringer i kryptoaktiver eller unoterede selskaber.
{% endif %}{% if branche.it %}### IT og internetportaler
- Drift af portaler og webhosting er klassificeret som risikobranche (§ 135, stk. 5). Svært at verificere omsætning og leverancer; udenlandske betalinger og kryptoaktiver.
{% endif %}{% if branche.forening %}### Foreninger og NPO
- Risiko for terrorfinansiering ved indsamlinger og overførsler til konfliktområder.
- Kontantindsamlinger, mangelfuld dokumentation for anvendelse af midler.
{% endif %}{% if branche.landbrug %}### Landbrug
- Udenlandsk sæsonarbejdskraft og sort løn; handel med maskiner og dyr til/fra udlandet.
{% endif %}{% if branche.hvidvask_risiko == "normal" and not branche.kontantintensiv %}Branchen er ikke vurderet til forhøjet risiko i vores risikovurdering. Vurdér alligevel konkrete forhold hos kunden.
{% endif %}

| Brancherisiko | Score 1-4 |
|---|---|
| Samlet brancherisiko for kunden ({{ branche.hvidvask_risiko }}) | |

## 6. Formildende faktorer (bilag 2)

- [ ] Børsnoteret selskab med oplysningskrav om reelle ejere
- [ ] Offentlig myndighed eller offentligt ejet virksomhed
- [ ] Lang og veldokumenteret kunderelation uden usædvanlige forhold
- [ ] Enkel struktur, dansk ejerskab, MitID-identifikation, betalinger fra dansk pengeinstitut
- [ ] Lav kontantandel og gennemsigtig forretningsmodel

## 7. Samlet vurdering

| Område | Score |
|---|---|
| Kunderisiko | |
| Produkt/ydelse | |
| Kanal | |
| Geografi | |
| Branche | |
| **Samlet** | **{{ felt.samlet }}** |

Den samlede risiko er ikke et gennemsnit. Én høj faktor (fx PEP, højrisikotredjeland, uklare reelle ejere) kan i sig selv begrunde forhøjet eller høj risiko.

**Begrundelse:** {{ felt.begrundelse }}

| Samlet risiko | Procedure | Opdatering af kundekendskab |
|---|---|---|
| Lav | Lempede procedurer efter konkret vurdering (§ 21) – identitet skal stadig kontrolleres | Hvert 3. år og ved ændringer |
| Normal | Almindelige procedurer (§ 11) | Hvert 2. år og ved ændringer |
| Forhøjet | Skærpede procedurer (§ 17): yderligere dokumentation for midlernes oprindelse, partnergodkendelse, tættere overvågning | Årligt |
| Høj | Skærpede procedurer + godkendelse af hvidvaskansvarlig; overvej at afslå kunden | Mindst årligt og ved hver opgave |

**Tiltag:** {{ felt.tiltag }}

| Rolle | Navn | Dato | Underskrift |
|---|---|---|---|
| Udarbejdet af | {{ medarbejder.navn }} | {{ dato.idag }} | |
| Godkendt af partner | | | |
| Godkendt af hvidvaskansvarlig (forhøjet/høj) | | | |
