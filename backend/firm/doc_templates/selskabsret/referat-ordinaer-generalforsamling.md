---
{
  "title": "Referat af ordinær generalforsamling",
  "description": "Forhandlingsprotokol for ordinær generalforsamling i ApS og A/S: årsrapport, resultatdisponering, decharge, valg til bestyrelse, revisor eller fravalg af revision. Opfylder Erhvervsstyrelsens krav ved anmeldelse.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 76-107", "Selskabsloven § 101", "Selskabsloven §§ 179-182", "Årsregnskabsloven §§ 135, 135 a og 138", "Revisorloven § 16"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "gf_dato", "label": "Dato for generalforsamlingen", "type": "date"},
    {"name": "gf_tid", "label": "Tidspunkt", "type": "text", "default": "kl. 10.00"},
    {"name": "gf_sted", "label": "Sted", "type": "text", "default": "selskabets adresse, {{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }}"},
    {"name": "dirigent", "label": "Dirigent", "type": "text"},
    {"name": "fremmoedte", "label": "Fremmødte kapitalejere (navn, nominel kapital, stemmer, evt. fuldmægtig)", "type": "textarea"},
    {"name": "repraesenteret_pct", "label": "Repræsenteret kapital (%)", "type": "number", "default": "100"},
    {"name": "uden_indkaldelse", "label": "Alle kapitalejere er mødt og har givet afkald på formkrav til indkaldelse", "type": "checkbox", "default": true},
    {"name": "beretning", "label": "Kort referat af ledelsens beretning", "type": "textarea", "default": "Ledelsen redegjorde for selskabets virksomhed i regnskabsåret, herunder for udviklingen i aktiviteter og økonomiske forhold, som beskrevet i årsrapportens ledelsesberetning."},
    {"name": "resultat", "label": "Årets resultat (kr.)", "type": "text", "default": "{{ regnskab.resultat }}"},
    {"name": "resultatdisponering", "label": "Vedtaget resultatdisponering", "type": "textarea", "default": "Årets resultat overføres til overført resultat under egenkapitalen."},
    {"name": "udbytte_beloeb", "label": "Vedtaget udbytte (kr., tom hvis intet)", "type": "number"},
    {"name": "udbytte_betaling", "label": "Udbetalingsdato for udbytte", "type": "date"},
    {"name": "decharge", "label": "Decharge behandlet", "type": "checkbox", "default": true},
    {"name": "bestyrelse_valgt", "label": "Valgte bestyrelsesmedlemmer (tom hvis ingen bestyrelse/ingen ændring)", "type": "textarea"},
    {"name": "revisionsvalg", "label": "Revision", "type": "select", "options": ["Genvalg af revisor", "Valg af ny revisor", "Fravalg af revision", "Revision er fravalgt (ingen ændring)", "Udvidet gennemgang (erklæringsstandard for små virksomheder)"], "default": "Genvalg af revisor"},
    {"name": "revisor_navn", "label": "Valgt revisor/revisionsfirma (inkl. CVR)", "type": "text", "default": "{{ firma.navn }}, CVR-nr. {{ firma.cvr }}"},
    {"name": "vedtaegtsaendring", "label": "Vedtagne vedtægtsændringer (fuld ordlyd)", "type": "textarea"},
    {"name": "eventuelt", "label": "Eventuelt", "type": "textarea", "default": "Intet at referere."},
    {"name": "anmelder", "label": "Hvem anmelder til Erhvervsstyrelsen", "type": "text", "default": "{{ firma.navn }}"}
  ]
}
---
# Referat af ordinær generalforsamling

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}

Den {{ felt.gf_dato }} {{ felt.gf_tid }} afholdtes ordinær generalforsamling i {{ kunde.navn }} på {{ felt.gf_sted }}.

**Fremmødte:**
{{ felt.fremmoedte }}

Repræsenteret var {{ felt.repraesenteret_pct }} % af selskabskapitalen og stemmerne.

Dagsordenen var:

1. Valg af dirigent
2. Ledelsens beretning
3. Godkendelse af årsrapport for {{ regnskab.aar }}
4. Anvendelse af overskud eller dækning af underskud
{% if felt.decharge %}5. Decharge til {{ kunde.ledelsesorgan }}
{% endif %}{% if kunde.selskabsform_kode == "as" or felt.bestyrelse_valgt %}6. Valg af bestyrelse
{% endif %}7. {% if felt.revisionsvalg == "Fravalg af revision" %}Fravalg af revision{% elif felt.revisionsvalg == "Revision er fravalgt (ingen ændring)" %}Revision (fortsat fravalg){% else %}Valg af revisor{% endif %}
{% if felt.vedtaegtsaendring %}8. Vedtægtsændringer
{% endif %}9. Eventuelt

