---
{
  "title": "Accept og fortsættelse af kundeforhold og opgave",
  "description": "Internt memo til dokumentation af beslutning om accept af ny kunde eller fortsættelse af eksisterende kundeforhold og opgave efter ISQM 1, ISA 220 (revideret) og de etiske regler. Skal godkendes af den opgaveansvarlige partner.",
  "kind": "arbejdspapir",
  "references": ["ISQM 1 afsnit 30 og A62-A72", "ISA 220 (revideret) afsnit 22-24", "ISA 210", "Revisorloven §§ 16, 18 og 24", "FSR – danske revisorers Etiske regler for revisorer (del 3 og 4A)", "Hvidvaskloven §§ 10-18"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "type", "label": "Vurderingstype", "type": "select", "options": ["Ny kunde", "Fortsættelse (årlig)", "Ny opgave for eksisterende kunde", "Revurdering pga. ændrede forhold"], "default": "Fortsættelse (årlig)"},
    {"name": "opgaver", "label": "Opgave(r)", "type": "select", "options": ["Revision", "Udvidet gennemgang", "Review", "Opstilling", "Aftalte arbejdshandlinger", "Bogføring/løn/moms", "Skat", "Flere – se beskrivelse"], "default": "Opstilling"},
    {"name": "opgavebeskrivelse", "label": "Beskrivelse af opgaven og ydelser", "type": "textarea"},
    {"name": "partner", "label": "Opgaveansvarlig partner", "type": "text"},
    {"name": "kvalitetssikring", "label": "Opgavekvalitetsgennemgang (EQR) påkrævet", "type": "select", "options": ["Nej", "Ja – kriterier i virksomhedens kvalitetsstyringssystem opfyldt", "Ja – frivilligt pga. risiko"], "default": "Nej"},
    {"name": "honorar_forventet", "label": "Forventet årligt honorar (kr.)", "type": "number"},
    {"name": "risiko_samlet", "label": "Samlet opgaverisiko", "type": "select", "options": ["Lav", "Normal", "Forhøjet", "Høj"], "default": "Normal"},
    {"name": "konklusion", "label": "Konklusion", "type": "select", "options": ["Kunden/opgaven accepteres", "Kunden/opgaven accepteres med betingelser (se nedenfor)", "Kunden/opgaven afvises/kundeforholdet afsluttes"], "default": "Kunden/opgaven accepteres"},
    {"name": "betingelser", "label": "Betingelser og særlige tiltag", "type": "textarea"}
  ]
}
---
# Accept og fortsættelse af kundeforhold – {{ kunde.navn }}

| | |
|---|---|
| Kunde | {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }} |
| Selskabsform / regnskabsklasse | {{ kunde.selskabsform }} / {{ kunde.regnskabsklasse }} |
| Branche | {{ kunde.branchekode }} {{ kunde.branchetekst }} (hvidvaskrisiko for branchen: {{ branche.hvidvask_risiko }}) |
| Regnskabsår | {{ regnskab.aar }} ({{ regnskab.start }} – {{ regnskab.slut }}) |
| Nøgletal | Omsætning {{ regnskab.omsaetning }} · Resultat {{ regnskab.resultat }} · Balance {{ regnskab.balancesum }} · Egenkapital {{ regnskab.egenkapital }} |
| Vurderingstype | {{ felt.type }} |
| Opgave | {{ felt.opgaver }} |
| Kundeansvarlig | {{ kunde.ansvarlig }} |
| Opgaveansvarlig partner | {{ felt.partner }} |
| Udarbejdet af / dato | {{ medarbejder.navn }} / {{ dato.idag }} |

**Beskrivelse af opgaven:** {{ felt.opgavebeskrivelse }}

Formålet er at dokumentere, at {{ firma.navn }} kun accepterer eller fortsætter kundeforhold og opgaver, hvor vi (1) kan udføre opgaven kompetent og har tid og ressourcer, (2) kan overholde de etiske krav, herunder uafhængighed, og (3) har vurderet kundens integritet, jf. ISQM 1 og ISA 220. Vurderingen gentages hvert år og ved væsentlige ændringer.

