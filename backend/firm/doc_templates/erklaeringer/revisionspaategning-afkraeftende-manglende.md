---
{
  "title": "Revisionspåtegning – afkræftende eller manglende konklusion (ISA 705)",
  "description": "Revisionspåtegning på årsregnskab (klasse B), når virkningen af et forhold er både væsentlig og gennemgribende: afkræftende konklusion ved væsentlig fejlinformation, manglende konklusion når tilstrækkeligt revisionsbevis ikke kan opnås. Drøft altid med kvalitetssikringsansvarlig før afgivelse.",
  "kind": "erklaering",
  "references": ["ISA 705 (DK), afsnit 8-10 og 26-28", "ISA 700 (DK)", "ISA 720", "Erklæringsbekendtgørelsen (BEK nr. 518 af 24/05/2024) § 5 og § 6, stk. 1-3 og 5-8", "Revisorloven § 16 (LBK nr. 206 af 20/02/2025)"],
  "legal_forms": ["aps", "as", "ivs", "holding", "pmv", "andet"],
  "industry_aware": false,
  "fields": [
    {"name": "konklusionstype", "label": "Type af konklusion", "type": "select", "options": ["Afkræftende konklusion", "Manglende konklusion"], "default": "Afkræftende konklusion"},
    {"name": "forhold_beskrivelse", "label": "Beskrivelse af forholdet/forholdene (poster, beløb, virkning, hvorfor gennemgribende)", "type": "textarea"},
    {"name": "ledelsesberetning", "label": "Årsrapporten indeholder en ledelsesberetning", "type": "checkbox", "default": true},
    {"name": "supplerende_oplysninger", "label": "Supplerende oplysninger efter erklæringsbekendtgørelsen § 7, stk. 2 (valgfrit)", "type": "textarea"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Påtegningens dato", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Den uafhængige revisors revisionspåtegning

Til {{ kunde.kapitalejere }} i {{ kunde.navn }}

{% if felt.konklusionstype == "Manglende konklusion" %}## Manglende konklusion

Vi har fået til opgave at revidere årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}, der omfatter resultatopgørelse, balance, egenkapitalopgørelse og noter, herunder anvendt regnskabspraksis. Årsregnskabet udarbejdes efter årsregnskabsloven.

Vi udtrykker ikke en konklusion om årsregnskabet. På grund af betydningen af de forhold, der er beskrevet i afsnittet „Grundlag for manglende konklusion“, har vi ikke været i stand til at opnå tilstrækkeligt og egnet revisionsbevis til at danne grundlag for en konklusion om årsregnskabet.

## Grundlag for manglende konklusion

{{ felt.forhold_beskrivelse }}

Vi har ikke kunnet opnå tilstrækkeligt og egnet revisionsbevis for de beskrevne forhold ved alternative revisionshandlinger. De mulige virkninger på årsregnskabet af ikke-opdaget fejlinformation kan være både væsentlige og gennemgribende, og vi har derfor ikke kunnet fastslå, om der er behov for reguleringer af årsregnskabet.

{% else %}## Afkræftende konklusion

Vi har revideret årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}, der omfatter resultatopgørelse, balance, egenkapitalopgørelse og noter, herunder anvendt regnskabspraksis. Årsregnskabet udarbejdes efter årsregnskabsloven.

Det er vores opfattelse, at årsregnskabet på grund af betydningen af det forhold, der er beskrevet i afsnittet „Grundlag for afkræftende konklusion“, ikke giver et retvisende billede af selskabets aktiver, passiver og finansielle stilling pr. {{ regnskab.slut }} eller af resultatet af selskabets aktiviteter for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} i overensstemmelse med årsregnskabsloven.

## Grundlag for afkræftende konklusion

{{ felt.forhold_beskrivelse }}

Efter vores opfattelse er virkningen af forholdet på årsregnskabet både væsentlig og gennemgribende.

Vi har udført vores revision i overensstemmelse med internationale standarder om revision og de yderligere krav, der er gældende i Danmark. Vores ansvar ifølge disse standarder og krav er nærmere beskrevet i afsnittet „Revisors ansvar for revisionen af årsregnskabet“. Vi er uafhængige af selskabet i overensstemmelse med International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code) og de yderligere etiske krav, der er gældende i Danmark, ligesom vi har opfyldt vores øvrige etiske forpligtelser i henhold til disse krav og IESBA Code. Det er vores opfattelse, at det opnåede revisionsbevis er tilstrækkeligt og egnet som grundlag for vores afkræftende konklusion.

{% endif %}## Ledelsens ansvar for årsregnskabet

Ledelsen har ansvaret for udarbejdelsen af et årsregnskab, der giver et retvisende billede i overensstemmelse med årsregnskabsloven. Ledelsen har endvidere ansvaret for den interne kontrol, som ledelsen anser for nødvendig for at udarbejde et årsregnskab uden væsentlig fejlinformation, uanset om denne skyldes besvigelser eller fejl.

Ved udarbejdelsen af årsregnskabet er ledelsen ansvarlig for at vurdere selskabets evne til at fortsætte driften, at oplyse om forhold vedrørende fortsat drift, hvor dette er relevant, samt at udarbejde årsregnskabet på grundlag af regnskabsprincippet om fortsat drift, medmindre ledelsen enten har til hensigt at likvidere selskabet, indstille driften eller ikke har andet realistisk alternativ end at gøre dette.

## Revisors ansvar for revisionen af årsregnskabet