## Valg af dirigent
{{ felt.dirigent }} blev valgt som dirigent og accepterede valget.

{% if felt.uden_indkaldelse %}Dirigenten konstaterede, at samtlige kapitalejere var til stede eller repræsenteret, og at de enstemmigt havde givet afkald på de formelle krav til indkaldelse og varsel, jf. selskabslovens § 76, stk. 2. Generalforsamlingen var herefter lovlig og beslutningsdygtig i henhold til dagsordenen.{% else %}Dirigenten konstaterede, at generalforsamlingen var lovligt indkaldt i overensstemmelse med vedtægterne og selskabslovens § 94, og at den var beslutningsdygtig i henhold til dagsordenen.{% endif %}

## Ledelsens beretning
{{ felt.beretning }}

Beretningen blev taget til efterretning.

## Godkendelse af årsrapport
Årsrapporten for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} blev fremlagt. Årsrapporten udviser et resultat på {{ felt.resultat }} kr., en balancesum på {{ regnskab.balancesum }} kr. og en egenkapital på {{ regnskab.egenkapital }} kr.
{% if felt.revisionsvalg == "Revision er fravalgt (ingen ændring)" %}
Årsrapporten er ikke revideret, idet selskabet har fravalgt revision efter årsregnskabslovens § 135, stk. 1.
{% elif felt.revisionsvalg == "Fravalg af revision" %}
Årsrapporten for {{ regnskab.aar }} er forsynet med erklæring fra selskabets revisor. Fravalget af revision (nedenfor) har først virkning for kommende regnskabsår.
{% else %}
Årsrapporten er forsynet med erklæring fra selskabets revisor.
{% endif %}
Årsrapporten blev enstemmigt godkendt.

## Anvendelse af overskud eller dækning af underskud
Generalforsamlingen godkendte følgende resultatdisponering: {{ felt.resultatdisponering }}
{% if felt.udbytte_beloeb %}
Det blev vedtaget at udlodde ordinært udbytte på {{ felt.udbytte_beloeb }} kr. Ledelsen oplyste, at udlodningen efter ledelsens vurdering er forsvarlig under hensyn til selskabets økonomiske stilling og ikke overstiger de frie reserver, jf. selskabslovens §§ 179 og 180. Generalforsamlingen kan ikke vedtage et højere udbytte end foreslået eller tiltrådt af ledelsen, jf. § 180, stk. 1.

Udbyttet udbetales {{ felt.udbytte_betaling }} med fradrag af udbytteskat. Udbytteskatten angives og betales senest den 10. i måneden efter den måned, hvor udbyttet er vedtaget (i januar den 17.); har selskabet A-skattefrist den sidste bankdag, er fristen den sidste bankdag i måneden efter, jf. kildeskattelovens §§ 65 og 66 og skat.dk.
{% endif %}
{% if felt.decharge %}
## Decharge
Generalforsamlingen meddelte {{ kunde.ledelsesorgan }} decharge for regnskabsåret. Det bemærkes, at decharge ikke afskærer søgsmål vedrørende forhold, hvorom generalforsamlingen ikke fik i alt væsentligt rigtige og fuldstændige oplysninger, jf. selskabslovens § 364, stk. 2.
{% endif %}
{% if kunde.selskabsform_kode == "as" or felt.bestyrelse_valgt %}
## Valg af bestyrelse
Følgende blev valgt til bestyrelsen: {{ felt.bestyrelse_valgt }}
{% if kunde.selskabsform_kode == "as" %}Bestyrelsen består herefter af mindst 3 medlemmer, jf. selskabslovens § 111, stk. 2. Bestyrelsen konstituerer sig selv med formand og eventuel næstformand.{% endif %}
{% endif %}