## 1. Kundens integritet og ledelse

| # | Spørgsmål | Ja/Nej | Kommentar |
|---|---|---|---|
| 1.1 | Er identiteten og ejerstrukturen (reelle ejere) kendt og dokumenteret i KYC-skemaet? | | |
| 1.2 | Er der negativ omtale af kunden, ejere eller ledelse (søgning i medier, Statstidende, CVR-historik, konkurser, karantæne)? | | |
| 1.3 | Er ledelsen eller ejere tidligere straffet eller sanktioneret for økonomisk kriminalitet, eller er de opført på sanktionslister? | | |
| 1.4 | Er ejere/ledelse PEP, nærtstående eller nære samarbejdspartnere til en PEP? | | |
| 1.5 | Har kunden hyppigt skiftet revisor eller bogholder, eller er grunden til skiftet uklar? | | |
| 1.6 | Er der indikationer på, at ledelsen vil presse os til at acceptere uhensigtsmæssig regnskabspraksis, eller begrænse vores arbejde? | | |
| 1.7 | Er der restancer hos Skattestyrelsen, tvangsopløsningssager eller sen indsendelse af årsrapporter? | | |
| 1.8 | Er der ubetalte honorarer fra tidligere år? | | |

## 2. Hvidvask (sammenfatning af særskilt KYC og risikovurdering)

- [ ] Kundekendskabsprocedurer gennemført og dokumenteret (hvidvasklovens § 11)
- [ ] Risikovurdering af kunden udarbejdet og godkendt – samlet risiko: ________
- [ ] Formål med og tilsigtet beskaffenhed af kundeforholdet vurderet
- [ ] Skærpede procedurer anvendt, hvis risikoen er forhøjet/høj, eller kunden er PEP (§§ 17-18)
- [ ] Ingen uafklarede mistanker (§ 25) – ellers stop og kontakt hvidvaskansvarlig

{% if branche.hvidvask_risiko == "høj" %}> **Branchen har høj hvidvaskrisiko ({{ branche.navn }}).** Accept kræver godkendelse af partner og hvidvaskansvarlig, og der skal være dokumenteret skærpet kundekendskab.{% elif branche.hvidvask_risiko == "forhøjet" %}> **Branchen har forhøjet hvidvaskrisiko ({{ branche.navn }}).** Vurdér behovet for skærpede procedurer, og dokumentér begrundelsen.{% endif %}

## 3. Etik og uafhængighed

| # | Spørgsmål | Ja/Nej | Kommentar |
|---|---|---|---|
| 3.1 | Er uafhængighedsvurdering udarbejdet for erklæringsopgaven (revisorlovens § 24)? | | |
| 3.2 | Har firmaet, partnere eller medarbejdere på opgaven økonomiske interesser, lån, nære relationer eller ansættelsesforhold hos kunden? | | |
| 3.3 | Leverer vi ikke-revisionsydelser (bogføring, løn, skat, rådgivning), der skaber selvrevisions- eller egeninteressetrussel, og er der sikkerhedsforanstaltninger? | | |
| 3.4 | Udgør honoraret fra kunden (og nærtstående) en væsentlig del af firmaets eller partnerens samlede honorar? | | |
| 3.5 | Har den opgaveansvarlige været på opgaven i mange år (trussel om fortrolighed), og er der behov for rotation eller ekstra gennemgang? | | |
| 3.6 | Er der interessekonflikter med andre kunder (konkurrenter, modparter)? | | |

## 4. Kompetence og ressourcer

| # | Spørgsmål | Ja/Nej | Kommentar |
|---|---|---|---|
| 4.1 | Har teamet branchekendskab og kompetence til opgaven ({{ kunde.branchetekst }})? | | |
| 4.2 | Har vi tid og bemanding til at overholde fristen {{ regnskab.frist_aarsrapport }}? | | |
| 4.3 | Er der behov for specialister (skat, IT, vurdering af ejendomme, aktuar)? | | |
| 4.4 | Er det relevante regnskabsgrundlag acceptabelt (ISA 210.6)? | | |
| 4.5 | Har ledelsen anerkendt sit ansvar (opdragsbrev underskrevet)? | | |
| 4.6 | Krav om opgavekvalitetsgennemgang: {{ felt.kvalitetssikring }} | | |