{% if felt.konklusionstype == "Manglende konklusion" %}Vores ansvar er at udføre en revision af årsregnskabet i overensstemmelse med internationale standarder om revision og de yderligere krav, der er gældende i Danmark, og at afgive en revisionspåtegning. På grund af de forhold, der er beskrevet i afsnittet „Grundlag for manglende konklusion“, har vi imidlertid ikke været i stand til at opnå tilstrækkeligt og egnet revisionsbevis til at danne grundlag for en konklusion om årsregnskabet.

Vi er uafhængige af selskabet i overensstemmelse med International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code) og de yderligere etiske krav, der er gældende i Danmark, ligesom vi har opfyldt vores øvrige etiske forpligtelser i henhold til disse krav og IESBA Code.{% else %}Vores mål er at opnå høj grad af sikkerhed for, om årsregnskabet som helhed er uden væsentlig fejlinformation, uanset om denne skyldes besvigelser eller fejl, og at afgive en revisionspåtegning med en konklusion. Høj grad af sikkerhed er et højt niveau af sikkerhed, men er ikke en garanti for, at en revision, der udføres i overensstemmelse med internationale standarder om revision og de yderligere krav, der er gældende i Danmark, altid vil afdække væsentlig fejlinformation, når sådan findes. Fejlinformationer kan opstå som følge af besvigelser eller fejl og kan betragtes som væsentlige, hvis det med rimelighed kan forventes, at de enkeltvis eller samlet har indflydelse på de økonomiske beslutninger, som regnskabsbrugerne træffer på grundlag af årsregnskabet.

Som led i en revision, der udføres i overensstemmelse med internationale standarder om revision og de yderligere krav, der er gældende i Danmark, foretager vi faglige vurderinger og opretholder professionel skepsis under revisionen. Herudover:

- identificerer og vurderer vi risikoen for væsentlig fejlinformation i årsregnskabet, uanset om denne skyldes besvigelser eller fejl, udformer og udfører revisionshandlinger som reaktion på disse risici samt opnår revisionsbevis, der er tilstrækkeligt og egnet til at danne grundlag for vores konklusion. Risikoen for ikke at opdage væsentlig fejlinformation forårsaget af besvigelser er højere end ved væsentlig fejlinformation forårsaget af fejl, idet besvigelser kan omfatte sammensværgelser, dokumentfalsk, bevidste udeladelser, vildledning eller tilsidesættelse af intern kontrol;
- opnår vi forståelse af den interne kontrol med relevans for revisionen for at kunne udforme revisionshandlinger, der er passende efter omstændighederne, men ikke for at kunne udtrykke en konklusion om effektiviteten af selskabets interne kontrol;
- tager vi stilling til, om den regnskabspraksis, som er anvendt af ledelsen, er passende, samt om de regnskabsmæssige skøn og tilknyttede oplysninger, som ledelsen har udarbejdet, er rimelige;
- konkluderer vi, om ledelsens udarbejdelse af årsregnskabet på grundlag af regnskabsprincippet om fortsat drift er passende, samt om der på grundlag af det opnåede revisionsbevis er væsentlig usikkerhed forbundet med begivenheder eller forhold, der kan skabe betydelig tvivl om selskabets evne til at fortsætte driften. Vores konklusioner er baseret på det revisionsbevis, der er opnået frem til datoen for vores revisionspåtegning. Fremtidige begivenheder eller forhold kan dog medføre, at selskabet ikke længere kan fortsætte driften;
- tager vi stilling til den samlede præsentation, struktur og indhold af årsregnskabet, herunder noteoplysningerne, samt om årsregnskabet afspejler de underliggende transaktioner og begivenheder på en sådan måde, at der gives et retvisende billede heraf.

Vi kommunikerer med den øverste ledelse om blandt andet det planlagte omfang og den tidsmæssige placering af revisionen samt betydelige revisionsmæssige observationer, herunder eventuelle betydelige mangler i intern kontrol, som vi identificerer under revisionen.{% endif %}

{% if felt.ledelsesberetning %}## Udtalelse om ledelsesberetningen

Ledelsen er ansvarlig for ledelsesberetningen.

{% if felt.konklusionstype == "Manglende konklusion" %}Da vi ikke udtrykker en konklusion om årsregnskabet, har vi ikke haft et tilstrækkeligt grundlag for at overveje, om ledelsesberetningen er væsentligt inkonsistent med årsregnskabet eller med vores viden opnået ved revisionen. Vi udtaler os derfor ikke om ledelsesberetningen.{% else %}Vores konklusion om årsregnskabet omfatter ikke ledelsesberetningen, og vi udtrykker ingen form for konklusion med sikkerhed om ledelsesberetningen.

I tilknytning til vores revision af årsregnskabet er det vores ansvar at læse ledelsesberetningen og i den forbindelse overveje, om ledelsesberetningen er væsentligt inkonsistent med årsregnskabet eller vores viden opnået ved revisionen eller på anden måde synes at indeholde væsentlig fejlinformation. Vores ansvar er derudover at overveje, om ledelsesberetningen indeholder krævede oplysninger i henhold til årsregnskabsloven.

Som beskrevet i afsnittet „Grundlag for afkræftende konklusion“ giver årsregnskabet efter vores opfattelse ikke et retvisende billede. Ledelsesberetningen indeholder af samme årsag væsentlig fejlinformation for så vidt angår de beløb og omtaler, der påvirkes af forholdet.{% endif %}

{% endif %}{% if felt.supplerende_oplysninger %}## Erklæring i henhold til anden lovgivning og øvrig regulering

{{ felt.supplerende_oplysninger }}

{% endif %}{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
