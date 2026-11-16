---
{
  "title": "Afslutningstjekliste – årsrapport klasse B",
  "description": "Tjekliste til gennemgang af årsrapportens form og indhold efter årsregnskabsloven for klasse B (inkl. mikrovirksomheder), før underskrift og indsendelse.",
  "kind": "tjekliste",
  "references": ["Årsregnskabsloven §§ 7, 9-11, 13, 22-24, 31-33, 53, 63-64, 67 a, 68, 71, 73, 76 a, 77, 135, 135 a, 138 (LBK nr. 402 af 23. marts 2026)", "Selskabsloven §§ 88, 119, 127, 179-180", "Erklæringsbekendtgørelsen", "Erhvervsstyrelsens taksonomi (XBRL/iXBRL)"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "mikro", "label": "Virksomheden er mikrovirksomhed (ÅRL § 22 a)", "type": "checkbox"},
    {"name": "revision_fravalgt", "label": "Revision er fravalgt (ÅRL § 135, stk. 1, 3. pkt.)", "type": "checkbox"},
    {"name": "erklaering", "label": "Erklæring på årsrapporten", "type": "select", "options": ["Revisionspåtegning", "Udvidet gennemgang", "Review", "Assistance (opstilling)", "Ingen"], "default": "Revisionspåtegning"},
    {"name": "underskrift_dato", "label": "Forventet underskriftsdato", "type": "date"}
  ]
}
---
# Afslutningstjekliste – årsrapport klasse B, {{ regnskab.aar }}

**Virksomhed:** {{ kunde.navn }}, CVR {{ kunde.cvr }}
**Regnskabsår:** {{ regnskab.start }} – {{ regnskab.slut }}
**Størrelse:** {% if felt.mikro %}Mikrovirksomhed{% else %}Lille virksomhed (klasse B){% endif %}
**Erklæring:** {{ felt.erklaering }}{% if felt.revision_fravalgt %} (revision fravalgt){% endif %}
**Frist for indsendelse:** {{ regnskab.frist_aarsrapport }}
**Gennemgået af:** {{ medarbejder.navn }}, {{ dato.idag }}

Svar: OK / Ikke relevant / Bemærkning (henvis til arbejdspapir). Paragrafhenvisninger er til årsregnskabsloven (ÅRL), LBK nr. 402 af 23. marts 2026, medmindre andet er anført.

## 1. Klasse og størrelsesgrænser
- [ ] Regnskabsklasse er korrekt fastlagt: virksomheden er en lille virksomhed (klasse B), dvs. den har ikke i to på hinanden følgende regnskabsår på balancetidspunktet overskredet to af grænserne balancesum 55 mio. kr., nettoomsætning 111 mio. kr. og 50 heltidsbeskæftigede (ÅRL § 7, stk. 2, nr. 1). De forhøjede grænser har virkning for regnskabsår, der begynder 1. januar 2024 eller senere (lov nr. 480 af 22. maj 2024, § 14, stk. 1) – overgangsreglerne er vurderet
- [ ] {% if felt.mikro %}Mikrovirksomhed: har ikke i to på hinanden følgende regnskabsår overskredet to af grænserne balancesum 3,5 mio. kr., nettoomsætning 7 mio. kr. og 10 heltidsbeskæftigede (§ 22 a, stk. 1), og er ikke udelukket efter § 22 a, stk. 3 (fx kapitalinteresser med betydelig indflydelse eller afledte finansielle instrumenter); anvendte undtagelser efter § 22 b er oplyst i noterne (§ 22 b, stk. 2){% else %}Mikroundtagelserne i § 22 b er ikke anvendt, eller det er dokumenteret, at betingelserne i § 22 a er opfyldt{% endif %}
- [ ] Tilvalg af regler fra højere regnskabsklasser er anvendt systematisk og konsekvent (§ 7, stk. 6)
- [ ] Betingelser for fravalg af revision er opfyldt (§ 135, stk. 1, 3. pkt.: to år i træk under to af grænserne – balancesum 4 mio. kr., nettoomsætning 8 mio. kr., 12 heltidsbeskæftigede), balancesummen har ikke to år i træk overskredet 50 mio. kr. (§ 135, stk. 2), reglen for virksomheder med kapitalinteresser er vurderet (§ 135, stk. 4), og der foreligger ikke udelukkelsesgrunde efter § 135 a (dom/bødeforelæg, konkurskarantæne).{% if branche.risikobranche %} **Virksomheden er i en klassificeret risikobranche (BEK nr. 1488 af 27. november 2025):** overstiger nettoomsætningen 5 mio. kr. to år i træk, kræves trods fravalg af revision mindst en erklæring om assistance med opstilling eller en erklæring med sikkerhed (§ 135, stk. 5){% endif %}

