---
{
  "title": "Beslutning om fravalg af revision",
  "description": "Generalforsamlingsbeslutning, ledelsens vurdering af betingelserne i ÅRL §§ 135-135 a og tjekliste til anmeldelse. Omfatter holdingreglen, 50 mio.-grænsen og klassificerede risikobrancher.",
  "kind": "beslutning",
  "references": ["Årsregnskabsloven § 135, stk. 1-6", "Årsregnskabsloven § 135 a", "Årsregnskabsloven § 110", "Bekendtgørelse nr. 1488 af 27. november 2025 om klassificerede risikobrancher", "Selskabsloven §§ 9, 88 og 106", "Erhvervsstyrelsen: Fravalg af revision (erhvervsstyrelsen.dk/fravalg-af-revision)"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": true,
  "fields": [
    {"name": "gf_dato", "label": "Dato for ordinær generalforsamling", "type": "date"},
    {"name": "dirigent", "label": "Dirigent", "type": "text"},
    {"name": "aar1", "label": "Første regnskabsår i testen", "type": "text"},
    {"name": "aar2", "label": "Andet regnskabsår i testen", "type": "text", "default": "{{ regnskab.aar }}"},
    {"name": "balance1", "label": "Balancesum år 1 (kr.)", "type": "number"},
    {"name": "balance2", "label": "Balancesum år 2 (kr.)", "type": "text", "default": "{{ regnskab.balancesum }}"},
    {"name": "oms1", "label": "Nettoomsætning år 1 (kr.)", "type": "number"},
    {"name": "oms2", "label": "Nettoomsætning år 2 (kr.)", "type": "text", "default": "{{ regnskab.omsaetning }}"},
    {"name": "ansatte1", "label": "Gns. heltidsansatte år 1", "type": "number"},
    {"name": "ansatte2", "label": "Gns. heltidsansatte år 2", "type": "number"},
    {"name": "kapitalinteresser", "label": "Selskabet har kapitalinteresser med betydelig indflydelse (≥ 20 % stemmer)", "type": "checkbox"},
    {"name": "risikobranche", "label": "Hovedbranchekode er en klassificeret risikobranche (bkg. 1488/2025)", "type": "checkbox", "default": "{% if branche.risikobranche %}true{% endif %}"},
    {"name": "vedtaegtsbestemmelse", "label": "Vedtægternes bestemmelse om revision (der ophæves)", "type": "textarea", "default": "§ [nr.] Selskabets årsregnskab revideres af en statsautoriseret eller registreret revisor, der vælges af generalforsamlingen for ét år ad gangen."}
  ]
}
---
# Beslutning om fravalg af revision

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}

## 1. Ledelsens vurdering af betingelserne

Ledelsen har forud for den ordinære generalforsamling vurderet, om selskabet opfylder betingelserne for at undlade revision efter årsregnskabslovens § 135, stk. 1, 3. pkt.

**Størrelsesgrænser** – må ikke overskride to af tre i to på hinanden følgende regnskabsår på balancetidspunktet:

| | Grænse | {{ felt.aar1 }} | {{ felt.aar2 }} |
|---|---|---|---|
| Balancesum | 4.000.000 kr. | {{ felt.balance1 }} | {{ felt.balance2 }} |
| Nettoomsætning | 8.000.000 kr. | {{ felt.oms1 }} | {{ felt.oms2 }} |
| Gns. heltidsbeskæftigede | 12 | {{ felt.ansatte1 }} | {{ felt.ansatte2 }} |

Beløbene opgøres efter ÅRL § 7, stk. 3 og 4 (nettoomsætning omregnes til 12 måneder ved forlænget eller forkortet regnskabsår).

**Øvrige betingelser**

