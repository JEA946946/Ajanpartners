---
{
  "title": "Ledelseserklæring – revision af årsregnskab (ISA 580)",
  "description": "Skriftlig ledelseserklæring til revisor ved revision af årsregnskabet. Dækker ISA 580 og de specifikke krav i ISA 240, 250, 450, 501, 540, 550, 560 og 570 samt danske forhold (kapitalejerlån, skatter og afgifter, bogføringsloven). Branchespecifikke afsnit om varelager, igangværende arbejder, investeringsejendomme, kontantsalg, moms og biologiske aktiver. Dateres samme dag som påtegningen.",
  "kind": "brev",
  "references": ["ISA 580", "ISA 240", "ISA 250", "ISA 450", "ISA 501", "ISA 540", "ISA 550", "ISA 560", "ISA 570", "Selskabsloven §§ 115-119, 127 og 179", "Selskabsloven §§ 210 og 215 (ophævet pr. 1/1 2025 – ældre lån)", "Ligningsloven § 16 E", "Bogføringsloven (lov nr. 700 af 24/05/2022)"],
  "legal_forms": ["aps", "as", "ivs", "holding", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "erklaeringsdato", "label": "Dato (samme som revisionspåtegningen)", "type": "text", "default": "{{ dato.idag }}"},
    {"name": "har_bestyrelse", "label": "Selskabet har en bestyrelse (ApS)", "type": "checkbox", "default": false},
    {"name": "vaesentlighed", "label": "Beløbsgrænse for væsentlige forhold i erklæringen (kr.)", "type": "number"},
    {"name": "ukorrigerede_fejl", "label": "Der er ukorrigerede fejl (liste vedlægges)", "type": "checkbox", "default": false},
    {"name": "naertstaaende", "label": "Nærtstående parter (navne/selskaber, adskilt med komma)", "type": "textarea"},
    {"name": "efterfoelgende", "label": "Begivenheder efter balancedagen, der er oplyst i årsregnskabet (tom = ingen)", "type": "textarea"},
    {"name": "retssager", "label": "Verserende retssager/tvister (tom = ingen)", "type": "textarea"},
    {"name": "fortsat_drift_tilsagn", "label": "Fortsat drift er baseret på tilsagn/kapitalberedskab (beskrivelse, tom = ikke relevant)", "type": "textarea"},
    {"name": "kapitalejerlaan", "label": "Der er ydet lån til kapitalejere/ledelse (oplyses særskilt)", "type": "checkbox", "default": false},
    {"name": "lager_optaellingsdato", "label": "Dato for lageroptælling (hvis relevant)", "type": "text", "default": "{{ regnskab.slut }}"},
    {"name": "ejendom_afkastkrav", "label": "Anvendt afkastkrav for investeringsejendomme (hvis relevant)", "type": "text"},
    {"name": "yderligere", "label": "Yderligere specifikke erklæringer (valgfrit)", "type": "textarea"}
  ]
}
---
**{{ firma.navn }}**
{{ firma.adresse }}
Att.: {{ medarbejder.navn }}

{{ felt.erklaeringsdato }}

# Ledelseserklæring

Denne erklæring afgives i forbindelse med jeres revision af årsregnskabet for {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}, for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}, med henblik på, at I kan udtrykke en konklusion om, hvorvidt årsregnskabet giver et retvisende billede i overensstemmelse med årsregnskabsloven.

Vi bekræfter efter bedste overbevisning og efter at have foretaget de forespørgsler, vi har anset for nødvendige for at kunne afgive erklæringen, følgende. Forhold anses for væsentlige, hvis de enkeltvis eller samlet kan påvirke regnskabsbrugernes økonomiske beslutninger{% if felt.vaesentlighed %}, og under alle omstændigheder forhold over {{ felt.vaesentlighed }} kr.{% else %}.{% endif %}

## 1. Årsregnskabet

