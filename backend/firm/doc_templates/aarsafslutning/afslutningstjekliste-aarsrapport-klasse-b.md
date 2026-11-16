---
{
  "title": "Afslutningstjekliste – årsrapport klasse B",
  "description": "Tjekliste til gennemgang af årsrapportens form og indhold efter årsregnskabsloven for klasse B (inkl. mikrovirksomheder), før underskrift og indsendelse.",
  "kind": "tjekliste",
  "references": ["Årsregnskabsloven §§ 7-11, 13, 19, 22-24, 53, 64, 72, 77, 83, 135, 138", "Selskabsloven §§ 115, 119, 180-182", "Erklæringsbekendtgørelsen", "Erhvervsstyrelsens taksonomi (XBRL/iXBRL)"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "mikro", "label": "Virksomheden er mikrovirksomhed (ÅRL § 7, stk. 2, nr. 1)", "type": "checkbox"},
    {"name": "revision_fravalgt", "label": "Revision er fravalgt (ÅRL § 135, stk. 1)", "type": "checkbox"},
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

Svar: OK / Ikke relevant / Bemærkning (henvis til arbejdspapir).

## 1. Klasse og størrelsesgrænser
- [ ] Regnskabsklasse er korrekt fastlagt: klasse B, og virksomheden har ikke to år i træk overskredet to af tre grænser for klasse C (ÅRL § 7, stk. 2, nr. 2, med gældende beløbsgrænser efter seneste lovændring)
- [ ] {% if felt.mikro %}Mikrovirksomhed: har ikke to år i træk overskredet to af grænserne (balancesum, nettoomsætning, 10 ansatte); de valgte lempelser er anvendt konsekvent{% else %}Mikrolempelser er ikke anvendt, eller det er dokumenteret, at virksomheden ikke længere er mikrovirksomhed{% endif %}
- [ ] Fravalg af lempelser/tilvalg af bestemmelser fra højere klasse er anvendt konsekvent (ÅRL § 7, stk. 3; § 23)
- [ ] Betingelser for fravalg af revision er opfyldt (ÅRL § 135: to år i træk under to af grænserne – balancesum 4 mio. kr., nettoomsætning 8 mio. kr., 12 ansatte), og der er ikke krav om revision fra fx Erhvervsstyrelsen efter § 135, stk. 6, eller fordi virksomheden er holding med aktivitet over grænserne

## 2. Årsrapportens bestanddele (ÅRL § 22)
- [ ] Forside og virksomhedsoplysninger (navn, CVR, hjemstedskommune, regnskabsperiode, ledelse, revisor) – ÅRL § 11 og § 19
- [ ] Ledelsespåtegning (ÅRL § 9) – se afsnit 3
- [ ] Erklæring fra revisor, hvis afgivet, og påtegningen henviser til den korrekte årsrapport
- [ ] {% if felt.mikro %}Ledelsesberetning kan udelades (mikrovirksomhed), medmindre der er oplysninger, der skal gives (fx usikkerhed om fortsat drift, egne kapitalandele){% else %}Ledelsesberetning (ÅRL § 77, jf. § 77 a/§ 99 for klasse B) – se afsnit 4{% endif %}
- [ ] Resultatopgørelse (artsopdelt eller funktionsopdelt; bruttofortjeneste efter § 32 er anvendt korrekt)
- [ ] Balance (skemaopstilling efter bilag 2, skema A/B)
- [ ] Egenkapitalopgørelse/egenkapitalnote (krav for klasse B – mikro kan udelade)
- [ ] Anvendt regnskabspraksis (ÅRL § 53) – {% if felt.mikro %}mikro kan give begrænsede oplysninger{% else %}fuldstændig beskrivelse af indregnings- og målegrundlag{% endif %}
- [ ] Noter (se afsnit 5)
- [ ] Pengestrømsopgørelse er IKKE krævet for klasse B (frivillig)

## 3. Ledelsespåtegning (ÅRL § 9)
- [ ] Erklæring om, at årsrapporten giver et retvisende billede (§ 11) og er aflagt efter årsregnskabsloven
- [ ] Erklæring om, at ledelsesberetningen indeholder en retvisende redegørelse (hvis der er ledelsesberetning)
{% if felt.revision_fravalgt %}- [ ] Erklæring om, at ledelsen anser betingelserne for at undlade revision for opfyldt (fravalgserklæring i ledelsespåtegningen)
{% endif %}- [ ] Indstilling til godkendelse på generalforsamlingen
- [ ] Underskrevet af alle medlemmer af {{ kunde.ledelsesorgan }} med navn og funktion; afvigende opfattelser er anført
- [ ] Dirigentens erklæring om godkendelse er medtaget (navn på dirigent, dato for generalforsamling)

{% if not felt.mikro %}## 4. Ledelsesberetning (ÅRL § 77)
- [ ] Beskrivelse af væsentlige ændringer i aktiviteter og økonomiske forhold
- [ ] Usikkerhed ved indregning eller måling og usædvanlige forhold, der har påvirket indregning eller måling (skal oplyses i ledelsesberetning eller noter)
- [ ] Begivenheder efter balancedagen af væsentlig betydning (ISA 560)
- [ ] Erhvervelse og afhændelse af egne kapitalandele, hvis relevant
- [ ] Filialer i udlandet, hvis relevant
- [ ] Usikkerhed om fortsat drift – omtale af kapitaltab og ledelsens planer (SL § 119), se going concern-arbejdspapir
{% endif %}
## 5. Noter (klasse B – minimumskrav)
- [ ] Anvendt regnskabspraksis, herunder ændringer og deres effekt (ÅRL § 53; § 13 om konsistens)
- [ ] Gennemsnitligt antal heltidsbeskæftigede medarbejdere i året
- [ ] Eventualforpligtelser og eventualaktiver (ÅRL § 64): kautioner, garantier, uopsigelige lejeforpligtelser, sambeskatningshæftelse{% if branche.byggeri %}, arbejdsgarantier/entreprisegarantier{% endif %}
- [ ] Sikkerhedsstillelser: pantsatte aktiver og bogført værdi heraf (ejerpantebreve, virksomhedspant, deponeringer)
- [ ] Langfristet gæld: andel, der forfalder efter mere end 5 år
- [ ] Lån og forskud til ledelsesmedlemmer (ÅRL § 72): beløb, rente, hovedvilkår og tilbagebetalte beløb
- [ ] Nærtstående parter (ÅRL § 98 c): oplysning om transaktioner, der ikke er gennemført på normale markedsvilkår – klasse B har lempelser; vurder omfanget konkret
- [ ] Kontrollerende kapitalejer/modervirksomhed og koncernregnskab, hvis virksomheden indgår i en koncern
- [ ] Usikkerhed ved indregning og måling (skøn) og usædvanlige forhold
- [ ] Ekstraordinære poster er ikke anvendt (ophævet) – usædvanlige poster oplyses særskilt
- [ ] Udskudt skat (eller udskudt skatteaktiv og grundlaget for indregning)
{% if branche.ejendom %}- [ ] Investeringsejendomme målt til dagsværdi (ÅRL § 38): væsentlige forudsætninger (afkastkrav), følsomhed og dagsværdireguleringer i resultatopgørelsen; reserve efter § 41 overvejet
{% endif %}{% if branche.holding %}- [ ] Kapitalandele i dattervirksomheder/associerede virksomheder: navn, hjemsted, ejerandel, egenkapital og resultat; reserve for nettoopskrivning efter indre værdis metode (ÅRL § 43 a)
{% endif %}{% if branche.igangvaerende_arbejder %}- [ ] Igangværende arbejder for fremmed regning: salgsværdi, aconto-faktureringer og nettopræsentation (aktiv/forpligtelse); praksis for indregning (produktionsmetoden)
{% endif %}{% if branche.lager %}- [ ] Varebeholdninger: målegrundlag (FIFO/vejede gennemsnitspriser), nedskrivninger og evt. pantsætning
{% endif %}{% if branche.landbrug %}- [ ] Biologiske aktiver og EU-støtte: målegrundlag og regnskabspraksis
{% endif %}- [ ] Aktiverede udviklingsomkostninger og bunden reserve for udviklingsomkostninger (ÅRL § 83)
- [ ] Anlægsnoter (kostpris primo, tilgang, afgang, af- og nedskrivninger, regnskabsmæssig værdi ultimo)

## 6. Egenkapital og selskabsret
- [ ] Selskabskapital svarer til registreringen i CVR
- [ ] Forslag til resultatdisponering (ÅRL § 31) er i overensstemmelse med ledelsens indstilling
- [ ] Foreslået udbytte er vist som særskilt post under egenkapitalen, og det er forsvarligt (SL §§ 115, 180-182)
- [ ] Bundne reserver (udvikling, indre værdi, opskrivning) er opgjort korrekt og fragår i frie reserver
- [ ] Kapitaltab: hvis egenkapitalen udgør mindre end halvdelen af selskabskapitalen, skal ledelsen redegøre på generalforsamlingen (SL § 119)
- [ ] Lån til kapitalejere og ledelse: vist som særskilt post i balancen og oplyst efter ÅRL § 72; forsvarlighed vurderet (SL § 115). De særlige regler i SL §§ 210-212 er ophævet fra 1. januar 2025, men lån til personlige hovedaktionærer beskattes fortsat efter ligningsloven § 16 E – manglende indeholdelse af A-skat/udbytteskat kan være en skatteretlig overtrædelse, der skal omtales i påtegningen (ledelsesansvar)

## 7. Afstemninger og konsistens
- [ ] Årsrapporten stemmer til saldobalance og efterposteringsliste (alle korrektioner er bogført i programmet)
- [ ] Sammenligningstal er korrekte og stemmer til sidste års godkendte årsrapport; ændringer er forklaret
- [ ] Tværgående kontrol: noter, ledelsesberetning og hovedopgørelser er indbyrdes konsistente
- [ ] Skat i resultatopgørelse og balance stemmer til skatteopgørelsen
- [ ] Beløb, afrunding, sideoversigt, sprog og stavning er gennemgået

## 8. Erklæring, godkendelse og indsendelse
- [ ] Ledelseserklæring er modtaget, dateret samme dag som eller tæt på påtegningsdatoen (ISA 580)
- [ ] Efterfølgende begivenheder er gennemgået frem til påtegningsdatoen (ISA 560)
- [ ] Erklæringen følger FSR – danske revisorers eksempler for den valgte erklæringstype og indeholder evt. supplerende oplysninger/forbehold
- [ ] Erklæringen er underskrevet med MNE-nummer
- [ ] Generalforsamlingen er afholdt, og årsrapporten er godkendt
- [ ] Årsrapporten er indberettet digitalt (iXBRL) til Erhvervsstyrelsen uden ugrundet ophold efter godkendelsen og senest 6 måneder efter regnskabsårets udløb (ÅRL § 138) – frist: {{ regnskab.frist_aarsrapport }}
- [ ] Kvittering for indsendelse er gemt i sagen

Forventet underskriftsdato: {{ felt.underskrift_dato }}

Gennemgået: ______________________  Godkendt af opgaveansvarlig: ______________________
