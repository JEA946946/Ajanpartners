---
{
  "title": "Beslutning om vedtægtsændring",
  "description": "Generalforsamlingsbeslutning om ændring af vedtægter med majoritetskrav (SL §§ 106-107), indkaldelseskrav, konsoliderede vedtægter og anmeldelse til Erhvervsstyrelsen.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 28, 96, 106 og 107", "Selskabsloven § 9", "Selskabsloven § 76"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "gf_dato", "label": "Dato for generalforsamlingen", "type": "date"},
    {"name": "gf_type", "label": "Generalforsamling", "type": "select", "options": ["ordinær", "ekstraordinær"], "default": "ekstraordinær"},
    {"name": "dirigent", "label": "Dirigent", "type": "text"},
    {"name": "aendringstype", "label": "Type ændring", "type": "select", "options": ["Navn/binavne", "Formål", "Hjemsted/adresse (kun kommune hvis angivet)", "Regnskabsår", "Ledelsesstruktur", "Elektronisk kommunikation/generalforsamling", "Ophævelse af revisionsbestemmelse", "Bemyndigelse til kapitalforhøjelse/ekstraordinært udbytte", "Omsættelighedsbegrænsning", "Andet"], "default": "Andet"},
    {"name": "gammel", "label": "Nuværende ordlyd", "type": "textarea"},
    {"name": "ny", "label": "Ny ordlyd", "type": "textarea"},
    {"name": "stemmer_for", "label": "Stemmer for (% af afgivne/repræsenterede)", "type": "text", "default": "100 % / 100 %"},
    {"name": "enstemmig", "label": "Alle kapitalejere til stede og enige", "type": "checkbox", "default": true}
  ]
}
---
# Beslutning om vedtægtsændring

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}

På {{ felt.gf_type }} generalforsamling den {{ felt.gf_dato }} under ledelse af dirigent {{ felt.dirigent }} blev følgende ændring af selskabets vedtægter vedtaget:

**Nuværende ordlyd:**
> {{ felt.gammel }}

**Ny ordlyd:**
> {{ felt.ny }}

## Majoritet og lovlighed
Dirigenten konstaterede, at
{% if felt.enstemmig %}- samtlige kapitalejere var til stede eller repræsenteret og enstemmigt havde fraveget form- og fristkrav (selskabslovens § 76, stk. 2), og at forslaget blev vedtaget enstemmigt,{% else %}- generalforsamlingen var lovligt indkaldt, og indkaldelsen angav forslagets væsentligste indhold (fuld ordlyd hvor § 96, stk. 2 kræver det),
- forslaget blev vedtaget med {{ felt.stemmer_for }} af såvel de afgivne stemmer som den repræsenterede kapital, dvs. mindst 2/3 (selskabslovens § 106),{% endif %}
{% if felt.aendringstype == "Omsættelighedsbegrænsning" %}- beslutningen begrænser kapitalandelenes omsættelighed og kræver derfor tilslutning fra mindst 9/10 af såvel de afgivne stemmer som den repræsenterede kapital (§ 107, stk. 2, nr. 2),
{% endif %}{% if felt.aendringstype == "Regnskabsår" %}- omlægningen af regnskabsåret medfører et overgangsår på højst 18 måneder (årsregnskabslovens § 15). Skattemæssigt kræver omlægning tilladelse fra Skattestyrelsen, medmindre den skyldes indtræden i sambeskatning,
{% endif %}{% if felt.aendringstype == "Ophævelse af revisionsbestemmelse" %}- ophævelsen sker i forbindelse med fravalg af revision på ordinær generalforsamling (årsregnskabslovens § 135, stk. 1), og betingelserne er dokumenteret,
{% endif %}{% if felt.aendringstype == "Navn/binavne" %}- navnet indeholder selskabsformen ({{ kunde.selskabsform }}) og er tilstrækkeligt adskilt fra andre registrerede navne og varemærker,
{% endif %}- beslutningen ikke er omfattet af kravet om enstemmighed i § 107, stk. 1 (forøgede forpligtelser for kapitalejerne).

## Opfølgning
- [ ] Konsoliderede vedtægter med ny dato udarbejdes og underskrives af dirigent/ledelse.
- [ ] Anmeldelse til Erhvervsstyrelsen senest 2 uger efter beslutningen med vedtægter og referat (selskabslovens § 9).
{% if felt.aendringstype == "Navn/binavne" %}- [ ] Nyt navn på brevpapir, hjemmeside, fakturaer, bank, Skattestyrelsen (opdateres via CVR), forsikringer og domæner.
{% endif %}{% if felt.aendringstype == "Regnskabsår" %}- [ ] Ansøgning om omlægning af indkomstår til Skattestyrelsen; aconto skat og frister tilpasses.
{% endif %}{% if felt.aendringstype == "Formål" %}- [ ] Branchekode i CVR opdateres; vurdér om ændringen medfører tilladelseskrav eller hvidvaskpligt.
{% endif %}

{{ kunde.by }}, {{ felt.gf_dato }}

Som dirigent:

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.dirigent }}
