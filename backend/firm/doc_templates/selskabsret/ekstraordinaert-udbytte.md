---
{
  "title": "Beslutning om ekstraordinært udbytte",
  "description": "Ledelsens forslag og forsvarlighedsvurdering, generalforsamlingsbeslutning og balancekrav efter SL §§ 179, 182-183 (mellembalance ved > 6 måneder; A/S altid balance). Med skattemæssig opfølgning.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 179, 180, 182, 183 og 194", "Kildeskatteloven §§ 65 og 66", "Personskatteloven § 8 a", "Ligningsloven § 16 A"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "beslutningsdato", "label": "Dato for beslutningen", "type": "date"},
    {"name": "beslutningsorgan", "label": "Besluttes af", "type": "select", "options": ["Generalforsamlingen", "Det centrale ledelsesorgan efter bemyndigelse i vedtægterne (SL § 182, stk. 2)"], "default": "Generalforsamlingen"},
    {"name": "dirigent", "label": "Dirigent (ved generalforsamling)", "type": "text"},
    {"name": "udbytte", "label": "Ekstraordinært udbytte (kr.)", "type": "number"},
    {"name": "kapitalejere_fordeling", "label": "Fordeling på kapitalejere (navn, ejerandel, beløb)", "type": "textarea"},
    {"name": "seneste_balancedag", "label": "Balancedag i seneste godkendte årsrapport", "type": "text", "default": "{{ regnskab.slut }}"},
    {"name": "frie_reserver_aarsrapport", "label": "Frie reserver iflg. seneste årsrapport (kr.)", "type": "number"},
    {"name": "allerede_udloddet", "label": "Udloddet/bundet siden balancedagen (kr.)", "type": "number", "default": "0"},
    {"name": "mere_end_6_mdr", "label": "Beslutningen træffes mere end 6 måneder efter seneste balancedag", "type": "checkbox"},
    {"name": "mellembalance_dato", "label": "Mellembalancens balancedag", "type": "date"},
    {"name": "mellembalance_frie_reserver", "label": "Frie reserver iflg. mellembalance (kr.)", "type": "number"},
    {"name": "revisionspligt", "label": "Selskabet er revisionspligtigt", "type": "checkbox", "default": true},
    {"name": "likviditet", "label": "Ledelsens vurdering af likviditet og kapitalberedskab", "type": "textarea", "default": "Selskabets likvide beholdninger og tilsagte kreditfaciliteter er efter udlodningen tilstrækkelige til at opfylde selskabets nuværende og forventede forpligtelser i mindst de kommende 12 måneder. Der er ikke indtrådt væsentlige negative begivenheder efter seneste balancedag."},
    {"name": "betalingsdato", "label": "Udbetalingsdato", "type": "date"}
  ]
}
---
# Beslutning om ekstraordinært udbytte

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}

## 1. Ledelsens forslag og vurdering

Ledelsen ({{ kunde.ledelsesorgan }}) foreslår udlodning af ekstraordinært udbytte på **{{ felt.udbytte }} kr.**

**Grundlag (SL § 182, stk. 3):** Der kan kun udloddes frie reserver efter seneste godkendte årsrapport (overført overskud og ikke-bundne reserver med fradrag af overført underskud) samt overskud og frie reserver opstået eller frigjort efter balancedagen, medmindre beløbet allerede er udloddet, forbrugt eller bundet. Selskabet skal have aflagt sin første årsrapport (§ 182, stk. 1).

| Opgørelse | Kr. |
|---|---|
| Frie reserver pr. {{ felt.seneste_balancedag }} iflg. seneste godkendte årsrapport | {{ felt.frie_reserver_aarsrapport }} |
| Udloddet, forbrugt eller bundet siden | -{{ felt.allerede_udloddet }} |
{% if felt.mere_end_6_mdr %}| Frie reserver iflg. mellembalance pr. {{ felt.mellembalance_dato }} | {{ felt.mellembalance_frie_reserver }} |
{% endif %}| **Foreslået ekstraordinært udbytte** | **{{ felt.udbytte }}** |