## 2. Årsrapportens bestanddele (ÅRL § 22)
- [ ] Forside og virksomhedsoplysninger (navn, CVR, regnskabsperiode, ledelse, revisor)
- [ ] Ledelsespåtegning (§ 9) – kan undlades, hvis ledelsesorganet kun har ét medlem (§ 9 a) – se afsnit 3
- [ ] Erklæring fra revisor, hvis afgivet, indgår i årsrapporten (§ 22, stk. 1) og henviser til den korrekte årsrapport
- [ ] Ledelsesberetning (§ 22, stk. 1, og § 76 a) – kravet gælder også mikrovirksomheder; § 22 b giver kun lempelser for noterne – se afsnit 4
- [ ] Resultatopgørelse (artsopdelt eller funktionsopdelt; sammendragning til bruttofortjeneste efter § 32 er anvendt korrekt)
- [ ] Balance og resultatopgørelse er opstillet efter bilag 2, skema 1 eller 2 og skema 3 eller 4 (§ 23), med sammenligningstal (§ 24)
- [ ] Egenkapitalopgørelse er ikke et krav i klasse B (krav i klasse C, § 86 a). Resultatdisponering (§ 31) samt oversigt over dagsværdireserve (§ 55 a) og opskrivningsreserve (§ 58) gives, hvis relevant
- [ ] Anvendt regnskabspraksis (§ 53) – {% if felt.mikro %}mikrovirksomheder kan undlade redegørelsen (§ 22 b, stk. 1, nr. 1) og skal i så fald oplyse det (§ 22 b, stk. 2){% else %}redegørelse for indregningsmetoder og målegrundlag samt oplysning om regnskabsklassen (§ 53, stk. 1){% endif %}
- [ ] Noter (se afsnit 5)
- [ ] Pengestrømsopgørelse er ikke krævet i klasse B (krav i klasse C, § 86)

## 3. Ledelsespåtegning (ÅRL § 9)
- [ ] Erklæring om, hvorvidt årsrapporten er aflagt i overensstemmelse med lovgivningen og eventuelle krav i vedtægter, og hvorvidt årsregnskabet giver et retvisende billede (§ 9, stk. 1, nr. 1-2)
- [ ] Bemærk: erklæringen om ledelsesberetningen i § 9, stk. 3, gælder kun virksomheder med værdipapirer optaget til handel på et reguleret marked og statslige aktieselskaber
{% if felt.revision_fravalgt %}- [ ] Erklæring om, hvorvidt virksomheden opfylder betingelserne for at undlade revision (§ 9, stk. 6)
{% endif %}- [ ] Indstilling til godkendelse på generalforsamlingen
- [ ] Underskrevet og dateret af alle medlemmer af {{ kunde.ledelsesorgan }} (§ 9, stk. 1; ved digital underskrift skal underskriverens navn fremgå tydeligt, § 9, stk. 2); evt. indvendinger er anført med begrundelse (§ 10)
- [ ] Oplysning om godkendelse på generalforsamlingen (dato og dirigent) er medtaget, hvis den anvendes

## 4. Ledelsesberetning (ÅRL §§ 76 a og 77)
- [ ] Beskrivelse af virksomhedens væsentligste aktiviteter (§ 76 a, nr. 1)
- [ ] Redegørelse for eventuelle væsentlige ændringer i virksomhedens aktiviteter og økonomiske forhold (§ 76 a, nr. 2)
- [ ] Egne kapitalandele: antal, pålydende værdi, andel af kapitalen, erhvervelser/afhændelser i året og årsager hertil (§ 77), hvis relevant
- [ ] Yderligere oplysninger, hvis lovens bestemmelser ikke er tilstrækkelige til at give et retvisende billede (§ 11, stk. 2) – fx usikkerhed om fortsat drift og kapitaltab (SL § 119, se going concern-arbejdspapir), væsentlig usikkerhed ved indregning eller måling eller væsentlige begivenheder efter balancedagen. (De særskilte krav om begivenheder efter balancedagen, § 98 d, og ledelsesberetningens indhold i § 99 gælder klasse C.)

