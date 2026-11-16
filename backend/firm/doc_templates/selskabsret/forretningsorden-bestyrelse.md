---
{
  "title": "Forretningsorden for bestyrelsen",
  "description": "Forretningsorden efter selskabslovens § 130 for bestyrelser i SMV'er (A/S og ApS med bestyrelse): opgaver, møder, beslutninger, inhabilitet, tavshedspligt, rapportering, kapitalberedskab.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 111, 115, 117, 122-131", "Selskabsloven § 132 (tavshedspligt)", "Selskabsloven § 119"],
  "legal_forms": ["as", "aps", "holding"],
  "industry_aware": true,
  "fields": [
    {"name": "vedtaget_dato", "label": "Vedtaget dato", "type": "date"},
    {"name": "antal_moeder", "label": "Antal ordinære møder pr. år", "type": "number", "default": "4"},
    {"name": "indkaldelsesvarsel", "label": "Indkaldelsesvarsel (dage)", "type": "number", "default": "8"},
    {"name": "formand_afgoer", "label": "Formandens stemme afgør ved stemmelighed (kræver hjemmel i vedtægterne)", "type": "checkbox"},
    {"name": "beloebsgraense", "label": "Beløbsgrænse for dispositioner, der kræver bestyrelsens godkendelse (kr.)", "type": "number", "default": "250000"},
    {"name": "rapportering", "label": "Rapporteringsfrekvens fra direktionen", "type": "select", "options": ["Månedlig", "Kvartalsvis"], "default": "Månedlig"},
    {"name": "elektroniske_moeder", "label": "Møder kan holdes elektronisk/skriftligt", "type": "checkbox", "default": true}
  ]
}
---
# Forretningsorden for bestyrelsen i {{ kunde.navn }}

CVR-nr. {{ kunde.cvr }}

Denne forretningsorden er fastsat af bestyrelsen i medfør af selskabslovens § 130 og supplerer selskabsloven og selskabets vedtægter. Ved uoverensstemmelse går lov og vedtægter forud.

## § 1 Bestyrelsens opgaver
1. Bestyrelsen varetager den overordnede og strategiske ledelse og sikrer en forsvarlig organisation af selskabets virksomhed (selskabslovens § 115).
2. Bestyrelsen påser, at
   - bogføringen og regnskabsaflæggelsen foregår tilfredsstillende efter selskabets forhold,
   - der er etableret de fornødne procedurer for risikostyring og interne kontroller,
   - bestyrelsen løbende modtager den fornødne rapportering om de finansielle forhold,
   - direktionen udøver sit hverv på behørig måde og efter bestyrelsens retningslinjer, og
   - kapitalberedskabet til enhver tid er forsvarligt, herunder at der er tilstrækkelig likviditet til nuværende og fremtidige forpligtelser.
3. Bestyrelsen ansætter og afskediger direktionen, fastsætter dens vilkår og udsteder en skriftlig direktionsinstruks.
4. Bestyrelsen godkender årligt strategi, budget og likviditetsbudget samt forsikringsforhold og it-sikkerhed.
5. Konstaterer bestyrelsen, at egenkapitalen udgør mindre end halvdelen af selskabskapitalen, skal den sikre, at der afholdes generalforsamling senest 6 måneder efter konstateringen (selskabslovens § 119).
6. Bestyrelsen sikrer, at selskabets reelle ejere er korrekt registreret, og at resultatet af den årlige undersøgelse fremlægges på årsregnskabsmødet (selskabslovens § 58 a, stk. 4).

## § 2 Konstituering
Bestyrelsen vælger umiddelbart efter hver ordinære generalforsamling en formand{% if kunde.selskabsform_kode == "as" %} og en næstformand. En direktør kan ikke være formand eller næstformand (selskabslovens § 111, stk. 1, nr. 1){% else %} og eventuelt en næstformand{% endif %}. Formanden leder bestyrelsens arbejde og sikrer, at møder holdes, når det er nødvendigt.

