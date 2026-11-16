---
{
  "title": "Referat af ekstraordinær generalforsamling",
  "description": "Forhandlingsprotokol for ekstraordinær generalforsamling (fx ledelsesændring, vedtægtsændring, ekstraordinært udbytte, kapitaltab efter SL § 119). Med majoritetskrav og anmeldelsesfrister.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 76, 89, 94, 101, 105-107", "Selskabsloven § 119", "Selskabsloven § 9"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "gf_dato", "label": "Dato", "type": "date"},
    {"name": "gf_tid", "label": "Tidspunkt", "type": "text", "default": "kl. 10.00"},
    {"name": "gf_sted", "label": "Sted", "type": "text", "default": "selskabets adresse"},
    {"name": "dirigent", "label": "Dirigent", "type": "text"},
    {"name": "fremmoedte", "label": "Fremmødte kapitalejere (navn, kapital, stemmer, fuldmægtig)", "type": "textarea"},
    {"name": "repraesenteret_pct", "label": "Repræsenteret kapital (%)", "type": "number", "default": "100"},
    {"name": "uden_indkaldelse", "label": "Alle kapitalejere til stede og afkald på formkrav", "type": "checkbox", "default": true},
    {"name": "anledning", "label": "Anledning", "type": "select", "options": ["Generelle forslag", "Kapitaltab (SL § 119)"], "default": "Generelle forslag"},
    {"name": "punkt1", "label": "Dagsordenspunkt 1 – overskrift", "type": "text", "default": "Valg af nyt medlem af direktionen/bestyrelsen"},
    {"name": "beslutning1", "label": "Dagsordenspunkt 1 – drøftelse og beslutning", "type": "textarea"},
    {"name": "punkt2", "label": "Dagsordenspunkt 2 – overskrift (valgfri)", "type": "text"},
    {"name": "beslutning2", "label": "Dagsordenspunkt 2 – drøftelse og beslutning", "type": "textarea"},
    {"name": "punkt3", "label": "Dagsordenspunkt 3 – overskrift (valgfri)", "type": "text"},
    {"name": "beslutning3", "label": "Dagsordenspunkt 3 – drøftelse og beslutning", "type": "textarea"},
    {"name": "vedtaegtsaendring", "label": "Indebærer beslutningerne vedtægtsændring", "type": "checkbox"},
    {"name": "egenkapital_konstateret", "label": "Egenkapital ved konstatering af kapitaltab (kr.)", "type": "text", "default": "{{ regnskab.egenkapital }}"},
    {"name": "tiltag", "label": "Foreslåede foranstaltninger ved kapitaltab", "type": "textarea"},
    {"name": "anmelder", "label": "Bemyndiget til anmeldelse", "type": "text", "default": "{{ firma.navn }}"}
  ]
}
---
# Referat af ekstraordinær generalforsamling

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}

Den {{ felt.gf_dato }} {{ felt.gf_tid }} afholdtes ekstraordinær generalforsamling i selskabet på {{ felt.gf_sted }}.

**Fremmødte:**
{{ felt.fremmoedte }}

Repræsenteret var {{ felt.repraesenteret_pct }} % af selskabskapitalen og stemmerne.

## Valg af dirigent
{{ felt.dirigent }} blev valgt som dirigent og konstaterede, at
{% if felt.uden_indkaldelse %}samtlige kapitalejere var til stede eller repræsenteret og enstemmigt havde besluttet at fravige lovens og vedtægternes form- og fristkrav, jf. selskabslovens § 76, stk. 2,{% else %}generalforsamlingen var indkaldt af {{ kunde.ledelsesorgan }} med lovligt varsel (tidligst 4 og senest 2 uger før, medmindre vedtægterne foreskriver længere frist, jf. selskabslovens § 94), og at indkaldelsen indeholdt den fulde ordlyd af eventuelle forslag til vedtægtsændringer,{% endif %} og at generalforsamlingen var lovlig og beslutningsdygtig.

{% if felt.anledning == "Kapitaltab (SL § 119)" %}
## Redegørelse for selskabets økonomiske stilling (selskabslovens § 119)
Generalforsamlingen er afholdt, fordi {{ kunde.ledelsesorgan }} har konstateret, at selskabets egenkapital udgør mindre end halvdelen af den tegnede kapital. Generalforsamlingen skal afholdes senest 6 måneder efter konstateringen.

Egenkapitalen er opgjort til {{ felt.egenkapital_konstateret }} kr. Ledelsen redegjorde for årsagerne til tabet, den forventede udvikling, likviditeten og kapitalberedskabet, jf. selskabslovens §§ 115 og 118.

Ledelsen foreslog følgende foranstaltninger:
{{ felt.tiltag }}

*Mulige foranstaltninger er bl.a. kapitalforhøjelse, kapitalejerindskud/tilskud, konvertering eller efterstillelse (rangordensklausul) af kapitalejerlån, rekonstruktion, salg af aktiviteter eller opløsning. Ledelsen skal løbende vurdere, om driften kan fortsættes forsvarligt; ved insolvens skal ledelsen undgå at påføre kreditorerne yderligere tab.*

Generalforsamlingen tog redegørelsen til efterretning og traf beslutning som anført nedenfor.
{% endif %}

## {{ felt.punkt1 }}
{{ felt.beslutning1 }}
{% if felt.punkt2 %}
## {{ felt.punkt2 }}
{{ felt.beslutning2 }}
{% endif %}{% if felt.punkt3 %}
## {{ felt.punkt3 }}
{{ felt.beslutning3 }}
{% endif %}
{% if felt.vedtaegtsaendring %}
## Majoritet
Beslutningerne om vedtægtsændring blev vedtaget med mindst 2/3 af såvel de afgivne stemmer som den på generalforsamlingen repræsenterede selskabskapital, jf. selskabslovens § 106. Dirigenten konstaterede, at ingen af beslutningerne er omfattet af de skærpede krav i § 107 (enstemmighed ved forøgede forpligtelser; 9/10 ved bl.a. begrænsning af udbytteret eller omsættelighed), eller at disse krav i givet fald var opfyldt. De ændrede vedtægter vedlægges anmeldelsen.
{% endif %}

## Eventuelt
Intet.

Dirigenten hævede herefter generalforsamlingen og bemyndigede {{ felt.anmelder }} til at anmelde beslutningerne til Erhvervsstyrelsen og til at foretage de ændringer, som Erhvervsstyrelsen måtte kræve.

## Opfølgning
- [ ] Anmeldelse til Erhvervsstyrelsen senest 2 uger efter beslutningen (selskabslovens § 9).
- [ ] Protokollen tilgængelig for kapitalejerne senest 2 uger efter generalforsamlingen (§ 101, stk. 4).
- [ ] Ledelsesændringer: ny direktør/bestyrelsesmedlem registreres med MitID; reelle ejere vurderes på ny, hvis direktionen er registreret som reelle ejere.

{{ kunde.by }}, {{ felt.gf_dato }}

Som dirigent:

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.dirigent }}