1. Vi har opfyldt vores ansvar, som fastsat i opdragsbrevet, for udarbejdelsen af årsregnskabet i overensstemmelse med årsregnskabsloven, og årsregnskabet giver efter vores opfattelse et retvisende billede.
2. De væsentlige forudsætninger, som vi har anvendt ved regnskabsmæssige skøn, herunder skøn målt til dagsværdi, er rimelige, og de tilknyttede oplysninger er passende.
3. Forbindelser og transaktioner med nærtstående parter er indregnet og oplyst i overensstemmelse med årsregnskabsloven.{% if felt.naertstaaende %} Vi har oplyst jer om følgende nærtstående parter: {{ felt.naertstaaende }}.{% endif %}
4. Alle begivenheder efter balancedagen, som efter årsregnskabsloven kræver regulering eller oplysning, er reguleret eller oplyst.{% if felt.efterfoelgende %} Følgende begivenheder er oplyst: {{ felt.efterfoelgende }}{% endif %}
5. {% if felt.ukorrigerede_fejl %}Virkningen af de ikke-korrigerede fejlinformationer, som fremgår af vedlagte oversigt, er efter vores opfattelse uvæsentlig, både enkeltvis og samlet, for årsregnskabet som helhed.{% else %}Der er os bekendt ingen ikke-korrigerede fejlinformationer; alle reguleringer, I har foreslået, er bogført.{% endif %}
6. Alle kendte faktiske og mulige retssager og krav, hvis virkning skal tages i betragtning ved udarbejdelsen af årsregnskabet, er oplyst til jer og er indregnet og oplyst i overensstemmelse med årsregnskabsloven.{% if felt.retssager %} Det drejer sig om: {{ felt.retssager }}{% endif %}
7. Selskabet har tilfredsstillende ejendomsret til alle aktiver, og der er ingen pantsætninger, ejendomsforbehold eller andre sikkerhedsstillelser ud over dem, der er oplyst i årsregnskabet. Alle forpligtelser, herunder eventualforpligtelser, garantier, leasing- og lejeforpligtelser samt kautioner, er indregnet eller oplyst.
8. Vi har vurderet selskabets evne til at fortsætte driften i mindst 12 måneder fra balancedagen og er ikke bekendt med begivenheder eller forhold, der kan skabe betydelig tvivl herom, ud over hvad der er oplyst i årsregnskabet.{% if felt.fortsat_drift_tilsagn %} Vores vurdering er baseret på følgende: {{ felt.fortsat_drift_tilsagn }}{% endif %}

## 2. Oplysninger stillet til rådighed

1. Vi har givet jer adgang til alle oplysninger, som vi er bekendt med, og som er relevante for udarbejdelsen af årsregnskabet, såsom bogføring, dokumentation, referater fra generalforsamlinger{% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %} og bestyrelsesmøder{% endif %}, aftaler og andre forhold.
2. Vi har givet jer de yderligere oplysninger, I har anmodet om, og uhindret adgang til personer i selskabet, som I har fundet det nødvendigt at indhente revisionsbevis fra.
3. Alle transaktioner er registreret i bogføringen og afspejlet i årsregnskabet. Bogføringen er foretaget i overensstemmelse med bogføringsloven, herunder kravene til registrering, dokumentation og opbevaring af regnskabsmateriale i 5 år, og til brug af et digitalt bogføringssystem, når loven kræver det.

## 3. Besvigelser og overholdelse af lovgivning

1. Vi anerkender vores ansvar for at udforme, implementere og opretholde intern kontrol med henblik på at forebygge og opdage besvigelser.
2. Vi har oplyst jer om resultatet af vores vurdering af risikoen for, at årsregnskabet kan indeholde væsentlig fejlinformation som følge af besvigelser.
3. Vi har oplyst jer om alle besvigelser eller mistanker om besvigelser, som vi er bekendt med, og som involverer ledelsen, medarbejdere med betydelige roller i den interne kontrol eller andre, hvor besvigelsen kan have væsentlig indvirkning på årsregnskabet, samt om påstande om besvigelser fremsat af medarbejdere, tidligere medarbejdere, analytikere, myndigheder eller andre.
4. Vi har oplyst jer om alle kendte tilfælde af manglende overholdelse eller mulig manglende overholdelse af love og øvrig regulering, hvis virkning bør tages i betragtning ved udarbejdelsen af årsregnskabet.
5. Selskabet har rettidigt angivet og afregnet moms, A-skat, arbejdsmarkedsbidrag, selskabsskat og øvrige skatter og afgifter, og der er ikke verserende sager med Skattestyrelsen eller andre myndigheder, som ikke er oplyst til jer.
6. {% if felt.kapitalejerlaan %}Vi har oplyst jer om alle lån og sikkerhedsstillelser, som selskabet har ydet til kapitalejere, ledelsesmedlemmer eller disses nærtstående, herunder mellemregninger, herunder vilkår og formål. Lånene er ydet i selskabets interesse og på forsvarlige vilkår, jf. selskabslovens §§ 115-118 og 127, og eventuelle lån ydet før 1. januar 2025 i strid med de dagældende regler i selskabslovens § 210 er tilbagebetalt med renter, jf. § 215. Vi er bekendt med, at lån til personlige kapitalejere og disses nærtstående beskattes efter ligningslovens § 16 E.{% else %}Selskabet har ikke ydet lån eller stillet sikkerhed for kapitalejere, ledelsesmedlemmer eller disses nærtstående, hverken direkte eller i form af mellemregninger.{% endif %}
7. Udlodninger til kapitalejerne i regnskabsåret og frem til i dag er sket i overensstemmelse med selskabslovens §§ 179-183, og selskabets kapitalberedskab er efter vores vurdering forsvarligt, jf. selskabslovens § 115.

