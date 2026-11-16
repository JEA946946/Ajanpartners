---
{
  "title": "Ledelseserklæring – udvidet gennemgang",
  "description": "Skriftlig ledelseserklæring ved udvidet gennemgang af årsregnskab (klasse B). Følger kravene i standarden om udvidet gennemgang (som bygger på ISRE 2400) og dækker de supplerende handlinger: fortsat drift, nærtstående parter, begivenheder efter balancedagen, retssager, besvigelser og lovgivning. Branchespecifikke erklæringer om varelager, igangværende arbejder, investeringsejendomme, kontantsalg og moms.",
  "kind": "brev",
  "references": ["Erhvervsstyrelsens erklæringsstandard for små virksomheder / FSR – danske revisorers standard om udvidet gennemgang", "ISRE 2400 (Revideret), afsnit 61-65", "Selskabsloven §§ 115-118, 127 og 179", "Selskabsloven §§ 210 og 215 (ophævet pr. 1/1 2025 – ældre lån)", "Bogføringsloven"],
  "legal_forms": ["aps", "as", "ivs", "holding", "pmv", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "erklaeringsdato", "label": "Dato (samme som erklæringen om udvidet gennemgang)", "type": "text", "default": "{{ dato.idag }}"},
    {"name": "har_bestyrelse", "label": "Selskabet har en bestyrelse (ApS)", "type": "checkbox", "default": false},
    {"name": "ukorrigerede_fejl", "label": "Der er ukorrigerede fejl (liste vedlægges)", "type": "checkbox", "default": false},
    {"name": "naertstaaende", "label": "Nærtstående parter (navne/selskaber)", "type": "textarea"},
    {"name": "kapitalejerlaan", "label": "Der er ydet lån til kapitalejere/ledelse", "type": "checkbox", "default": false},
    {"name": "yderligere", "label": "Yderligere specifikke erklæringer (valgfrit)", "type": "textarea"}
  ]
}
---
**{{ firma.navn }}**
{{ firma.adresse }}
Att.: {{ medarbejder.navn }}

{{ felt.erklaeringsdato }}

# Ledelseserklæring

Denne erklæring afgives i forbindelse med jeres udvidede gennemgang af årsregnskabet for {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}, for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}. Vi er bekendt med, at den udvidede gennemgang ikke er en revision, og at den primært er baseret på vores oplysninger og forklaringer. Vi bekræfter efter bedste overbevisning følgende:

## Årsregnskabet og oplysningerne

1. Vi har opfyldt vores ansvar for udarbejdelsen af et årsregnskab, der giver et retvisende billede i overensstemmelse med årsregnskabsloven, og for den interne kontrol, vi anser for nødvendig.
2. Vi har givet jer alle relevante oplysninger og adgang til bogføring, bilag, aftaler og referater samt til de personer, I har ønsket at tale med. Alle transaktioner er bogført i overensstemmelse med bogføringsloven.
3. Vores svar på jeres forespørgsler er fyldestgørende og korrekte, og vi har ikke tilbageholdt oplysninger af betydning for årsregnskabet.
4. De væsentlige forudsætninger for regnskabsmæssige skøn er rimelige.
5. Forbindelser og transaktioner med nærtstående parter er oplyst til jer og behandlet korrekt i årsregnskabet.{% if felt.naertstaaende %} Nærtstående parter: {{ felt.naertstaaende }}.{% endif %}
6. Alle begivenheder efter balancedagen, der kræver regulering eller oplysning, er reguleret eller oplyst.
7. Alle retssager, krav, garantier, kautioner, sikkerhedsstillelser og eventualforpligtelser er oplyst til jer og er indregnet eller oplyst i årsregnskabet.
8. {% if felt.ukorrigerede_fejl %}Virkningen af de ikke-korrigerede fejlinformationer i vedlagte oversigt er uvæsentlig, enkeltvis og samlet.{% else %}Der er os bekendt ingen ikke-korrigerede fejlinformationer.{% endif %}
9. Vi har vurderet, at selskabet kan fortsætte driften i mindst 12 måneder fra balancedagen, og vi er ikke bekendt med forhold, der kan skabe betydelig tvivl herom, ud over hvad der er oplyst i årsregnskabet.

## Besvigelser, lovgivning og selskabsretlige forhold

1. Vi er ikke bekendt med besvigelser eller mistanke om besvigelser, der involverer ledelsen, medarbejdere eller andre, og som kan påvirke årsregnskabet.
2. Vi er ikke bekendt med overtrædelser af love og øvrig regulering, herunder skatte-, moms- og afgiftslovgivningen, som kan påvirke årsregnskabet. Moms, A-skat, arbejdsmarkedsbidrag og selskabsskat er angivet og afregnet rettidigt.
3. {% if felt.kapitalejerlaan %}Vi har oplyst jer om alle lån, mellemregninger og sikkerhedsstillelser til kapitalejere, ledelsesmedlemmer og disses nærtstående. Lån og sikkerhedsstillelser, som selskabet har ydet til kapitalejere, ledelsesmedlemmer eller disses nærtstående, er ydet i selskabets interesse og på forsvarlige vilkår, jf. selskabslovens §§ 115-118 og 127, og eventuelle lån ydet før 1. januar 2025 i strid med de dagældende regler i selskabslovens § 210 er tilbagebetalt med renter efter § 215.{% else %}Selskabet har ikke ydet lån eller stillet sikkerhed for kapitalejere, ledelsesmedlemmer eller disses nærtstående.{% endif %}
4. Udlodninger til kapitalejerne er sket i overensstemmelse med selskabslovens regler, og selskabets kapitalberedskab er forsvarligt, jf. selskabslovens § 115.

{% if branche.lager or branche.igangvaerende_arbejder or branche.investeringsejendomme or branche.kontantintensiv or branche.momsfritaget or branche.landbrug %}## Branchespecifikke forhold

{% if branche.lager %}- **Varelager:** Varebeholdningerne er optalt pr. {{ regnskab.slut }}, alle ejede varer er medtaget, og beholdningerne er målt til kostpris, dog højst nettorealisationsværdi, med nedskrivning af ukurante varer.
{% endif %}{% if branche.igangvaerende_arbejder %}- **Igangværende arbejder:** Alle igangværende arbejder er medtaget og målt til salgsværdien af det udførte arbejde efter færdiggørelsesgraden, og forventede tab er indregnet.
{% endif %}{% if branche.investeringsejendomme %}- **Investeringsejendomme:** Dagsværdien er opgjort efter en afkastbaseret model med forudsætninger, der afspejler markedsforholdene på balancedagen, og der er hensat til udskudt skat.
{% endif %}{% if branche.kontantintensiv %}- **Kontantsalg:** Alt salg, også kontantsalg, er registreret løbende og fuldstændigt i kasseapparat/salgssystem, og kasseafstemninger og z-rapporter er opbevaret.
{% endif %}{% if branche.momsfritaget %}- **Moms og lønsumsafgift:** Delvis fradragsret for moms er opgjort og årsreguleret korrekt, og lønsumsafgift er opgjort og afregnet.
{% endif %}{% if branche.landbrug %}- **Landbrug:** Besætninger og afgrøder er optalt og målt efter den oplyste regnskabspraksis, og landbrugsstøtte er indregnet i rette periode med opfyldte betingelser.
{% endif %}
{% endif %}{% if felt.yderligere %}## Øvrige forhold

{{ felt.yderligere }}

{% endif %}Med venlig hilsen

**{{ kunde.navn }}**

{% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %}**Direktion**

______________________________

**Bestyrelse**

______________________________ (formand)

______________________________
{% else %}**Direktion**

______________________________
{% endif %}