## 5. Noter (klasse B)
- [ ] Anvendt regnskabspraksis, herunder ændringer og deres effekt (§§ 51 og 53; reel kontinuitet, § 13, stk. 2)
- [ ] Gennemsnitligt antal heltidsbeskæftigede i regnskabsåret (§ 68; mikrovirksomheder kan undlade, § 22 b, stk. 1, nr. 4)
- [ ] Eventualforpligtelser og andre forpligtelser, der ikke er indregnet (§ 64, stk. 1): kautioner, garantier, leasing- og lejeforpligtelser, sambeskatningshæftelse{% if branche.byggeri %}, arbejdsgarantier/entreprisegarantier{% endif %}
- [ ] Pantsætninger og sikkerhedsstillelser: samlet omfang og regnskabsmæssig værdi af de pantsatte aktiver (§ 64, stk. 2); forhold over for tilknyttede og associerede virksomheder særskilt (§ 64, stk. 3)
- [ ] Gæld, der forfalder til betaling mere end 5 år efter balancetidspunktet (§ 63; mikrovirksomheder kan undlade, § 22 b, stk. 1, nr. 2)
- [ ] Tilgodehavender hos og sikkerhedsstillelser for medlemmer af ledelsen (§ 73): summen pr. ledelseskategori, væsentligste vilkår inkl. rentefod, tilbagebetalte beløb, nedskrivninger/afkald og lån optaget og indfriet i året
- [ ] Nærtstående parter: oplysningskravet i § 98 c gælder regnskabsklasse C og er ikke blandt de bestemmelser, der gælder for klasse B (§ 22, stk. 1); særregel for erhvervsdrivende fonde i § 69, stk. 3. Vurder, om oplysning er nødvendig for et retvisende billede (§ 11, stk. 2)
- [ ] Navn og hjemsted for den modervirksomhed, der udarbejder koncernregnskab for den mindste koncern, virksomheden indgår i (§ 71)
- [ ] Særlige poster på grund af størrelse eller art, herunder nedskrivninger og tilbageførsler (§ 67 a; mikrovirksomheder kan undlade nr. 1 og 2, § 22 b, stk. 1, nr. 3); ændrede regnskabsmæssige skøn (§ 54)
- [ ] Ekstraordinære poster anvendes ikke (posten findes ikke i skemaerne i bilag 2) – særlige poster oplyses efter § 67 a
- [ ] Udskudt skat er indregnet som hensat forpligtelse (§ 47); et udskudt skatteaktiv er kun indregnet, hvis betingelserne i § 33 er opfyldt
{% if branche.ejendom %}- [ ] Investeringsejendomme målt til dagsværdi (§ 38): dagsværdi ultimo og årets ændringer (§ 58 a, stk. 1) samt centrale forudsætninger, når dagsværdien ikke måles på grundlag af et aktivt marked (§ 58 a, stk. 2). Opskrivningsreglen i § 41 gælder ikke investeringsejendomme. Mikrovirksomheder, der anvender undtagelserne i § 22 b, kan ikke anvende § 38 (§ 22 b, stk. 4)
{% endif %}{% if branche.holding %}- [ ] Kapitalandele i dattervirksomheder/associerede virksomheder: målegrundlag (kostpris eller indre værdi, § 43 a); ved indre værdi: reserve for nettoopskrivning (§ 43 a, stk. 5) og forskelsbeløb ved første indregning (§ 58 c)
{% endif %}{% if branche.igangvaerende_arbejder %}- [ ] Igangværende arbejder for fremmed regning: salgsværdi, aconto-faktureringer og præsentation (aktiv/forpligtelse); praksis for indregning (produktionsmetoden kan fravælges, § 49, stk. 1)
{% endif %}{% if branche.lager %}- [ ] Varebeholdninger: målegrundlag (FIFO, vejede gennemsnitspriser eller lignende metode, § 45), nedskrivning til nettorealisationsværdi (§ 46) og evt. pantsætning
{% endif %}{% if branche.landbrug %}- [ ] Biologiske aktiver og EU-støtte: målegrundlag (dagsværdi efter § 38, stk. 2, eller kostpris) og regnskabspraksis
{% endif %}- [ ] Aktiverede udviklingsomkostninger (valgfrit i klasse B, § 33, stk. 1) og reserve for udviklingsomkostninger under egenkapitalen (bilag 2; Erhvervsstyrelsens vejledning om indregning af immaterielle anlægsaktiver)
- [ ] Anlægsnoter (kostpris primo, tilgang, afgang, af- og nedskrivninger, regnskabsmæssig værdi ultimo) – lovkrav i klasse C (§ 88), frivillige i klasse B