## § 3 Møder
1. Der afholdes mindst {{ felt.antal_moeder }} ordinære møder årligt efter en årsplan, herunder et årsregnskabsmøde og et budgetmøde.
2. Formanden indkalder med mindst {{ felt.indkaldelsesvarsel }} dages varsel med dagsorden og materiale. Et bestyrelsesmedlem, en direktør eller selskabets generalforsamlingsvalgte revisor kan forlange, at bestyrelsen indkaldes (selskabslovens § 123).
{% if felt.elektroniske_moeder %}3. Møder kan afholdes som video- eller telefonmøder eller skriftligt, når formanden finder det forsvarligt, og intet medlem modsætter sig det.
{% endif %}4. Direktionen deltager i møderne uden stemmeret, medmindre bestyrelsen bestemmer andet. Revisor deltager i årsregnskabsmødet.

## § 4 Beslutninger
1. Bestyrelsen er beslutningsdygtig, når over halvdelen af samtlige medlemmer er repræsenteret (selskabslovens § 124).
2. Beslutninger træffes ved simpelt flertal.{% if felt.formand_afgoer %} Ved stemmelighed er formandens, ved dennes forfald næstformandens, stemme afgørende.{% else %} Ved stemmelighed er forslaget forkastet.{% endif %}
3. Beslutning i vigtige sager må ikke træffes, uden at alle medlemmer så vidt muligt har haft lejlighed til at deltage i behandlingen.

## § 5 Inhabilitet
Et medlem må ikke deltage i behandlingen af aftaler mellem selskabet og medlemmet selv, søgsmål mod medlemmet selv eller aftaler/søgsmål med tredjemand, hvis medlemmet har en væsentlig interesse heri, der kan være stridende mod selskabets (selskabslovens § 131). Medlemmet skal selv oplyse om mulig inhabilitet. Inhabilitet føres til protokols.

## § 6 Protokol
Der føres protokol over forhandlingerne, som underskrives af samtlige tilstedeværende medlemmer (selskabslovens § 128). Et medlem eller en direktør, der ikke er enig i en beslutning, har ret til at få sin opfattelse indført. Revisionsprotokollatet fremlægges på førstkommende møde, og hvert medlem underskriver det til bekræftelse af, at det er gennemgået.

## § 7 Rapportering fra direktionen
Direktionen rapporterer til bestyrelsen (frekvens: {{ felt.rapportering }}) om resultat og likviditet sammenholdt med budget, ordrebeholdning, væsentlige risici og afvigelser.{% if branche.byggeri or branche.igangvaerende_arbejder %} Rapporteringen omfatter status på igangværende arbejder og tabsgivende projekter samt stillede garantier.{% endif %}{% if branche.lager %} Rapporteringen omfatter lagerstatus og ukurans.{% endif %}{% if branche.finans %} Rapporteringen omfatter solvens, likviditetsdækning og compliance med tilladelser og hvidvaskregler.{% endif %}{% if branche.kontantintensiv %} Rapporteringen omfatter kontantstyring og kassekontrol.{% endif %}

## § 8 Dispositioner af usædvanlig art eller stor betydning
Følgende kræver bestyrelsens forudgående godkendelse (selskabslovens § 117, stk. 1):
- Køb, salg eller pantsætning af fast ejendom og virksomheder eller kapitalandele.
- Investeringer og enkeltaftaler over {{ felt.beloebsgraense }} kr. ud over budget.
- Optagelse af lån, kautioner, garantier og sikkerhedsstillelse uden for den daglige drift.
- Aftaler med kapitalejere, ledelsesmedlemmer eller nærtstående (herunder lån og sikkerhedsstillelse).
- Ansættelse og afskedigelse af ledende medarbejdere samt bonus- og pensionsordninger.
- Indledning af retssager af væsentlig betydning.

## § 9 Tavshedspligt
Bestyrelsens medlemmer har tavshedspligt om alt, hvad de erfarer i deres egenskab af bestyrelsesmedlemmer, medmindre det skal oplyses til generalforsamlingen (selskabslovens § 132). Materiale opbevares forsvarligt og tilbageleveres eller slettes ved fratræden.

## § 10 Evaluering og ændring
Bestyrelsen gennemgår forretningsordenen årligt og evaluerer sit arbejde. Ændringer vedtages af bestyrelsen.

Vedtaget på bestyrelsesmøde den {{ felt.vedtaget_dato }}.

| Navn | Underskrift |
|---|---|
| | |
| | |
| | |
