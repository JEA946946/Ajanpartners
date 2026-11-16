---
{
  "title": "Uafhængighedsvurdering – erklæringsopgave",
  "description": "Internt arbejdspapir til vurdering og dokumentation af revisors uafhængighed efter revisorlovens § 24 og de etiske regler: trusler, sikkerhedsforanstaltninger, ikke-revisionsydelser, honorarafhængighed og teamets bekræftelser.",
  "kind": "arbejdspapir",
  "references": ["Revisorloven §§ 16, stk. 4, 24 og 25 (LBK nr. 206 af 20/02/2025)", "Bekendtgørelse nr. 520 af 24/05/2024 om godkendte revisorers og revisionsvirksomheders uafhængighed", "EU-forordning 537/2014 art. 4", "FSR – danske revisorers Etiske regler for revisorer (IESBA), del 4A og afsnit 600", "ISQM 1", "ISA 220 (revideret) afsnit 16-21"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "opgave", "label": "Erklæringsopgave", "type": "select", "options": ["Revision", "Udvidet gennemgang", "Review", "Andre erklæringer med sikkerhed", "Opstilling (uafhængighed ikke krav)", "Aftalte arbejdshandlinger"], "default": "Revision"},
    {"name": "partner", "label": "Opgaveansvarlig partner/underskriver", "type": "text"},
    {"name": "team", "label": "Medarbejdere på opgaven", "type": "textarea"},
    {"name": "aar_paa_opgaven", "label": "Antal år underskriveren har været på opgaven", "type": "number"},
    {"name": "honorar_erklaering", "label": "Honorar for erklæringsopgaven (kr.)", "type": "number"},
    {"name": "honorar_andet", "label": "Honorar for andre ydelser (kr.)", "type": "number"},
    {"name": "honorarandel", "label": "Kundens andel af firmaets samlede honorar (%)", "type": "number"},
    {"name": "pie", "label": "Kunden er en virksomhed af interesse for offentligheden (PIE)", "type": "checkbox", "default": false},
    {"name": "honorargraense", "label": "Grænse for honorarafhængighed i firmaets politik (udfyldes af revisor)", "type": "text"}
  ]
}
---
# Uafhængighedsvurdering – {{ kunde.navn }}

| | |
|---|---|
| Kunde | {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }} ({{ kunde.selskabsform }}, klasse {{ kunde.regnskabsklasse }}) |
| Opgave / regnskabsår | {{ felt.opgave }} / {{ regnskab.aar }} |
| Opgaveansvarlig | {{ felt.partner }} – {{ felt.aar_paa_opgaven }} år på opgaven |
| Team | {{ felt.team }} |
| Udarbejdet | {{ medarbejder.navn }}, {{ dato.idag }} |

## 1. Retsgrundlag

Revisorlovens § 24, stk. 1, kræver, at revisor, revisionsvirksomheden og andre personer, der er knyttet til opgaven eller kontrollerer den, ved opgaver efter § 1, stk. 2 (revisionspåtegninger og andre erklæringer med sikkerhed), er uafhængige af virksomheden og ikke involveret i dens beslutningstagning – både i opgaveperioden og i den periode, erklæringen dækker. Revisor er ikke uafhængig, hvis der foreligger en økonomisk interesse eller et forretnings-, ansættelsesmæssigt eller andet forhold, som for en velinformeret tredjemand kan vække tvivl om uafhængigheden (§ 24, stk. 2). Ved trusler skal der træffes sikkerhedsforanstaltninger; er uafhængigheden bragt i fare, skal revisor afstå fra opgaven (§ 24, stk. 3). Væsentlige trusler og sikkerhedsforanstaltninger dokumenteres i arbejdspapirerne (§ 24, stk. 5).

De etiske regler (IESBA Code som udgivet af FSR – danske revisorer) anvender den begrebsmæssige ramme: identificere trusler, vurdere dem og håndtere dem ved at fjerne omstændighederne, anvende sikkerhedsforanstaltninger eller afslå/afslutte opgaven.

{% if felt.pie %}> **PIE:** Kunden er en virksomhed af interesse for offentligheden. EU-forordning 537/2014 (forbudte ikke-revisionsydelser, art. 5; honorarloft for ikke-revisionsydelser på 70 % af gennemsnittet af de seneste 3 års revisionshonorarer, art. 4, stk. 2; rotation, art. 17), revisorlovens § 24 a om tilladte skatte- og vurderingsydelser og de skærpede etiske regler for PIE gælder. Inddrag kvalitetsafdelingen.{% endif %}
{% if felt.opgave == "Opstilling (uafhængighed ikke krav)" %}> Ved opstilling efter ISRS 4410 er der ikke krav om uafhængighed, men er revisor ikke uafhængig, skal det oplyses i erklæringen (revisorlovens § 16, stk. 4), og de øvrige etiske principper (integritet, objektivitet, kompetence, fortrolighed) skal overholdes. Udfyld alligevel punkt 2-3, hvis opstillingen skal opfylde kravet om uafhængig revisor i årsregnskabslovens § 135, stk. 5.{% endif %}

## 2. Trusler mod uafhængigheden

