---
{
  "title": "Erklæring om opstilling af årsregnskab (ISRS 4410)",
  "description": "Revisors erklæring om opstilling af årsregnskab efter ISRS 4410 (Revideret). Ingen sikkerhed. Til selskaber, der har fravalgt revision, og til personligt ejede virksomheder. Mulighed for at fremhæve særligt regnskabsgrundlag eller kendte fejl. Klasse B-virksomheder i en klassificeret risikobranche med nettoomsætning over 5 mio. kr. i 2 på hinanden følgende år skal have erklæringen fra en uafhængig revisor (ÅRL § 135, stk. 5).",
  "kind": "erklaering",
  "references": ["ISRS 4410 (Revideret), afsnit 40-41", "Revisorloven § 1, stk. 3, og § 16, stk. 4 (LBK nr. 206 af 20/02/2025)", "Årsregnskabsloven § 135, stk. 1, 3. pkt., og stk. 5", "IESBA Code"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "regnskabsgrundlag", "label": "Regnskabsmæssig begrebsramme", "type": "select", "options": ["årsregnskabsloven", "årsregnskabslovens bestemmelser for regnskabsklasse B", "den regnskabspraksis, der er beskrevet i note 1 (skattemæssige værdier)", "den regnskabspraksis, der er beskrevet i note 1"], "default": "årsregnskabsloven"},
    {"name": "formaal_begraenset", "label": "Regnskabet har et særligt formål (fx kun til brug for skatteansættelse eller långiver)", "type": "checkbox", "default": false},
    {"name": "formaal_tekst", "label": "Særligt formål og brugere", "type": "text", "default": "til brug for ejerens og Skattestyrelsens opgørelse af den skattepligtige indkomst"},
    {"name": "fremhaevelse", "label": "Fremhævelse af forhold, ledelsen er gjort bekendt med (valgfrit)", "type": "textarea"},
    {"name": "ikke_uafhaengig", "label": "Revisor er ikke uafhængig af virksomheden (skal oplyses, revisorloven § 16, stk. 4 – ikke muligt ved erklæring efter ÅRL § 135, stk. 5, for risikobrancher)", "type": "checkbox", "default": false},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor", "revisor"], "default": "registreret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr. (kun hvis godkendt revisor)", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Revisors erklæring om opstilling af årsregnskab

Til {% if kunde.er_kapitalselskab %}ledelsen og {{ kunde.kapitalejere }}{% else %}ledelsen og ejerne{% endif %} i {{ kunde.navn }}

Vi har opstillet årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} på grundlag af {% if kunde.er_kapitalselskab %}selskabets{% else %}virksomhedens{% endif %} bogføring og øvrige oplysninger, som ledelsen har tilvejebragt.

Årsregnskabet omfatter resultatopgørelse, balance{% if kunde.er_kapitalselskab %}, egenkapitalopgørelse{% endif %} og noter, herunder anvendt regnskabspraksis.

Vi har udført opgaven i overensstemmelse med ISRS 4410 (Revideret) om opgaver med opstilling af finansielle oplysninger.

{% if felt.ikke_uafhaengig %}Vi skal oplyse, at vi ikke er uafhængige af {% if kunde.er_kapitalselskab %}selskabet{% else %}virksomheden{% endif %}, jf. revisorlovens § 16, stk. 4.

{% endif %}Vi har anvendt vores faglige ekspertise til at bistå ledelsen med udarbejdelsen og præsentationen af årsregnskabet i overensstemmelse med {{ felt.regnskabsgrundlag }}. Vi har overholdt relevante bestemmelser i revisorloven og International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code), herunder principper vedrørende integritet, objektivitet, faglig kompetence og fornøden omhu.

Årsregnskabet og nøjagtigheden og fuldstændigheden af de oplysninger, der er anvendt ved opstillingen heraf, er ledelsens ansvar.

Da en opstillingsopgave ikke er en erklæringsopgave med sikkerhed, er vi ikke forpligtet til at kontrollere nøjagtigheden eller fuldstændigheden af de oplysninger, ledelsen har givet os til brug for opstillingen, eller til at revidere eller gennemgå årsregnskabet. Vi udtrykker derfor ingen revisions- eller reviewkonklusion om, hvorvidt årsregnskabet er udarbejdet i overensstemmelse med {{ felt.regnskabsgrundlag }}.

{% if felt.formaal_begraenset %}Som det fremgår af note 1, er årsregnskabet udarbejdet {{ felt.formaal_tekst }}. Årsregnskabet er derfor muligvis ikke egnet til andre formål.

{% endif %}{% if felt.fremhaevelse %}## Fremhævelse af forhold

{{ felt.fremhaevelse }}

{% endif %}{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}{% if felt.mne_nr %}
MNE-nr. {{ felt.mne_nr }}{% endif %}
