---
{
  "title": "Indkaldelse til ordinær generalforsamling",
  "description": "Indkaldelse med dagsorden for ApS og A/S iht. selskabslovens §§ 88-98. Kan tilpasses fravalg af revision, udbytte og vedtægtsændringer.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 88-98", "Selskabsloven §§ 90, 94 og 96", "Årsregnskabsloven § 138", "Årsregnskabsloven § 135"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "gf_dato", "label": "Dato for generalforsamlingen", "type": "date"},
    {"name": "gf_tid", "label": "Tidspunkt", "type": "text", "default": "kl. 10.00"},
    {"name": "gf_sted", "label": "Sted (adresse eller elektronisk)", "type": "text", "default": "{{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }}"},
    {"name": "elektronisk", "label": "Generalforsamlingen afholdes helt eller delvis elektronisk", "type": "checkbox"},
    {"name": "resultatdisponering", "label": "Bestyrelsens/direktionens forslag til resultatdisponering", "type": "textarea", "default": "Årets resultat overføres til næste år."},
    {"name": "udbytte_beloeb", "label": "Foreslået udbytte (kr., tom hvis intet)", "type": "number"},
    {"name": "revisionsvalg", "label": "Revision", "type": "select", "options": ["Genvalg af revisor", "Valg af ny revisor", "Fravalg af revision", "Revision er fravalgt (ingen ændring)"], "default": "Genvalg af revisor"},
    {"name": "revisor_navn", "label": "Revisor/revisionsfirma der foreslås valgt", "type": "text", "default": "{{ firma.navn }}"},
    {"name": "decharge", "label": "Decharge er på dagsordenen", "type": "checkbox", "default": true},
    {"name": "valg_bestyrelse", "label": "Valg af bestyrelsesmedlemmer (navne)", "type": "textarea"},
    {"name": "vedtaegtsforslag", "label": "Forslag til vedtægtsændringer (fuld ordlyd)", "type": "textarea"},
    {"name": "andre_forslag", "label": "Øvrige forslag", "type": "textarea"},
    {"name": "underskriver", "label": "Underskriver (formand/direktør)", "type": "text"}
  ]
}
---
# Indkaldelse til ordinær generalforsamling

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}

Til {{ kunde.kapitalejere }} i {{ kunde.navn }}

{% if kunde.selskabsform_kode == "as" %}Bestyrelsen{% else %}Ledelsen{% endif %} indkalder hermed til ordinær generalforsamling i selskabet

**{{ felt.gf_dato }} {{ felt.gf_tid }}**
**Sted: {{ felt.gf_sted }}**
{% if felt.elektronisk %}
Generalforsamlingen afholdes {% if kunde.selskabsform_kode == "as" %}delvis{% else %}helt eller delvis{% endif %} elektronisk, jf. selskabslovens § 77. Vejledning om tilmelding, tekniske krav, stemmeafgivning og muligheden for at stille spørgsmål sendes til alle tilmeldte kapitalejere senest 3 dage før generalforsamlingen. Vedtægterne skal indeholde hjemmel til elektronisk generalforsamling, eller alle kapitalejere skal være enige.
{% endif %}

## Dagsorden

1. Valg af dirigent.
2. {% if kunde.selskabsform_kode == "as" %}Bestyrelsens{% else %}Ledelsens{% endif %} beretning om selskabets virksomhed i det forløbne regnskabsår.
3. Fremlæggelse af årsrapport for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} til godkendelse.
4. Beslutning om anvendelse af overskud eller dækning af underskud i henhold til den godkendte årsrapport.{% if felt.udbytte_beloeb %} Det foreslås, at der udloddes udbytte på {{ felt.udbytte_beloeb }} kr.{% endif %}
{% if felt.decharge %}5. Beslutning om meddelelse af decharge til {{ kunde.ledelsesorgan }}.
{% endif %}{% if kunde.selskabsform_kode == "as" %}6. Valg af medlemmer til bestyrelsen.
{% else %}{% if felt.valg_bestyrelse %}6. Valg af medlemmer til bestyrelsen.
{% endif %}{% endif %}7. {% if felt.revisionsvalg == "Fravalg af revision" %}Forslag om fravalg af revision af selskabets årsregnskab fremadrettet, jf. årsregnskabslovens § 135, stk. 1.{% elif felt.revisionsvalg == "Revision er fravalgt (ingen ændring)" %}Revision: Selskabets årsregnskab revideres ikke, jf. årsregnskabslovens § 135, stk. 1. Generalforsamlingen orienteres om, at betingelserne fortsat er opfyldt.{% else %}Valg af revisor.{% endif %}
{% if felt.vedtaegtsforslag %}8. Forslag om ændring af vedtægterne.
{% endif %}{% if felt.andre_forslag %}9. Øvrige forslag fra {% if kunde.selskabsform_kode == "as" %}bestyrelsen{% else %}ledelsen{% endif %} eller kapitalejerne.
{% endif %}10. Eventuelt.


## Fuldstændige forslag