- [ ] Selskabet er i regnskabsklasse B ({{ kunde.regnskabsklasse }}).
- [ ] Balancesummen har ikke i 2 på hinanden følgende år oversteget 50 mio. kr. (§ 135, stk. 2).
{% if felt.kapitalinteresser or branche.holding %}- [ ] **Holdingreglen (§ 135, stk. 4):** Selskabet og de virksomheder, hvori det besidder kapitalinteresser og udøver betydelig indflydelse, overskrider ikke tilsammen grænserne i 2 på hinanden følgende år. Opgjort efter § 110, stk. 3 (sammenlægning med eliminering af koncerninterne poster) eller § 110, stk. 4 (simpel sammenlægning; grænserne forhøjes med 20 % til 4,8 mio. kr. og 9,6 mio. kr.). Betydelig indflydelse formodes ved 20 % eller mere af stemmerne. Opgørelsen vedlægges.
{% endif %}- [ ] Hverken selskabet, en tilknyttet virksomhed eller den, der har bestemmende indflydelse, har vedtaget bødeforelæg eller er dømt for overtrædelse af selskabs-, regnskabs-, hvidvask- eller skatte- og afgiftslovgivningen, således at fravalg er udelukket for det regnskabsår, hvori den endelige dom/det endelige bødeforelæg foreligger, og de 2 efterfølgende regnskabsår (§ 135 a, stk. 1).
- [ ] Intet ledelsesmedlem er indtrådt, der inden for de seneste 2 år før sin indtræden har været i konkurskarantæne (§ 135 a, stk. 2).
- [ ] Erhvervsstyrelsen har ikke truffet afgørelse efter § 135 a, stk. 3, om at fravalg ikke kan anvendes (væsentlige fejl ved kontrol af årsrapport eller bogføring).
- [ ] Selskabet er ikke en erhvervsdrivende fond eller et medarbejderinvesteringsselskab (§ 135, stk. 3).
{% if felt.risikobranche %}- [ ] **Klassificeret risikobranche (§ 135, stk. 5):** Selskabets hovedbranchekode ({{ kunde.branchekode }} {{ kunde.branchetekst }}) skal kontrolleres mod listen i bekendtgørelse nr. 1488 af 27. november 2025. Overskrider nettoomsætningen 5 mio. kr. i 2 på hinanden følgende år, kan revisionen fravælges, men årsregnskabet skal **fortsat** forsynes med en opstillingserklæring eller en erklæring med sikkerhed fra en godkendt revisor.
{% endif %}

**Konklusion:** Ledelsen vurderer, at betingelserne for fravalg af revision er opfyldt.

{% if branche.kontantintensiv or branche.byggeri or branche.vikar or branche.rengoering %}*Rådgivers bemærkning:* Selskabet driver virksomhed i en branche med forhøjet risiko for fejl og sort arbejde ({{ branche.navn }}). Selv hvor revision lovligt kan fravælges, bør det overvejes at bevare en erklæring (opstilling eller review), bl.a. af hensyn til banker, kreditforsikring og Skattestyrelsens kontrol.
{% endif %}
## 2. Generalforsamlingens beslutning

På selskabets ordinære generalforsamling den {{ felt.gf_dato }} besluttede generalforsamlingen under ledelse af dirigent {{ felt.dirigent }}:

1. at selskabets årsregnskab fra og med regnskabsåret efter {{ regnskab.aar }} ikke skal revideres, jf. årsregnskabslovens § 135, stk. 1, 3. pkt.,
2. at selskabets revisor fratræder med virkning fra generalforsamlingens afslutning, og
3. at følgende bestemmelse i vedtægterne ophæves (vedtaget med mindst 2/3 af de afgivne stemmer og den repræsenterede kapital, jf. selskabslovens § 106):

> {{ felt.vedtaegtsbestemmelse }}

Fravalget kan kun besluttes på en ordinær generalforsamling og kun med fremadrettet virkning.

## 3. Opfølgning

- [ ] Fravalget af revisor anmeldes til Erhvervsstyrelsen senest 2 uger efter beslutningen; ændrede vedtægter indsendes med generalforsamlingsreferatet vedlagt (selskabslovens § 9).
- [ ] I ledelsespåtegningen i årsrapporten for {{ regnskab.aar }} oplyses, at generalforsamlingen har besluttet at fravælge revision for kommende regnskabsår.
- [ ] I ledelsespåtegningen i den første ureviderede årsrapport erklærer ledelsen, at betingelserne for fravalg er opfyldt.
- [ ] Betingelserne overvåges årligt. Ifølge Erhvervsstyrelsen bliver virksomheden revisionspligtig allerede for det andet regnskabsår, hvor to af grænserne overskrides (tilsvarende for 50 mio.-grænsen), og der skal da vælges revisor.
- [ ] Det aftales, hvilken assistance {{ firma.navn }} fremover yder (opstilling efter ISRS 4410, review, skattemæssig assistance).

{{ kunde.by }}, {{ felt.gf_dato }}

Som dirigent:

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.dirigent }}