## 5. Opgavespecifik risiko

| # | Risikofaktor | Ja/Nej | Kommentar |
|---|---|---|---|
| 5.1 | Usikkerhed om fortsat drift (underskud, negativ egenkapital, likviditetsmangel, kapitaltab efter selskabslovens § 119)? | | |
| 5.2 | Væsentlige regnskabsmæssige skøn eller komplekse transaktioner? | | |
| 5.3 | Mangelfuld bogføring eller intern kontrol, mange korrektioner sidste år? | | |
| 5.4 | Transaktioner med nærtstående parter, lån til kapitalejere/ledelse (forsvarlighed SL §§ 115/127, beskatning LL § 16 E; lån fra før 2025 i strid med de ophævede §§ 210-212)? | | |
| 5.5 | Modifikationer i sidste års erklæring eller ledelsens uenighed med os? | | |
| 5.6 | Tredjemand vil anvende erklæringen (bank, investor, køber), og øger det ansvarsrisikoen? | | |
{% if branche.kontantintensiv %}| 5.7 | Kontantintensiv branche: risiko for ufuldstændig omsætning og sort løn | | |
{% endif %}{% if branche.byggeri %}| 5.8 | Byggeri: underentreprenører, fakturafabrikker, udenlandsk arbejdskraft, igangværende arbejder | | |
{% endif %}{% if branche.lager %}| 5.9 | Væsentligt varelager: optælling, kostpris, ukurans | | |
{% endif %}{% if branche.investeringsejendomme %}| 5.10 | Investeringsejendomme målt til dagsværdi: skøn og afkastkrav | | |
{% endif %}{% if branche.holding %}| 5.11 | Holding: koncernforhold, måling af kapitalandele, grænser i ÅRL § 135, stk. 4 | | |
{% endif %}

## 6. Ny kunde – revisorskifte

{% if felt.type == "Ny kunde" %}- [ ] Henvendelse til fratrædende revisor er sendt og besvaret (revisorlovens § 18, stk. 2). Svarets indhold: ________
- [ ] Henvendelse til revisor, der afgav seneste erklæring, hvis en anden end den fratrædende
- [ ] Seneste årsrapport og erklæring gennemgået (modifikationer, fremhævelser)
- [ ] Åbningsbalancen kan revideres/gennemgås (ISA 510)
- [ ] Kunden har givet samtykke til, at tidligere revisor må udtale sig
{% else %}Ikke relevant – eksisterende kunde.{% endif %}

## 7. Honorar

Forventet årligt honorar: {{ felt.honorar_forventet }} kr. Er honoraret tilstrækkeligt til at udføre opgaven med den nødvendige kvalitet (ISQM 1 – honorarer må ikke kompromittere kvaliteten)? ☐ Ja ☐ Nej

## 8. Konklusion og godkendelse

Samlet opgaverisiko: **{{ felt.risiko_samlet }}**

Konklusion: **{{ felt.konklusion }}**

{% if felt.betingelser %}Betingelser og særlige tiltag: {{ felt.betingelser }}{% endif %}

Hvis kunden eller opgaven afvises, eller kundeforholdet afsluttes, skal det vurderes, om der er pligt til at underrette Hvidvasksekretariatet (hvidvasklovens § 26), og om der skal ske anmeldelse af fratræden til Erhvervsstyrelsen.

| Rolle | Navn | Dato | Underskrift |
|---|---|---|---|
| Udarbejdet af | {{ medarbejder.navn }} | {{ dato.idag }} | |
| Opgaveansvarlig partner | {{ felt.partner }} | | |
| Hvidvaskansvarlig (ved høj risiko/PEP) | | | |