**Resultatdisponering**
{{ felt.resultatdisponering }}
{% if felt.udbytte_beloeb %}
Der foreslås udbytte på {{ felt.udbytte_beloeb }} kr. Udbyttet udbetales efter generalforsamlingen med fradrag af udbytteskat (27 % for personlige kapitalejere hjemmehørende i Danmark), jf. kildeskattelovens § 65. Ledelsen har vurderet, at udlodningen er forsvarlig under hensyn til selskabets økonomiske stilling, jf. selskabslovens § 179, og at den ligger inden for de frie reserver, jf. § 180.
{% endif %}
{% if felt.revisionsvalg == "Fravalg af revision" %}
**Fravalg af revision**
Det foreslås, at selskabets årsregnskab fremover ikke revideres. Selskabet har i de to seneste på hinanden følgende regnskabsår på balancedagen ikke overskredet to af følgende grænser: balancesum 4 mio. kr., nettoomsætning 8 mio. kr. og gennemsnitligt 12 heltidsbeskæftigede, jf. årsregnskabslovens § 135, stk. 1. Vedtages forslaget, fratræder den hidtidige revisor, og eventuelle bestemmelser om revision i vedtægterne foreslås samtidig ophævet (behandles under dagsordenspunktet om vedtægtsændringer).
{% elif felt.revisionsvalg == "Genvalg af revisor" or felt.revisionsvalg == "Valg af ny revisor" %}
**Valg af revisor**
Det foreslås, at {{ felt.revisor_navn }} vælges som selskabets revisor.
{% endif %}
{% if felt.valg_bestyrelse %}
**Valg til bestyrelsen**
Følgende foreslås valgt: {{ felt.valg_bestyrelse }}
{% if kunde.selskabsform_kode == "as" %}Oplysning om de foreslåede kandidaters ledelseshverv i andre erhvervsdrivende virksomheder fremlægges på generalforsamlingen, jf. selskabslovens § 120, stk. 3.{% endif %}
{% endif %}
{% if felt.vedtaegtsforslag %}
**Vedtægtsændringer**
{{ felt.vedtaegtsforslag }}

Vedtagelse kræver, at forslaget tiltrædes af mindst 2/3 af såvel de afgivne stemmer som den del af selskabskapitalen, der er repræsenteret på generalforsamlingen, medmindre vedtægterne eller selskabsloven stiller strengere krav, jf. selskabslovens §§ 106-107.
{% endif %}
{% if felt.andre_forslag %}
**Øvrige forslag**
{{ felt.andre_forslag }}
{% endif %}

## Praktiske oplysninger

- Årsrapporten, dagsordenen og de fuldstændige forslag {% if kunde.selskabsform_kode == "as" %}er gjort tilgængelige for aktionærerne senest 2 uger før generalforsamlingen, jf. selskabslovens § 98, stk. 1{% else %}fremlægges eller fremsendes til anpartshaverne i overensstemmelse med vedtægterne og senest samtidig med indkaldelsen, så anpartshaverne har reelt grundlag for at tage stilling (selskabslovens § 98 gælder kun aktieselskaber, men praksis følges med fordel){% endif %}.
- Enhver kapitalejer har ret til at møde på generalforsamlingen ved fuldmægtig. Fuldmagten skal være skriftlig og dateret, jf. selskabslovens § 80. Kapitalejeren kan møde med en rådgiver.
- Kapitalejere har ret til at stille spørgsmål til ledelsen om forhold af betydning for bedømmelsen af årsrapporten og selskabets stilling i øvrigt, jf. selskabslovens § 102.
- Enhver kapitalejer har ret til at få et bestemt emne optaget på dagsordenen til den ordinære generalforsamling, jf. selskabslovens § 90.{% if kunde.selskabsform_kode == "as" %} Krav fremsat skriftligt senest 6 uger før generalforsamlingen skal imødekommes.{% endif %}

Indkaldelsen sendes tidligst 4 uger og senest 2 uger før generalforsamlingen, medmindre vedtægterne fastsætter en længere frist, jf. selskabslovens § 94, stk. 1. Indkaldelsen skal angive tid, sted og dagsorden og, hvis der stilles forslag om vedtægtsændringer, forslagets væsentligste indhold (fuld ordlyd i tilfældene i § 96, stk. 2), jf. selskabslovens § 96. Indkaldelsen sendes på den måde, vedtægterne foreskriver (fx e-mail, når vedtægterne giver hjemmel til elektronisk kommunikation, jf. § 92), jf. § 95.

Den ordinære generalforsamling skal afholdes i så god tid, at den godkendte årsrapport kan modtages i Erhvervsstyrelsen inden udløbet af fristen i årsregnskabslovens § 138 (for klasse B og C senest 6 måneder efter regnskabsårets udløb; klasse D 4 måneder). Fristen for årsrapporten for {{ regnskab.aar }} er {{ regnskab.frist_aarsrapport }}.

{{ kunde.by }}, {{ dato.idag }}

På {% if kunde.selskabsform_kode == "as" %}bestyrelsens{% else %}ledelsens{% endif %} vegne

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.underskriver }}
