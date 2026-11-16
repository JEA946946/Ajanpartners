---
{
  "title": "Erklæring om udvidet gennemgang (klasse B)",
  "description": "Den uafhængige revisors erklæring om udvidet gennemgang af årsregnskab efter Erhvervsstyrelsens erklæringsstandard for små virksomheder og FSR – danske revisorers standard om udvidet gennemgang. Mulighed for modificeret konklusion, fremhævelse og supplerende oplysninger.",
  "kind": "erklaering",
  "references": ["Årsregnskabsloven § 135, stk. 1, 2. pkt.", "Erhvervsstyrelsens erklæringsstandard for små virksomheder (udvidet gennemgang)", "FSR – danske revisorers standard om udvidet gennemgang af regnskaber, der udarbejdes efter årsregnskabsloven", "Erklæringsbekendtgørelsen §§ 5-7", "Revisorloven § 18, stk. 1, 2. pkt."],
  "legal_forms": ["aps", "as", "ivs", "holding", "pmv", "andet"],
  "industry_aware": false,
  "fields": [
    {"name": "konklusion", "label": "Konklusion", "type": "select", "options": ["Uden modifikation", "Med forbehold", "Afkræftende konklusion", "Manglende konklusion"], "default": "Uden modifikation"},
    {"name": "modifikation_beskrivelse", "label": "Grundlag for modificeret konklusion (beskrivelse af forholdet og virkningen)", "type": "textarea"},
    {"name": "fortsat_drift", "label": "Væsentlig usikkerhed vedrørende fortsat drift", "type": "checkbox", "default": false},
    {"name": "fortsat_drift_tekst", "label": "Fortsat drift: henvisning til note og kort beskrivelse", "type": "textarea"},
    {"name": "fremhaevelse", "label": "Fremhævelse af forhold i regnskabet (tekst, valgfrit)", "type": "textarea"},
    {"name": "ledelsesberetning", "label": "Årsrapporten indeholder en ledelsesberetning", "type": "checkbox", "default": true},
    {"name": "supplerende_oplysninger", "label": "Supplerende oplysninger efter erklæringsbekendtgørelsen § 7, stk. 2 (valgfrit)", "type": "textarea"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "registreret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Den uafhængige revisors erklæring om udvidet gennemgang

Til {{ kunde.kapitalejere }} i {{ kunde.navn }}

{% if felt.konklusion == "Manglende konklusion" %}## Manglende konklusion

Vi har fået til opgave at udføre udvidet gennemgang af årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}, der omfatter resultatopgørelse, balance, egenkapitalopgørelse og noter, herunder anvendt regnskabspraksis. Årsregnskabet udarbejdes efter årsregnskabsloven.

Vi udtrykker ikke en konklusion om årsregnskabet. På grund af betydningen af det forhold, der er beskrevet i afsnittet „Grundlag for manglende konklusion“, har vi ikke været i stand til at opnå tilstrækkeligt og egnet bevis til at danne grundlag for en konklusion om årsregnskabet.

## Grundlag for manglende konklusion

{{ felt.modifikation_beskrivelse }}

{% else %}## {% if felt.konklusion == "Med forbehold" %}Konklusion med forbehold{% elif felt.konklusion == "Afkræftende konklusion" %}Afkræftende konklusion{% else %}Konklusion{% endif %}

Vi har udført udvidet gennemgang af årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}, der omfatter resultatopgørelse, balance, egenkapitalopgørelse og noter, herunder anvendt regnskabspraksis. Årsregnskabet udarbejdes efter årsregnskabsloven.

{% if felt.konklusion == "Med forbehold" %}Baseret på det udførte arbejde er det vores opfattelse, at årsregnskabet, bortset fra indvirkningen af det forhold, der er beskrevet i afsnittet „Grundlag for konklusion med forbehold“, giver et retvisende billede af selskabets aktiver, passiver og finansielle stilling pr. {{ regnskab.slut }} samt af resultatet af selskabets aktiviteter for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} i overensstemmelse med årsregnskabsloven.{% elif felt.konklusion == "Afkræftende konklusion" %}Baseret på det udførte arbejde er det vores opfattelse, at årsregnskabet på grund af betydningen af det forhold, der er beskrevet i afsnittet „Grundlag for afkræftende konklusion“, ikke giver et retvisende billede af selskabets aktiver, passiver og finansielle stilling pr. {{ regnskab.slut }} eller af resultatet af selskabets aktiviteter for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} i overensstemmelse med årsregnskabsloven.{% else %}Baseret på det udførte arbejde er det vores opfattelse, at årsregnskabet giver et retvisende billede af selskabets aktiver, passiver og finansielle stilling pr. {{ regnskab.slut }} samt af resultatet af selskabets aktiviteter for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} i overensstemmelse med årsregnskabsloven.{% endif %}

## {% if felt.konklusion == "Med forbehold" %}Grundlag for konklusion med forbehold{% elif felt.konklusion == "Afkræftende konklusion" %}Grundlag for afkræftende konklusion{% else %}Grundlag for konklusion{% endif %}

{% if felt.konklusion != "Uden modifikation" %}{{ felt.modifikation_beskrivelse }}

{% endif %}Vi har udført vores udvidede gennemgang i overensstemmelse med Erhvervsstyrelsens erklæringsstandard for små virksomheder og FSR – danske revisorers standard om udvidet gennemgang af regnskaber, der udarbejdes efter årsregnskabsloven. Vores ansvar ifølge disse standarder og krav er nærmere beskrevet i afsnittet „Revisors ansvar for den udvidede gennemgang af årsregnskabet“. Vi er uafhængige af selskabet i overensstemmelse med International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code) og de yderligere etiske krav, der er gældende i Danmark, ligesom vi har opfyldt vores øvrige etiske forpligtelser i henhold til disse krav og IESBA Code. Det er vores opfattelse, at det opnåede bevis er tilstrækkeligt og egnet som grundlag for vores {% if felt.konklusion == "Med forbehold" %}konklusion med forbehold{% elif felt.konklusion == "Afkræftende konklusion" %}afkræftende konklusion{% else %}konklusion{% endif %}.

