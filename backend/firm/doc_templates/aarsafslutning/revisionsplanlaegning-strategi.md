---
{
  "title": "Revisionsplanlægning og revisionsstrategi (memo)",
  "description": "Internt planlægningsnotat efter ISA 300: opgavens omfang, tidsplan, team, væsentlighed, branchespecifikke risici og planlagte handlinger.",
  "kind": "arbejdspapir",
  "references": ["ISA 300", "ISA 315 (ajourført 2019)", "ISA 320", "ISA 240", "ISA 220 (ajourført)", "ISQM 1", "Revisorloven § 16"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "opgavetype", "label": "Opgavetype", "type": "select", "options": ["Revision (ISA)", "Udvidet gennemgang", "Review (ISRE 2400)"], "default": "Revision (ISA)"},
    {"name": "foerste_aar", "label": "Første års revision (ny kunde)", "type": "checkbox"},
    {"name": "opgaveansvarlig", "label": "Opgaveansvarlig revisor", "type": "text", "default": "{{ kunde.ansvarlig }}"},
    {"name": "team", "label": "Øvrige teammedlemmer", "type": "text"},
    {"name": "budget_timer", "label": "Budget (timer)", "type": "number"},
    {"name": "dato_planlaegning", "label": "Planlægningsmøde med kunden", "type": "date"},
    {"name": "dato_feltarbejde", "label": "Feltarbejde (periode)", "type": "text"},
    {"name": "dato_afslutning", "label": "Forventet underskrift af årsrapport", "type": "date"},
    {"name": "vaesentlighed", "label": "Væsentlighed (kr.)", "type": "number"},
    {"name": "arbejdsvaesentlighed", "label": "Arbejdsvæsentlighed (kr.)", "type": "number"},
    {"name": "sidste_aars_forhold", "label": "Forhold fra sidste år (protokol, fejl, forbehold)", "type": "textarea"},
    {"name": "aendringer_i_aaret", "label": "Ændringer i virksomheden i året", "type": "textarea"}
  ]
}
---
# Revisionsstrategi og planlægning – {{ kunde.navn }}

| | |
|---|---|
| CVR | {{ kunde.cvr }} |
| Regnskabsår | {{ regnskab.aar }} ({{ regnskab.start }} – {{ regnskab.slut }}) |
| Regnskabsklasse | {{ kunde.regnskabsklasse }} |
| Branche | {{ kunde.branchekode }} {{ kunde.branchetekst }} |
| Opgave | {{ felt.opgavetype }} |
| Opgaveansvarlig | {{ felt.opgaveansvarlig }} |
| Team | {{ felt.team }} |
| Budget | {{ felt.budget_timer }} timer |
| Frist for indsendelse | {{ regnskab.frist_aarsrapport }} |
| Udarbejdet af / dato | {{ medarbejder.navn }}, {{ dato.idag }} |

## 1. Forudsætninger for opgaven
- [ ] Accept/fortsættelse af kundeforholdet er vurderet og dokumenteret (ISQM 1, ISA 220)
- [ ] Uafhængighed er vurderet for alle teammedlemmer (revisorloven § 24, uafhængighedsbekendtgørelsen); ingen ikke-revisionsydelser, der truer uafhængigheden
- [ ] Opdragsbrev er underskrevet og dækker {{ regnskab.aar }} (ISA 210)
- [ ] Kundekendskab efter hvidvaskloven er ajourført (risiko: {{ branche.hvidvask_risiko }})
{% if felt.foerste_aar %}- [ ] Første års revision: kontakt til forrige revisor, gennemgang af dennes arbejdspapirer og vurdering af primobalancer (ISA 510)
{% endif %}

## 2. Forståelse af virksomheden og dens omgivelser
**Aktivitet og forretningsmodel:** {{ kunde.branchetekst }}

**Ændringer i året:** {{ felt.aendringer_i_aaret }}

**Forhold fra sidste år:** {{ felt.sidste_aars_forhold }}

Nøgletal fra bogføringen:

| Post | {{ regnskab.aar }} |
|---|---|
| Omsætning | {{ regnskab.omsaetning }} |
| Resultat | {{ regnskab.resultat }} |
| Balancesum | {{ regnskab.balancesum }} |
| Egenkapital | {{ regnskab.egenkapital }} |

Regnskabsmæssige rammer: årsregnskabsloven, klasse {{ kunde.regnskabsklasse }}. Bogføringen føres i et digitalt bogføringssystem (bogføringsloven § 16), og kontrolmiljøet er præget af få personer og begrænset funktionsadskillelse – det tages i betragtning ved valg af substansbaseret tilgang.

## 3. Væsentlighed (ISA 320)
Fastlagt i særskilt arbejdspapir. Væsentlighed: {{ felt.vaesentlighed }} kr. Arbejdsvæsentlighed: {{ felt.arbejdsvaesentlighed }} kr.

## 4. Branchespecifikke risici og fokusområder
Generelle betydelige risici, der altid adresseres (ISA 240):
- **Ledelsens tilsidesættelse af kontroller** – journalposter, regnskabsmæssige skøn og usædvanlige transaktioner testes.
- **Indtægtsindregning** – formodet besvigelsesrisiko; periodeafgrænsning og fuldstændighed.