**Balancekrav (SL § 183):**
{% if felt.mere_end_6_mdr %}
Beslutningen træffes mere end 6 måneder efter balancedagen i den seneste godkendte årsrapport. Der er derfor udarbejdet en **mellembalance** pr. {{ felt.mellembalance_dato }}, som viser, at der er tilstrækkelige midler til udlodningen. Mellembalancen er udarbejdet efter samme regnskabspraksis som årsrapporten, og balancedagen ligger ikke mere end 6 måneder før beslutningen (§ 183, stk. 4).{% if felt.revisionspligt %} Da selskabet er revisionspligtigt, er mellembalancen gennemgået af selskabets revisor, og revisors erklæring vedlægges.{% endif %} Mellembalancen vedlægges beslutningen.
{% elif kunde.selskabsform_kode == "as" %}
I aktieselskaber skal beslutningen altid vedlægges en balance (§ 183, stk. 1). Bestyrelsen har vurderet, at det er forsvarligt at vedlægge balancen fra den seneste årsrapport, da der ikke siden balancedagen er sket væsentlige negative ændringer i selskabets økonomiske stilling.
{% else %}
I anpartsselskaber vurderer ledelsen, om beslutningen skal vedlægges en balance (§ 183, stk. 3). Ledelsen har vurderet, at {% if felt.mellembalance_dato %}der vedlægges en mellembalance pr. {{ felt.mellembalance_dato }}{% else %}balancen i seneste årsrapport giver et tilstrækkeligt grundlag, og at der ikke er behov for at vedlægge en særskilt balance{% endif %}.
{% endif %}

**Forsvarlighed (SL § 179, stk. 2):** Ledelsen har vurderet, at udlodningen ikke overstiger, hvad der er forsvarligt under hensyn til selskabets {% if branche.holding %}og koncernens {% endif %}økonomiske stilling, at den ikke sker til skade for selskabet eller dets kreditorer, og at der efter udlodningen er dækning for selskabskapitalen og bundne reserver.

{{ felt.likviditet }}

{% if branche.holding %}Ved udlodning fra holdingselskab er det vurderet, om datterselskabers forhold (garantier, sambeskatningshæftelse, forventede tab) påvirker forsvarligheden.
{% endif %}
## 2. Beslutning

{% if felt.beslutningsorgan == "Generalforsamlingen" %}
På ekstraordinær generalforsamling den {{ felt.beslutningsdato }}, ledet af {{ felt.dirigent }}, hvor {% if kunde.selskabsform_kode == "as" %}samtlige aktionærer{% else %}samtlige anpartshavere{% endif %} var til stede eller repræsenteret og gav afkald på form- og fristkrav (SL § 76, stk. 2), besluttede generalforsamlingen enstemmigt at udlodde ekstraordinært udbytte på {{ felt.udbytte }} kr. i overensstemmelse med ledelsens forslag. Generalforsamlingen kan ikke beslutte et højere beløb end foreslået eller tiltrådt af ledelsen (§ 182, stk. 1).
{% else %}
Ledelsen ({{ kunde.ledelsesorgan }}) har den {{ felt.beslutningsdato }} i henhold til bemyndigelse i vedtægterne, jf. selskabslovens § 182, stk. 2, besluttet at udlodde ekstraordinært udbytte på {{ felt.udbytte }} kr. Det er kontrolleret, at beløbet ligger inden for bemyndigelsens økonomiske og tidsmæssige rammer.
{% endif %}

Udbyttet fordeles forholdsmæssigt efter kapitalandele:

{{ felt.kapitalejere_fordeling }}

Udbyttet udbetales {{ felt.betalingsdato }} med fradrag af udbytteskat.

## 3. Skattemæssig opfølgning
- [ ] Udbytteskat (27 % til personer; til danske selskaber 22 % ved porteføljeaktier og ingen indeholdelse ved datterselskabs- eller koncernselskabsaktier, jf. kildeskattelovens § 65 og selskabsskattelovens § 13) indeholdes og angives/betales i TastSelv Erhverv senest den 10. i måneden efter beslutningen (for beslutning i december senest 17. januar), jf. kildeskattelovens §§ 65-66.
- [ ] Udbyttemodtagerne indberettes inden samme frist.
- [ ] Personlige kapitalejere: udbyttet er aktieindkomst (27 % op til 79.400 kr. i 2026, 158.800 kr. for ægtefæller; 42 % herover), jf. personskattelovens § 8 a.
- [ ] Bogføres som gæld til kapitalejere på beslutningsdagen; posteres mod overført resultat.
- [ ] Ulovlig udlodning skal tilbagebetales med renter efter § 194; ledelsen kan ifalde erstatningsansvar.

{{ kunde.by }}, {{ felt.beslutningsdato }}

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{% if felt.beslutningsorgan == "Generalforsamlingen" %}{{ felt.dirigent }}, dirigent{% else %}For ledelsen ({{ kunde.ledelsesorgan }}){% endif %}