{% endif %}{% if felt.fortsat_drift %}## Væsentlig usikkerhed vedrørende fortsat drift

{{ felt.fortsat_drift_tekst }} Disse begivenheder eller forhold indikerer, at der er en væsentlig usikkerhed, som kan rejse betydelig tvivl om selskabets evne til at fortsætte driften. Vores konklusion er ikke modificeret som følge af dette forhold.

{% endif %}{% if felt.fremhaevelse %}## Fremhævelse af forhold i regnskabet

{{ felt.fremhaevelse }} Vores konklusion er ikke modificeret som følge af dette forhold.

{% endif %}## Ledelsens ansvar for årsregnskabet

Ledelsen har ansvaret for udarbejdelsen af et årsregnskab, der giver et retvisende billede i overensstemmelse med årsregnskabsloven. Ledelsen har endvidere ansvaret for den interne kontrol, som ledelsen anser for nødvendig for at udarbejde et årsregnskab uden væsentlig fejlinformation, uanset om denne skyldes besvigelser eller fejl.

Ved udarbejdelsen af årsregnskabet er ledelsen ansvarlig for at vurdere selskabets evne til at fortsætte driften, at oplyse om forhold vedrørende fortsat drift, hvor dette er relevant, samt at udarbejde årsregnskabet på grundlag af regnskabsprincippet om fortsat drift, medmindre ledelsen enten har til hensigt at likvidere selskabet, indstille driften eller ikke har andet realistisk alternativ end at gøre dette.

## Revisors ansvar for den udvidede gennemgang af årsregnskabet

{% if felt.konklusion == "Manglende konklusion" %}Vores ansvar er at udføre en udvidet gennemgang af årsregnskabet i overensstemmelse med Erhvervsstyrelsens erklæringsstandard for små virksomheder og FSR – danske revisorers standard om udvidet gennemgang og at afgive en erklæring. På grund af det forhold, der er beskrevet i afsnittet „Grundlag for manglende konklusion“, har vi imidlertid ikke været i stand til at opnå tilstrækkeligt og egnet bevis til at danne grundlag for en konklusion. Vi er uafhængige af selskabet i overensstemmelse med IESBA Code og de yderligere etiske krav, der er gældende i Danmark, ligesom vi har opfyldt vores øvrige etiske forpligtelser i henhold til disse krav.{% else %}Vores ansvar er at udtrykke en konklusion om årsregnskabet. Det kræver, at vi planlægger og udfører handlinger med henblik på at opnå begrænset sikkerhed for vores konklusion om årsregnskabet og herudover udfører de specifikt krævede supplerende handlinger med henblik på at opnå yderligere sikkerhed for konklusionen.

En udvidet gennemgang omfatter handlinger, der primært består af forespørgsler til ledelsen og, hvor det er hensigtsmæssigt, andre i virksomheden, analytiske handlinger og de specifikt krævede supplerende handlinger samt vurdering af det opnåede bevis.

Omfanget af de handlinger, der udføres ved en udvidet gennemgang, er mindre end ved en revision, og vi udtrykker derfor ikke en revisionskonklusion om årsregnskabet.{% endif %}

{% if felt.ledelsesberetning %}## Udtalelse om ledelsesberetningen

Ledelsen er ansvarlig for ledelsesberetningen.

{% if felt.konklusion == "Manglende konklusion" %}Da vi ikke udtrykker en konklusion om årsregnskabet, har vi ikke haft grundlag for at overveje, om ledelsesberetningen er væsentligt inkonsistent med årsregnskabet, og vi udtaler os derfor ikke om ledelsesberetningen.{% else %}Vores konklusion om årsregnskabet omfatter ikke ledelsesberetningen, og vi udtrykker ingen form for konklusion med sikkerhed om ledelsesberetningen.

I tilknytning til vores udvidede gennemgang af årsregnskabet er det vores ansvar at læse ledelsesberetningen og i den forbindelse overveje, om ledelsesberetningen er væsentligt inkonsistent med årsregnskabet eller vores viden opnået ved den udvidede gennemgang eller på anden måde synes at indeholde væsentlig fejlinformation.

Vores ansvar er derudover at overveje, om ledelsesberetningen indeholder krævede oplysninger i henhold til årsregnskabsloven.

{% if felt.konklusion == "Uden modifikation" %}Baseret på det udførte arbejde er det vores opfattelse, at ledelsesberetningen er i overensstemmelse med årsregnskabet og er udarbejdet i overensstemmelse med årsregnskabslovens krav. Vi har ikke fundet væsentlig fejlinformation i ledelsesberetningen.{% else %}Som beskrevet i grundlaget for vores modificerede konklusion indeholder årsregnskabet efter vores opfattelse væsentlig fejlinformation. Ledelsesberetningen indeholder af samme årsag væsentlig fejlinformation for så vidt angår de beløb og omtaler, der påvirkes af forholdet. Bortset herfra er ledelsesberetningen udarbejdet i overensstemmelse med årsregnskabslovens krav.{% endif %}{% endif %}

{% endif %}{% if felt.supplerende_oplysninger %}## Erklæring i henhold til anden lovgivning og øvrig regulering

{{ felt.supplerende_oplysninger }}

{% endif %}{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