## 6. Egenkapital og selskabsret
- [ ] Selskabskapital svarer til registreringen i CVR
- [ ] Ledelsens forslag til resultatdisponering er placeret i tilknytning til resultatopgørelsen, og ekstraordinært udbytte udloddet i året fremgår særskilt (ÅRL § 31)
- [ ] Foreslået udbytte er vist som særlig post i egenkapitalen (ÅRL § 31, stk. 1), overstiger ikke de frie reserver (SL § 180, stk. 2) og er forsvarligt (SL § 179, stk. 2)
- [ ] Bundne reserver (udvikling, indre værdi, opskrivning) er opgjort korrekt og fragår i frie reserver
- [ ] Kapitaltab: udgør egenkapitalen mindre end halvdelen af den tegnede kapital, skal ledelsen sikre, at der senest 6 måneder efter konstateringen afholdes generalforsamling, hvor ledelsen redegør for den økonomiske stilling (SL § 119)
- [ ] Lån til kapitalejere og ledelse: oplyst efter ÅRL § 73; forsvarlighed og vilkår vurderet (SL § 115, nr. 5, og § 127). De særlige regler i SL §§ 210-212 er ophævet fra 1. januar 2025 (lov nr. 1668 af 30. december 2024), men lån til personlige kapitalejere med bestemmende indflydelse beskattes fortsat efter ligningsloven § 16 E (reglerne om tilbagebetaling ændret for lån ydet fra 1. januar 2026, lov nr. 749 af 20. juni 2025). Manglende indeholdelse af skat kan være en overtrædelse, som revisor skal vurdere at omtale i erklæringen (erklæringsbekendtgørelsen)

## 7. Afstemninger og konsistens
- [ ] Årsrapporten stemmer til saldobalance og efterposteringsliste (alle korrektioner er bogført i programmet)
- [ ] Sammenligningstal er korrekte og stemmer til sidste års godkendte årsrapport; primobalance = ultimobalance sidste år (§ 13, stk. 1, nr. 9); ændringer er forklaret
- [ ] Tværgående kontrol: noter, ledelsesberetning og hovedopgørelser er indbyrdes konsistente
- [ ] Skat i resultatopgørelse og balance stemmer til skatteopgørelsen
- [ ] Beløb, afrunding, sideoversigt, sprog og stavning er gennemgået

## 8. Erklæring, godkendelse og indsendelse
- [ ] Ledelseserklæring er modtaget og dateret så tæt som muligt på, men ikke efter, påtegningsdatoen (ISA 580, pkt. 14)
- [ ] Efterfølgende begivenheder er gennemgået frem til påtegningsdatoen (ISA 560)
- [ ] Erklæringen følger FSR – danske revisorers eksempler for den valgte erklæringstype og indeholder evt. supplerende oplysninger/forbehold
- [ ] Revisors navn og MNE-nummer samt revisionsvirksomhedens CVR-nummer er anført (bekendtgørelse nr. 859 af 18. juni 2025 om indberetning af årsrapporter m.v.)
- [ ] Generalforsamlingen er afholdt i så god tid, at årsrapporten kan nå Erhvervsstyrelsen inden fristen (SL § 88, stk. 2), og årsrapporten er godkendt
- [ ] Årsrapporten er indberettet digitalt (iXBRL) til Erhvervsstyrelsen uden ugrundet ophold efter godkendelsen og modtaget senest 6 måneder efter regnskabsårets afslutning (ÅRL § 138, stk. 1 – der kan ikke dispenseres) – frist: {{ regnskab.frist_aarsrapport }}
- [ ] Kvittering for indsendelse er gemt i sagen

Forventet underskriftsdato: {{ felt.underskrift_dato }}

Gennemgået: ______________________  Godkendt af opgaveansvarlig: ______________________
