---
{
  "title": "Erklæring om aftalte arbejdshandlinger – tilskudsregnskab (ISRS 4400)",
  "description": "Erklæring om faktiske resultater efter ISRS 4400 (Revideret) vedrørende et tilskudsregnskab/projektregnskab. Indeholder standardhandlinger (afstemning, stikprøver, løn, moms, egenfinansiering), som tilpasses tilskudsgiverens krav. Ingen konklusion og ingen sikkerhed.",
  "kind": "erklaering",
  "references": ["ISRS 4400 (Revideret) – aftalte arbejdshandlinger", "ISQM 1", "Erklæringsbekendtgørelsen", "FSR – danske revisorers Etiske regler", "Tilskudsgiverens vilkår/revisionsinstruks"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "tilskudsgiver", "label": "Tilskudsgiver/modtager af erklæringen", "type": "text"},
    {"name": "ordning", "label": "Tilskudsordning/projekt og j.nr.", "type": "text"},
    {"name": "periode", "label": "Projektperiode/regnskabsperiode", "type": "text", "default": "{{ regnskab.start }} – {{ regnskab.slut }}"},
    {"name": "tilsagnsbeloeb", "label": "Tilsagnsbeløb (kr.)", "type": "number"},
    {"name": "regnskabsopgoerelse", "label": "Betegnelse og dato for opgørelsen, handlingerne vedrører", "type": "text", "default": "tilskudsregnskabet for perioden, dateret og underskrevet af ledelsen"},
    {"name": "uafhaengighed", "label": "Uafhængighed", "type": "select", "options": ["Vi er uafhængige af virksomheden i overensstemmelse med IESBA Code og de yderligere etiske krav, der er gældende i Danmark.", "Vi er ikke forpligtet til at være uafhængige ved denne opgave og har ikke vurderet vores uafhængighed. De aftalte arbejdshandlinger kunne være udført af en ikke-uafhængig revisor."], "default": "Vi er uafhængige af virksomheden i overensstemmelse med IESBA Code og de yderligere etiske krav, der er gældende i Danmark."},
    {"name": "r1", "label": "Resultat 1 – afstemning til bogføring", "type": "textarea", "default": "Vi har ikke konstateret afvigelser."},
    {"name": "r2", "label": "Resultat 2 – stikprøver på udgifter", "type": "textarea", "default": "Vi har ikke konstateret undtagelser."},
    {"name": "r3", "label": "Resultat 3 – lønomkostninger og timer", "type": "textarea", "default": "Vi har ikke konstateret undtagelser."},
    {"name": "r4", "label": "Resultat 4 – moms", "type": "textarea", "default": "Vi har ikke konstateret undtagelser."},
    {"name": "r5", "label": "Resultat 5 – modtagne tilskud og egenfinansiering", "type": "textarea", "default": "Vi har ikke konstateret afvigelser."},
    {"name": "r6", "label": "Resultat 6 – budgetoverholdelse", "type": "textarea", "default": "Vi har ikke konstateret overskridelser ud over de tilladte."},
    {"name": "ekstra_handlinger", "label": "Yderligere aftalte handlinger og resultater (Markdown-tabelrækker eller tekst)", "type": "textarea"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Den uafhængige revisors erklæring om aftalte arbejdshandlinger vedrørende tilskudsregnskab

Til {{ felt.tilskudsgiver }} og ledelsen i {{ kunde.navn }}

## Formålet med erklæringen og begrænsning i anvendelse og distribution

Vi har udført de arbejdshandlinger, som er aftalt med {{ kunde.navn }} og {{ felt.tilskudsgiver }}, og som er anført nedenfor, vedrørende {{ felt.regnskabsopgoerelse }} for {{ felt.ordning }} for perioden {{ felt.periode }}.

Erklæringen er udelukkende udarbejdet med henblik på at bistå {{ felt.tilskudsgiver }} med at vurdere, om tilskudsregnskabet er udarbejdet i overensstemmelse med vilkårene for tilsagnet{% if felt.tilsagnsbeloeb %} på {{ felt.tilsagnsbeloeb }} kr.{% endif %}, og er muligvis ikke egnet til andre formål. Erklæringen er udelukkende til brug for {{ kunde.navn }} og {{ felt.tilskudsgiver }} og bør ikke udleveres til eller anvendes af andre parter.

## Den ansvarliges ansvar

{{ kunde.navn }} har bekræftet, at de aftalte arbejdshandlinger er passende til opgavens formål. Ledelsen er ansvarlig for tilskudsregnskabet og for, at tilskudsmidlerne er anvendt i overensstemmelse med tilsagnet. Ledelsen er tillige ansvarlig for det emne, som arbejdshandlingerne udføres på.

## Revisors ansvar

Vi har udført opgaven med aftalte arbejdshandlinger i overensstemmelse med ISRS 4400 (Revideret) om opgaver med aftalte arbejdshandlinger og de yderligere krav, der er gældende i Danmark. En opgave med aftalte arbejdshandlinger indebærer, at vi udfører de handlinger, der er aftalt med {{ kunde.navn }} og {{ felt.tilskudsgiver }}, og rapporterer om de faktiske resultater, som er de faktuelle resultater af de udførte handlinger. Vi fremsætter ingen udtalelse om, hvorvidt de aftalte handlinger er passende.

Opgaven er ikke en erklæringsopgave med sikkerhed. Vi udtrykker derfor ikke en konklusion eller anden form for sikkerhed. Havde vi udført yderligere arbejdshandlinger, kunne andre forhold være kommet til vores kendskab, som ville være blevet rapporteret.

## Faglig etik og uafhængighed

Vi har overholdt de etiske krav i revisorloven og FSR – danske revisorers Etiske regler for revisorer, som bygger på International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code). {{ felt.uafhaengighed }}

## Kvalitetsstyring

Revisionsvirksomheden anvender den internationale standard om kvalitetsstyring, ISQM 1, der kræver, at vi designer, implementerer og driver et kvalitetsstyringssystem, herunder politikker og procedurer for overholdelse af etiske krav, faglige standarder og gældende krav i lov og øvrig regulering.

## Arbejdshandlinger og faktiske resultater

Vi har udført nedenstående arbejdshandlinger og rapporterer de faktiske resultater:

| Nr. | Aftalt arbejdshandling | Faktiske resultater |
|---|---|---|
| 1 | Vi har afstemt tilskudsregnskabets udgifter og indtægter til virksomhedens bogføring for perioden. | {{ felt.r1 }} |
| 2 | Vi har for en stikprøve af udgiftsposter i tilskudsregnskabet efterset, at de er dokumenteret ved bilag udstedt til virksomheden, er betalt, vedrører projektperioden og hører under de budgetposter, der er godkendt i tilsagnet. | {{ felt.r2 }} |
| 3 | Vi har for en stikprøve af medarbejdere afstemt de medtagne lønomkostninger til lønsedler og bogføring og efterset, at timeregistreringer er underskrevet af medarbejder og leder, og at timesatsen er beregnet efter tilsagnets regler. | {{ felt.r3 }} |
| 4 | Vi har efterset, at udgifter er medtaget eksklusive moms, i det omfang virksomheden har fradragsret for momsen. | {{ felt.r4 }} |
| 5 | Vi har afstemt modtagne tilskud til kontoudtog og efterset, at egenfinansiering og anden medfinansiering er opgjort og oplyst som krævet i tilsagnet. | {{ felt.r5 }} |
| 6 | Vi har sammenholdt de faktiske udgifter pr. budgetpost med det godkendte budget og beregnet afvigelser. | {{ felt.r6 }} |

{% if felt.ekstra_handlinger %}{{ felt.ekstra_handlinger }}

{% endif %}{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
