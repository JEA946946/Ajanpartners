---
{
  "title": "Beslutning om kapitalnedsættelse",
  "description": "Generalforsamlingsbeslutning om nedsættelse af selskabskapitalen til dækning af underskud, udbetaling til kapitalejere eller særlig reserve, med kreditorproklama (4 uger) og gennemførelse efter SL §§ 185-193.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 185-193", "Selskabsloven § 179", "Selskabsloven § 4, stk. 2", "Ligningsloven § 16 A og § 16 B"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "gf_dato", "label": "Dato for generalforsamlingen", "type": "date"},
    {"name": "dirigent", "label": "Dirigent", "type": "text"},
    {"name": "formaal", "label": "Formål", "type": "select", "options": ["Dækning af underskud", "Udbetaling til kapitalejere", "Henlæggelse til særlig reserve"], "default": "Udbetaling til kapitalejere"},
    {"name": "nuvaerende_kapital", "label": "Nuværende selskabskapital (kr.)", "type": "number"},
    {"name": "nedsaettelse", "label": "Nedsættelsesbeløb (nominelt kr.)", "type": "number"},
    {"name": "kurs", "label": "Kurs for udbetaling (fx 100 eller højere)", "type": "text", "default": "100"},
    {"name": "udbetaling_i_alt", "label": "Samlet udbetaling inkl. overkurs (kr.)", "type": "number"},
    {"name": "fordeling", "label": "Fordeling på kapitalejere", "type": "textarea", "default": "Forholdsmæssigt efter kapitalandele."},
    {"name": "samtidig_forhoejelse", "label": "Kapitalen forhøjes samtidig med mindst samme beløb (ingen proklama)", "type": "checkbox"},
    {"name": "vedtaegtsbestemmelse", "label": "Ny ordlyd af kapitalbestemmelsen", "type": "textarea"}
  ]
}
---
# Beslutning om kapitalnedsættelse

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}

På generalforsamling den {{ felt.gf_dato }} under ledelse af dirigent {{ felt.dirigent }} blev det med det flertal, der kræves til vedtægtsændring (selskabslovens §§ 106 og 186), besluttet:

1. Selskabskapitalen nedsættes med nominelt **{{ felt.nedsaettelse }} kr.** fra nominelt {{ felt.nuvaerende_kapital }} kr.
2. Nedsættelsesbeløbet anvendes til følgende formål: **{{ felt.formaal }}** (selskabslovens § 188, stk. 1).
{% if felt.formaal == "Udbetaling til kapitalejere" %}3. Udbetalingen sker til kurs {{ felt.kurs }}, i alt {{ felt.udbetaling_i_alt }} kr., således at {{ felt.udbetaling_i_alt }} kr. udbetales, heraf nominelt {{ felt.nedsaettelse }} kr. som nedsættelsesbeløb og resten som overkurs (selskabslovens § 188, stk. 2). Fordeling: {{ felt.fordeling }}
{% elif felt.formaal == "Dækning af underskud" %}3. Nedsættelsen sker ved overførsel af {{ felt.nedsaettelse }} kr. fra selskabskapitalen til overført resultat til dækning af underskud, som er opgjort i selskabets senest godkendte årsrapport eller i en mellembalance.
{% else %}3. Nedsættelsesbeløbet henlægges til en særlig reserve, der kun kan anvendes efter generalforsamlingens beslutning.
{% endif %}4. Vedtægternes kapitalbestemmelse affattes således:

> {{ felt.vedtaegtsbestemmelse }}

Selskabskapitalen udgør efter nedsættelsen mindst {% if kunde.selskabsform_kode == "as" %}400.000{% else %}20.000{% endif %} kr. (selskabslovens § 4, stk. 2).

## Ledelsens vurdering
{% if felt.formaal == "Dækning af underskud" %}Ledelsen bekræfter, at underskuddet er opgjort korrekt, og at der ikke findes frie reserver, som kan dække det.{% else %}Ledelsen har vurderet, at nedsættelsen er forsvarlig under hensyn til selskabets økonomiske stilling, og at den ikke sker til skade for selskabet eller dets kreditorer (selskabslovens § 179, stk. 2). Selskabets likviditet og kapitalberedskab vil efter udbetalingen være tilstrækkeligt.{% endif %}

{% if kunde.selskabsform_kode == "as" %}Forslaget og dokumenterne efter selskabslovens § 156 har været tilgængelige for aktionærerne (§ 185).{% endif %}

## Kreditorbeskyttelse og gennemførelse
{% if felt.formaal == "Dækning af underskud" %}Ved nedsættelse til dækning af underskud skal kreditorerne ikke opfordres til at anmelde krav. Nedsættelsen gennemføres ved registreringen.
{% elif felt.samtidig_forhoejelse %}Da kapitalen samtidig forhøjes ved tegning af mindst samme nominelle beløb med tillæg af overkurs som nedsættelsesbeløbet, skal der ikke ske kreditorproklama (selskabslovens § 192, stk. 2).
{% else %}
1. Beslutningen anmeldes til Erhvervsstyrelsen senest 2 uger efter beslutningen; ellers mister den sin gyldighed (selskabslovens § 191).
2. Ved Erhvervsstyrelsens offentliggørelse opfordres selskabets kreditorer til at anmelde deres krav inden 4 uger (§ 192, stk. 1).
3. Efter fristens udløb træffer ledelsen beslutning om gennemførelse, hvis det fortsat er forsvarligt, og anmeldte forfaldne krav er dækket eller der er stillet betryggende sikkerhed (§ 193, stk. 1). Udbetaling må først ske herefter.
4. Gennemførelsen anmeldes; Erhvervsstyrelsen kan registrere gennemførelsen 4 uger efter proklamafristens udløb, medmindre selskabet forinden har registreret gennemførelse eller annullation (§ 193, stk. 2).
{% endif %}

## Skattemæssige forhold
{% if felt.formaal == "Udbetaling til kapitalejere" %}
- Udbetaling ved kapitalnedsættelse behandles som udbytte efter ligningslovens § 16 A, medmindre betingelserne for afståelsesbeskatning efter § 16 A, stk. 3, nr. 1, litra b, er opfyldt (fx kapitalejere med under 10 % af kapitalen eller selskabsaktionærer med datterselskabsaktier).
- Behandles udbetalingen som udbytte, indeholdes udbytteskat efter kildeskatteloven, og beløbet indberettes.
- For selskabsaktionærer med datterselskabs- eller koncernselskabsaktier er udbetalingen som udgangspunkt skattefri.
{% else %}
- Nedsættelse til dækning af underskud eller henlæggelse til særlig reserve udløser ikke beskatning hos kapitalejerne.
{% endif %}

## Opfølgning
- [ ] Anmeldelse senest 2 uger efter beslutningen med opdaterede vedtægter.
- [ ] Ejerbog, ejerregister og reelle ejere opdateres efter gennemførelsen.
- [ ] Bogføring: nedsættelse/udbetaling registreres ved gennemførelse.

{{ kunde.by }}, {{ felt.gf_dato }}

Som dirigent:

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.dirigent }}