{% if branche.byggeri %}- **Igangværende arbejder/entreprisekontrakter:** færdiggørelsesgrad, estimerede restomkostninger, tabsgivende kontrakter, ekstraarbejder og tvister. Skøn med høj usikkerhed (ISA 540).
- **Omvendt betalingspligt og underentreprenører:** moms og RUT-registrering, sort arbejde-risiko.
{% elif branche.igangvaerende_arbejder %}- **Igangværende arbejder for fremmed regning:** ikke-fakturerede timer, værdiansættelse til salgsværdi, tabsgivende opgaver og forudbetalinger.
{% endif %}{% if branche.lager %}- **Varelager:** eksistens (deltagelse i optælling, ISA 501), kostpris, ukurans og nedskrivning til nettorealisationsværdi, periodeafgrænsning af vareforbrug.
{% endif %}{% if branche.kontantintensiv %}- **Kontant omsætning:** fuldstændighed af omsætningen; afstemning af Z-rapporter, kasse og bank; bruttoavancekontrol; hvidvaskrisiko.
{% endif %}{% if branche.restauration or branche.hotel %}- **Restauration/hotel:** drikkepenge, personaleforplejning, vareforbrug vs. salg (bruttoavance), sæsonudsving og løn til ikke-registrerede medarbejdere.
{% endif %}{% if branche.ejendom %}- **Ejendomme:** værdiansættelse (dagsværdi efter ÅRL § 38 eller kostpris), forudsætninger for afkastkrav, udskudt skat, lejeindtægter og deposita, skillelinjen mellem vedligeholdelse og forbedring.
{% endif %}{% if branche.holding %}- **Kapitalandele og koncernforhold:** værdiansættelse af kapitalandele (indre værdi/kostpris, nedskrivningstest), mellemregninger, nærtstående parter, udbytte og sambeskatning; kapitalejerlån.
{% endif %}{% if branche.transport %}- **Transport:** værdiansættelse og afskrivning af køretøjer, leasing, rejse- og udetillæg til chauffører, cabotage og udenlandsk moms.
{% endif %}{% if branche.landbrug %}- **Landbrug:** biologiske aktiver (dagsværdi/kostpris), EU-støtte og risiko for tilbagebetaling, finansiering (høj gearing, renterisiko) og fortsat drift.
{% endif %}{% if branche.bilhandel %}- **Bilhandel:** varelager af biler (værdiansættelse, demobiler), brugtmoms, registreringsafgift og hvidvaskrisiko ved kontanthandel.
{% endif %}{% if branche.vikar or branche.rengoering %}- **Løn og arbejdskraft:** udenlandsk arbejdskraft, arbejdsudleje, sociale ordninger, risiko for sort løn og social dumping.
{% endif %}{% if branche.it or branche.medier %}- **Abonnements- og licensindtægter:** periodisering af forudfakturerede indtægter, aktiverede udviklingsomkostninger og reserve for udviklingsomkostninger under egenkapitalen.
{% endif %}{% if branche.momsfritaget %}- **Moms:** delvis fradragsret, pro rata-beregning og lønsumsafgift.
{% endif %}{% if branche.forening %}- **Forening/nonprofit:** tilskud og vilkår, fuldstændighed af kontingenter og indsamlinger, formålsbestemt anvendelse.
{% endif %}- **Fortsat drift (ISA 570):** vurderes ud fra egenkapital, likviditet og budget.
- **Nærtstående parter (ISA 550):** transaktioner med {{ kunde.kapitalejere }} og ledelse, herunder mellemregninger.

## 5. Revisionstilgang
| Område | Risiko (lav/middel/høj) | Tilgang (kontrol/substans) | Ansvarlig | Arbejdspapir |
|---|---|---|---|---|
| Omsætning og tilgodehavender | | | | |
{% if branche.lager %}| Varelager og vareforbrug | | | | |
{% endif %}{% if branche.igangvaerende_arbejder %}| Igangværende arbejder | | | | |
{% endif %}{% if branche.ejendom %}| Investeringsejendomme/grunde og bygninger | | | | |
{% endif %}{% if branche.holding %}| Kapitalandele og koncernmellemværender | | | | |
{% endif %}| Materielle anlægsaktiver | | | | |
| Likvider og gæld til kreditinstitutter | | | | |
| Leverandørgæld og omkostninger | | | | |
| Løn og personaleomkostninger | | | | |
| Moms og skat (aktuel og udskudt) | | | | |
| Egenkapital og kapitalejerlån | | | | |
| Noteoplysninger og ledelsesberetning | | | | |

## 6. Eksterne bekræftelser og specialister
- [ ] Engagementsforespørgsel til pengeinstitut(ter)
- [ ] Saldobekræftelser debitorer/kreditorer (udvalg efter væsentlighed og risiko)
- [ ] Advokatforespørgsel (ved verserende sager eller juridisk bistand i året)
{% if branche.lager %}- [ ] Deltagelse i lageroptælling den ______________
{% endif %}{% if branche.ejendom %}- [ ] Behov for ekstern valuar/ekspert (ISA 620)
{% endif %}

## 7. Tidsplan og kommunikation
| Milepæl | Dato |
|---|---|
| Planlægningsmøde med kunden | {{ felt.dato_planlaegning }} |
| Materialeliste sendt / frist | |
| Feltarbejde | {{ felt.dato_feltarbejde }} |
| Afslutningsmøde og ledelseserklæring | |
| Underskrift af årsrapport | {{ felt.dato_afslutning }} |
| Indsendelse til Erhvervsstyrelsen (senest) | {{ regnskab.frist_aarsrapport }} |

Kommunikation med den øverste ledelse (ISA 260/265): {% if kunde.selskabsform_kode == "as" %}revisionsprotokollat til bestyrelsen{% else %}brev/møde med {{ kunde.ledelsesorgan }}{% endif %}.

## 8. Godkendelse
Strategien og planen er drøftet med teamet, og alle teammedlemmer er orienteret om væsentlige risici og muligheden for besvigelser (ISA 240 – drøftelse i opgaveteamet; ISA 315).

Opgaveansvarlig: ______________________ Dato: ____________
