---
{
  "title": "Opdragsbrev – aftalte arbejdshandlinger (ISRS 4400)",
  "description": "Opdragsbrev for erklæring om aftalte arbejdshandlinger efter ISRS 4400 (revideret), fx til tilskudsgiver, franchisegiver, bank eller udlejer (omsætningsopgørelse).",
  "kind": "brev",
  "references": ["ISRS 4400 (revideret)", "Erklæringsbekendtgørelsen", "Revisorloven §§ 16 og 24", "FSR – danske revisorers Etiske regler for revisorer", "Hvidvaskloven"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "revisor_titel", "label": "Underskrivende revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "emne", "label": "Emnet for handlingerne (fx omsætningsopgørelse, tilskudsregnskab)", "type": "text"},
    {"name": "periode", "label": "Periode/dato som oplysningerne vedrører", "type": "text", "default": "{{ regnskab.start }} – {{ regnskab.slut }}"},
    {"name": "formaal", "label": "Formålet med opgaven", "type": "textarea"},
    {"name": "bestiller", "label": "Bestiller (hvis andre end kunden)", "type": "text"},
    {"name": "brugere", "label": "Tiltænkte brugere af erklæringen", "type": "text"},
    {"name": "handlinger", "label": "Aftalte handlinger (én pr. linje, nummereret)", "type": "textarea"},
    {"name": "uafhaengighed", "label": "Uafhængighed", "type": "select", "options": ["Vi er uafhængige af virksomheden i overensstemmelse med revisorlovens og de etiske reglers krav", "Der er ikke krav om uafhængighed, og vi har ikke vurderet vores uafhængighed"], "default": "Vi er uafhængige af virksomheden i overensstemmelse med revisorlovens og de etiske reglers krav"},
    {"name": "vaesentlighed", "label": "Eventuel aftalt beløbsgrænse for afvigelser", "type": "text"},
    {"name": "frist", "label": "Frist for erklæring", "type": "date"},
    {"name": "honorar", "label": "Honorar (kr. ekskl. moms)", "type": "number"},
    {"name": "timepris", "label": "Timepris for ekstraarbejde (kr. ekskl. moms)", "type": "number"},
    {"name": "ansvarsbegraensning", "label": "Ansvarsbegrænsning", "type": "text", "default": "et beløb svarende til tre gange honoraret for opgaven"}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Opdragsbrev – erklæring om aftalte arbejdshandlinger vedrørende {{ felt.emne }}

Med dette brev bekræfter vi vilkårene for vores udførelse af aftalte arbejdshandlinger vedrørende {{ felt.emne }} for {{ felt.periode }}.

## 1. Formål og brugere

Formålet med opgaven er: {{ felt.formaal }}

{% if felt.bestiller %}Opgaven er bestilt af {{ felt.bestiller }} i samarbejde med {{ kunde.navn }}.{% endif %} Erklæringen er udelukkende til brug for {{ felt.brugere }} og må ikke anvendes til andre formål eller udleveres til andre uden vores skriftlige samtykke.

## 2. Opgavens karakter

Vi udfører opgaven efter ISRS 4400 (revideret), Opgaver om aftalte arbejdshandlinger. Ved en sådan opgave udfører vi de handlinger, der er aftalt med jer{% if felt.bestiller %} og {{ felt.bestiller }}{% endif %}, og rapporterer de faktiske resultater. Vi udtrykker **ingen konklusion og ingen sikkerhed**. Det er brugerne af erklæringen, der selv vurderer de rapporterede resultater og drager konklusioner.

Handlingerne er hverken revision eller review. Havde vi udført yderligere handlinger, kunne andre forhold være kommet til vores kendskab, som ville være blevet rapporteret.

Vi overholder de etiske krav i FSR – danske revisorers Etiske regler for revisorer. Om uafhængighed gælder: {{ felt.uafhaengighed }}. Dette oplyses i erklæringen.

## 3. Aftalte handlinger

Vi udfører følgende handlinger. I bekræfter med jeres underskrift, at handlingerne er passende i forhold til opgavens formål:

{{ felt.handlinger }}

{% if felt.vaesentlighed %}Afvigelser under {{ felt.vaesentlighed }} rapporteres ikke, medmindre de er af kvalitativ betydning.{% endif %}

Handlingerne er beskrevet præcist, så de faktiske resultater kan rapporteres objektivt uden faglig vurdering. Ønskes handlingerne ændret, sker det skriftligt, før erklæringen afgives.

## 4. Ansvar

{{ kunde.ledelsesorgan }} har ansvaret for det emne, handlingerne udføres på, for de oplysninger og dokumenter, vi modtager, og for at give os adgang til de personer og oplysninger, vi har brug for. Bestiller og brugere har ansvaret for, at de aftalte handlinger er tilstrækkelige til deres formål.

## 5. Rapportering

Vi afgiver en skriftlig erklæring om aftalte arbejdshandlinger med en beskrivelse af formål, brugere, de udførte handlinger og de faktiske resultater, herunder eventuelle undtagelser. Vi forventer at afgive erklæringen senest {{ felt.frist }}, forudsat at materialet foreligger rettidigt.

## 6. Hvidvask, honorar og øvrige vilkår

Vi er omfattet af hvidvaskloven og indhenter derfor legitimation og oplysninger om ejere, reelle ejere og ledelse.

Honoraret udgør {{ felt.honorar }} kr. ekskl. moms. Ændringer i handlingerne eller ekstraarbejde afregnes med {{ felt.timepris }} kr. pr. time ekskl. moms.

Vores ansvar er begrænset til {{ felt.ansvarsbegraensning }}. Begrænsningen gælder ikke ved forsæt eller grov uagtsomhed. Vi har intet ansvar over for andre end de i erklæringen angivne brugere. Opgaven udføres i øvrigt efter vores almindelige forretningsbetingelser.

Vi beder jer bekræfte opdragsbrevet og de aftalte handlinger ved at underskrive og returnere en kopi.

Med venlig hilsen

{{ firma.navn }}

&nbsp;

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}

&nbsp;

**Accepteret på vegne af {{ kunde.navn }}**

Dato: ________________

______________________________
{{ kunde.ledelsesorgan }}
{% if felt.bestiller %}

**Accepteret på vegne af {{ felt.bestiller }}**

Dato: ________________

______________________________
{% endif %}