{% if branche.lager or branche.igangvaerende_arbejder or branche.investeringsejendomme or branche.kontantintensiv or branche.momsfritaget or branche.landbrug or branche.holding %}## 4. Branchespecifikke forhold

{% if branche.lager %}**Varelager**

- Varebeholdningerne er optalt pr. {{ felt.lager_optaellingsdato }} under betryggende forhold, og alle varer, som selskabet ejer, er medtaget – også varer under transport og hos tredjemand. Varer, der tilhører andre (konsignationsvarer, kundevarer til reparation), er ikke medtaget.
- Beholdningerne er målt til kostpris efter FIFO eller vejede gennemsnitspriser, dog højst til nettorealisationsværdi. Ukurante og langsomt omsættelige varer er nedskrevet.
- Der er foretaget korrekt periodeafgrænsning af varekøb og -salg omkring balancedagen.

{% endif %}{% if branche.igangvaerende_arbejder %}**Igangværende arbejder for fremmed regning**

- Alle igangværende arbejder er medtaget og målt til salgsværdien af det udførte arbejde opgjort efter færdiggørelsesgraden (produktionsmetoden), eller efter den regnskabspraksis, der er oplyst i årsregnskabet.
- Færdiggørelsesgrad og forventede samlede omkostninger pr. projekt er opgjort på et pålideligt grundlag, og forventede tab på tabsgivende kontrakter er indregnet fuldt ud.
- Der er ikke indgået aftaler om ekstraarbejder, bod, garantiforpligtelser eller tvister, som ikke er indregnet eller oplyst.

{% endif %}{% if branche.investeringsejendomme %}**Investeringsejendomme**

- Investeringsejendommene er målt til dagsværdi efter årsregnskabslovens § 38 på grundlag af en afkastbaseret model{% if felt.ejendom_afkastkrav %} med et afkastkrav på {{ felt.ejendom_afkastkrav }}{% endif %}. Forudsætningerne for lejeindtægter, tomgang, drifts- og vedligeholdelsesudgifter og afkastkrav afspejler markedsforholdene på balancedagen.
- Alle lejekontrakter, lejeregulering, depositum og forudbetalt leje er oplyst til jer, og der er ikke indgået aftaler om væsentlige renoveringer eller salg, som ikke er oplyst.
- Dagsværdireguleringer er bundet på en reserve for opskrivninger efter dagsværdi, og der er hensat til udskudt skat.

{% endif %}{% if branche.kontantintensiv %}**Kontantsalg og kasse**

- Alt salg, herunder kontantsalg og MobilePay/kortbetalinger, er registreret løbende og fuldstændigt i kasseapparat/salgssystem, og z-rapporter, dagsopgørelser og kasseafstemninger er opbevaret.
- Der er ikke foretaget private hævninger eller betalinger direkte fra kassen, som ikke er bogført.
- Selskabet har overholdt hvidvasklovens forbud mod at modtage kontante betalinger over den gældende beløbsgrænse.

{% endif %}{% if branche.momsfritaget %}**Moms og lønsumsafgift**

- Fradrag for indgående moms er opgjort korrekt efter momslovens regler om delvis fradragsret, herunder den foreløbige og endelige fradragsprocent, og der er foretaget årsregulering.
- Lønsumsafgift er opgjort og afregnet efter lønsumsafgiftsloven for den momsfritagne del af aktiviteten.
- Reguleringsforpligtelser for investeringsgoder (fast ejendom og maskiner) er opgjort og oplyst.

{% endif %}{% if branche.landbrug %}**Landbrug – biologiske aktiver og støtte**

- Besætninger og afgrøder er optalt og målt efter den oplyste regnskabspraksis, ved dagsværdimåling til dagsværdi med fradrag af forventede salgsomkostninger.
- Landbrugsstøtte (grundbetaling m.v.) er indregnet i den periode, den vedrører, og betingelserne for støtten er opfyldt. Der er ikke modtaget krav om tilbagebetaling, som ikke er indregnet.
- Miljø- og klimaforpligtelser samt eventuelle påbud er oplyst til jer.

{% endif %}{% if branche.holding %}**Kapitalandele og koncernforhold**

- Kapitalandele i dattervirksomheder og associerede virksomheder er målt efter den oplyste regnskabspraksis, og der er ikke indikationer på værdiforringelse ud over det indregnede.
- Alle koncerninterne mellemværender, garantier, kautioner og sambeskatningsforhold er oplyst til jer.

{% endif %}{% endif %}{% if felt.yderligere %}## 5. Øvrige forhold

{{ felt.yderligere }}

{% endif %}{% if felt.ukorrigerede_fejl %}Bilag: Oversigt over ikke-korrigerede fejlinformationer.

{% endif %}Med venlig hilsen

**{{ kunde.navn }}**

{% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %}**Direktion**

______________________________

**Bestyrelse**

______________________________ (formand)

______________________________

______________________________
{% else %}**Direktion**

______________________________

______________________________
{% endif %}