## {% if felt.revisionsvalg == "Fravalg af revision" %}Fravalg af revision{% elif felt.revisionsvalg == "Revision er fravalgt (ingen ændring)" %}Revision{% else %}Valg af revisor{% endif %}
{% if felt.revisionsvalg == "Fravalg af revision" %}
Dirigenten oplyste, at selskabet i de to seneste på hinanden følgende regnskabsår på balancedagen ikke har overskredet to af følgende tre grænser: balancesum 4 mio. kr., nettoomsætning 8 mio. kr. og et gennemsnitligt antal heltidsbeskæftigede på 12, jf. årsregnskabslovens § 135, stk. 1, 3. pkt., at balancesummen ikke i 2 på hinanden følgende år har oversteget 50 mio. kr. (stk. 2), at holdingreglen i stk. 4 er opfyldt, og at selskabet ikke er udelukket efter § 135 a (bødeforelæg/dom, konkurskarantæne, Erhvervsstyrelsens påbud). Er selskabet i en klassificeret risikobranche med en nettoomsætning over 5 mio. kr. i 2 på hinanden følgende år, skal årsregnskabet fortsat forsynes med en opstillingserklæring eller en erklæring med sikkerhed, jf. § 135, stk. 5.

Generalforsamlingen besluttede enstemmigt, at selskabets årsregnskab fremover ikke skal revideres. Fravalget har virkning fra og med regnskabsåret efter {{ regnskab.aar }}. Den hidtidige revisor fratræder. Fravalget af revisor anmeldes til Erhvervsstyrelsen senest 2 uger efter beslutningen.

Ledelsen sikrer, at det i ledelsespåtegningen i årsrapporten for {{ regnskab.aar }} oplyses, at revision fravælges for kommende regnskabsår, og at det i den første ureviderede årsrapport erklæres, at betingelserne for fravalg er opfyldt.
{% elif felt.revisionsvalg == "Revision er fravalgt (ingen ændring)" %}
Dirigenten oplyste, at selskabet fortsat opfylder betingelserne for fravalg af revision efter årsregnskabslovens § 135, stk. 1. Generalforsamlingen tog dette til efterretning, og der blev ikke valgt revisor.
{% elif felt.revisionsvalg == "Udvidet gennemgang (erklæringsstandard for små virksomheder)" %}
{{ felt.revisor_navn }} blev valgt som selskabets revisor. Generalforsamlingen tog til efterretning, at revisionen udføres som udvidet gennemgang efter Erhvervsstyrelsens erklæringsstandard for små virksomheder, jf. årsregnskabslovens § 135, stk. 1, 2. pkt.
{% else %}
{{ felt.revisor_navn }} blev {% if felt.revisionsvalg == "Genvalg af revisor" %}genvalgt{% else %}valgt{% endif %} som selskabets revisor.
{% endif %}
{% if felt.vedtaegtsaendring %}
## Vedtægtsændringer
Generalforsamlingen vedtog følgende ændringer af vedtægterne med den fornødne majoritet efter selskabslovens § 106 (mindst 2/3 af såvel de afgivne stemmer som den repræsenterede kapital):

{{ felt.vedtaegtsaendring }}

De opdaterede vedtægter vedlægges anmeldelsen til Erhvervsstyrelsen.
{% endif %}

## Eventuelt
{{ felt.eventuelt }}

Da der ikke forelå yderligere, hævede dirigenten generalforsamlingen.

Dirigenten bemyndigede {{ felt.anmelder }} til at anmelde de vedtagne beslutninger til Erhvervsstyrelsen og til at foretage de ændringer i dokumenterne, som Erhvervsstyrelsen måtte kræve som betingelse for registrering.

## Opfølgning (udfyldes af selskabet/rådgiver)
- [ ] Årsrapporten indberettes til Erhvervsstyrelsen senest {{ regnskab.frist_aarsrapport }} (ÅRL § 138).
- [ ] Ændringer (revisor, bestyrelse, vedtægter) anmeldes senest 2 uger efter generalforsamlingen (selskabslovens § 9).
- [ ] Forhandlingsprotokollen gøres tilgængelig for kapitalejerne senest 2 uger efter generalforsamlingen (selskabslovens § 101, stk. 4).
{% if felt.udbytte_beloeb %}- [ ] Udbytteskat angives og indbetales i TastSelv Erhverv, og udbyttemodtagerne indberettes.
{% endif %}- [ ] Register over reelle ejere og ejerbog gennemgås (årlig undersøgelse, selskabslovens § 58 a).

{{ kunde.by }}, {{ felt.gf_dato }}

Som dirigent:

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.dirigent }}
