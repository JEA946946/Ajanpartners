---
{
  "title": "Reviewerklæring på årsregnskab (ISRE 2400)",
  "description": "Den uafhængige revisors erklæring om review af årsregnskab efter ISRE 2400. Anvendes typisk, hvor revisionen er fravalgt (ÅRL § 135, stk. 1, 3. pkt.), og ledelsen ønsker en erklæring med begrænset sikkerhed. Konklusion i negativ form.",
  "kind": "erklaering",
  "references": ["ISRE 2400 (Revideret), afsnit 86-92", "Erklæringsbekendtgørelsen (BEK nr. 518 af 24/05/2024) §§ 13-16", "Årsregnskabsloven § 135", "Revisorloven § 16 (LBK nr. 206 af 20/02/2025)"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "konklusion", "label": "Konklusion", "type": "select", "options": ["Uden modifikation", "Med forbehold", "Afkræftende konklusion"], "default": "Uden modifikation"},
    {"name": "modifikation_beskrivelse", "label": "Grundlag for modificeret konklusion", "type": "textarea"},
    {"name": "fremhaevelse", "label": "Fremhævelse af forhold, fx fortsat drift (valgfrit)", "type": "textarea"},
    {"name": "ledelsesberetning", "label": "Årsrapporten indeholder en ledelsesberetning", "type": "checkbox", "default": false},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "registreret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Den uafhængige revisors reviewerklæring om årsregnskabet

Til {% if kunde.er_kapitalselskab %}{{ kunde.kapitalejere }}{% else %}ejerne{% endif %} i {{ kunde.navn }}

Vi har udført review af årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}, der omfatter resultatopgørelse, balance{% if kunde.er_kapitalselskab %}, egenkapitalopgørelse{% endif %} og noter, herunder anvendt regnskabspraksis. Årsregnskabet udarbejdes efter årsregnskabsloven.

## Ledelsens ansvar for årsregnskabet

Ledelsen har ansvaret for udarbejdelsen af et årsregnskab, der giver et retvisende billede i overensstemmelse med årsregnskabsloven, og for den interne kontrol, som ledelsen anser for nødvendig for at udarbejde et årsregnskab uden væsentlig fejlinformation, uanset om denne skyldes besvigelser eller fejl.

## Revisors ansvar

Vores ansvar er at udtrykke en konklusion om årsregnskabet. Vi har udført vores review i overensstemmelse med den internationale standard om review af historiske regnskaber, ISRE 2400 (Revideret), og de yderligere krav, der er gældende i Danmark. Standarden kræver, at vi konkluderer, om vi er blevet opmærksomme på forhold, der giver os grund til at mene, at årsregnskabet som helhed ikke i alle væsentlige henseender er udarbejdet i overensstemmelse med den relevante regnskabsmæssige begrebsramme. Standarden kræver også, at vi overholder relevante etiske krav, herunder uafhængighedskrav, jf. revisorloven og International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code).

Et review af årsregnskabet efter ISRE 2400 er en erklæringsopgave med begrænset sikkerhed. Vi udfører handlinger, der primært består af forespørgsler til ledelsen og, hvor det er relevant, andre i virksomheden, samt analytiske handlinger, og vi vurderer det opnåede bevis.

De handlinger, der udføres ved et review, er væsentligt mindre end ved en revision udført efter de internationale standarder om revision. Vi udtrykker derfor ikke en revisionskonklusion om årsregnskabet.

{% if felt.konklusion != "Uden modifikation" %}## {% if felt.konklusion == "Med forbehold" %}Grundlag for konklusion med forbehold{% else %}Grundlag for afkræftende konklusion{% endif %}

{{ felt.modifikation_beskrivelse }}

{% endif %}## {% if felt.konklusion == "Med forbehold" %}Konklusion med forbehold{% elif felt.konklusion == "Afkræftende konklusion" %}Afkræftende konklusion{% else %}Konklusion{% endif %}

{% if felt.konklusion == "Med forbehold" %}Ved vores review er vi, bortset fra indvirkningen af det forhold, der er beskrevet i afsnittet „Grundlag for konklusion med forbehold“, ikke blevet opmærksomme på forhold, der giver os grund til at mene, at årsregnskabet ikke giver et retvisende billede af {% if kunde.er_kapitalselskab %}selskabets{% else %}virksomhedens{% endif %} aktiver, passiver og finansielle stilling pr. {{ regnskab.slut }} samt af resultatet af {% if kunde.er_kapitalselskab %}selskabets{% else %}virksomhedens{% endif %} aktiviteter for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} i overensstemmelse med årsregnskabsloven.{% elif felt.konklusion == "Afkræftende konklusion" %}På grund af betydningen af det forhold, der er beskrevet i afsnittet „Grundlag for afkræftende konklusion“, giver årsregnskabet efter vores opfattelse ikke et retvisende billede af {% if kunde.er_kapitalselskab %}selskabets{% else %}virksomhedens{% endif %} aktiver, passiver og finansielle stilling pr. {{ regnskab.slut }} eller af resultatet af aktiviteterne for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} i overensstemmelse med årsregnskabsloven.{% else %}Ved vores review er vi ikke blevet opmærksomme på forhold, der giver os grund til at mene, at årsregnskabet ikke giver et retvisende billede af {% if kunde.er_kapitalselskab %}selskabets{% else %}virksomhedens{% endif %} aktiver, passiver og finansielle stilling pr. {{ regnskab.slut }} samt af resultatet af {% if kunde.er_kapitalselskab %}selskabets{% else %}virksomhedens{% endif %} aktiviteter for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} i overensstemmelse med årsregnskabsloven.{% endif %}

{% if felt.fremhaevelse %}## Fremhævelse af forhold i regnskabet

{{ felt.fremhaevelse }} Vores konklusion er ikke modificeret som følge af dette forhold.

{% endif %}{% if felt.ledelsesberetning %}## Udtalelse om ledelsesberetningen

Ledelsen er ansvarlig for ledelsesberetningen. Vores konklusion om årsregnskabet omfatter ikke ledelsesberetningen, og vi udtrykker ingen form for konklusion med sikkerhed om ledelsesberetningen. I tilknytning til vores review har vi læst ledelsesberetningen og overvejet, om den er væsentligt inkonsistent med årsregnskabet eller vores viden opnået ved reviewet eller på anden måde synes at indeholde væsentlig fejlinformation, og om den indeholder krævede oplysninger i henhold til årsregnskabsloven.

Baseret på det udførte arbejde er det vores opfattelse, at ledelsesberetningen er i overensstemmelse med årsregnskabet og er udarbejdet i overensstemmelse med årsregnskabslovens krav. Vi har ikke fundet væsentlig fejlinformation i ledelsesberetningen.

{% endif %}{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