| Trussel | Forhold at vurdere | Til stede? | Vurdering / sikkerhedsforanstaltning |
|---|---|---|---|
| **Egeninteresse** | Økonomiske interesser i kunden (firma, partnere, team, nærtstående); lån eller garantier til/fra kunden; honorarafhængighed; forfaldne honorarer; betingede honorarer; frygt for at miste kunden | | |
| **Selvrevision** | Vi har udført bogføring, løn, opstilling, skatteberegninger, værdiansættelser eller IT-systemer, som indgår i det, vi skal afgive erklæring om | | |
| **Partiskhed** | Vi fremmer kundens interesser, fx ved at optræde som rådgiver over for tredjemand, i tvister eller ved salg af kundens aktier | | |
| **Fortrolighed/familiaritet** | Langvarig tilknytning; nære personlige eller familiære relationer til ledelsen; tidligere ansat hos kunden; ledelsesmedlem tidligere ansat hos os; gaver og gæstfrihed | | |
| **Intimidering** | Pres fra ledelsen om regnskabspraksis eller honorar; trussel om udskiftning eller sagsanlæg | | |

## 3. Ikke-revisionsydelser

| Ydelse | Leveres? | Trussel | Sikkerhedsforanstaltning |
|---|---|---|---|
| Løbende bogføring og afstemninger | | Selvrevision | Ledelsen godkender posteringer og bærer ansvaret; bogføring og erklæringsarbejde udføres af forskellige personer; partner gennemgår |
| Lønadministration | | Selvrevision | Kunden godkender lønnen før udbetaling; vi har ikke adgang til at gennemføre betalinger |
| Opstilling af årsregnskab | | Selvrevision | Ledelsen træffer alle skøn og godkender regnskabet; opstilling adskilt fra revisionsarbejdet |
| Skatteberegning og selvangivelse | | Selvrevision | Beregninger ikke væsentlige for regnskabet eller ikke baseret på væsentlige skøn; ledelsen godkender |
| Skatterådgivning/skatteplanlægning | | Selvrevision, partiskhed | Vurderes efter de etiske regler (afsnit 604) og uafhængighedsbekendtgørelsen |
| Værdiansættelser | | Selvrevision | Vurderes efter de etiske regler (afsnit 603) og uafhængighedsbekendtgørelsen |
| Juridisk/selskabsretlig bistand (GF-referat, ejerbog) | | Partiskhed | Rent administrativ bistand; beslutninger træffes af kunden |
| Rekruttering, IT-systemer, intern revision | | Selvrevision, egeninteresse | Vurderes konkret |
| Ledelsesopgaver (beslutninger, godkendelse af transaktioner, bankfuldmagter, opbevaring af kundens aktiver) | | | **Ikke tilladt** – revisor må ikke være involveret i virksomhedens beslutningstagning (revisorlovens § 24, stk. 1) |

Honorar for erklæringsopgaven: {{ felt.honorar_erklaering }} kr. · Andre ydelser: {{ felt.honorar_andet }} kr.

## 4. Honorarafhængighed og varighed

- Kundens andel af firmaets samlede honorar: {{ felt.honorarandel }} %. Vurdér truslen om egeninteresse og intimidering efter de etiske regler om honorarafhængighed (afsnit 410), herunder de grænser og krav om sikkerhedsforanstaltninger og oplysning, der gælder for henholdsvis PIE og andre virksomheder. Grænse anvendt i firmaets politik: {{ felt.honorargraense }}.
- Underskriveren har været på opgaven i {{ felt.aar_paa_opgaven }} år. Vurdér trusler om fortrolighed ved langvarig tilknytning, og om der skal ske rotation eller ekstra gennemgang (rotation af underskrivende revisor efter senest 7 år er lovkrav for PIE og for virksomheder omfattet af revisorlovens § 25, stk. 2).

## 5. Bekræftelser fra teamet

Hver person på opgaven bekræfter, at vedkommende og dennes nærtstående ikke har økonomiske interesser i, lån fra/til, ansættelse hos eller nære relationer til {{ kunde.navn }} eller dets ledelse, og ikke har modtaget gaver ud over sædvanlig størrelse.

| Navn | Rolle | Forhold at oplyse | Dato | Underskrift |
|---|---|---|---|---|
| {{ felt.partner }} | Opgaveansvarlig | | | |
| | | | | |
| | | | | |

## 6. Konklusion

- [ ] Der er ikke identificeret trusler mod uafhængigheden.
- [ ] Der er identificeret trusler, som er reduceret til et acceptabelt niveau ved de beskrevne sikkerhedsforanstaltninger.
- [ ] Truslerne kan ikke reduceres til et acceptabelt niveau – opgaven skal afslås/afsluttes, eller ydelser skal ophøre.

Vurderingen gentages ved hver ny opgave, mindst årligt, og når der opstår nye forhold.

| Rolle | Navn | Dato | Underskrift |
|---|---|---|---|
| Udarbejdet af | {{ medarbejder.navn }} | {{ dato.idag }} | |
| Godkendt af opgaveansvarlig | {{ felt.partner }} | | |
