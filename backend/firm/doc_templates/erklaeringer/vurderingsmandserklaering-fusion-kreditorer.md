---
{
  "title": "Vurderingsmandens erklæringer ved fusion (kreditorerklæring m.v., SL §§ 240-242)",
  "description": "Uvildig vurderingsmands erklæringer ved fusion af kapitalselskaber: erklæring om kreditorernes stilling (§ 242), udtalelse om fusionsplanen og vederlaget (§ 241) og vurderingsberetning ved kapitalforhøjelse i det fortsættende selskab (§ 240). Hver erklæring kan til- og fravælges, fx når kapitalejerne i enighed har fravalgt § 241- og § 242-erklæringerne. Kan tilpasses spaltning, hvor selskabsloven henviser til de tilsvarende regler.",
  "kind": "erklaering",
  "references": ["Selskabsloven §§ 237-242 og 249 (LBK nr. 331 af 20/03/2025)", "Selskabsloven § 37, stk. 1 (vurderingsmand)", "ISAE 3000 (Revideret)", "ISQM 1", "Erhvervsstyrelsens vejledning om fusion og om vurderingsberetninger"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "transaktion", "label": "Transaktion", "type": "select", "options": ["fusion", "spaltning"], "default": "fusion"},
    {"name": "fortsaettende", "label": "Fortsættende/modtagende selskab (navn og CVR)", "type": "text"},
    {"name": "ophoerende", "label": "Ophørende/indskydende selskab(er) (navn og CVR)", "type": "text"},
    {"name": "fusionsplan_dato", "label": "Dato for fusions-/spaltningsplanen", "type": "text"},
    {"name": "virkningstidspunkt", "label": "Regnskabsmæssigt virkningstidspunkt", "type": "text"},
    {"name": "regnskabsgrundlag", "label": "Regnskabsmæssigt grundlag (fx godkendte årsrapporter for 2025 og mellembalancer pr. ...)", "type": "text"},
    {"name": "kreditorerklaering", "label": "Erklæring om kreditorernes stilling (§ 242)", "type": "checkbox", "default": true},
    {"name": "kreditor_vurdering", "label": "Grundlag for kreditorvurderingen (egenkapital, likviditet, sikkerheder, koncerninterne mellemværender)", "type": "textarea"},
    {"name": "vederlagserklaering", "label": "Udtalelse om fusionsplanen og vederlaget (§ 241)", "type": "checkbox", "default": false},
    {"name": "vederlag", "label": "Vederlag/ombytningsforhold", "type": "text"},
    {"name": "vederlag_metoder", "label": "Metoder til fastsættelse af vederlaget, værdier og vægtning, særlige vanskeligheder", "type": "textarea"},
    {"name": "vurderingsberetning", "label": "Vurderingsberetning ved kapitalforhøjelse/nyt selskab (§ 240)", "type": "checkbox", "default": false},
    {"name": "kapitalforhoejelse", "label": "Kapitalforhøjelse i det fortsættende selskab: nominelt beløb og overkurs", "type": "text"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato (højst 3 måneder før vedtagelsen)", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Vurderingsmandens erklæringer om {% if felt.transaktion == "fusion" %}fusionen{% else %}spaltningen{% endif %} mellem {{ felt.fortsaettende }} og {{ felt.ophoerende }}

Til kapitalejerne og kreditorerne i de deltagende selskaber

Vi er udpeget som uvildig og sagkyndig vurderingsmand, jf. selskabslovens § 37, stk. 1, i forbindelse med den påtænkte {{ felt.transaktion }} mellem {{ felt.fortsaettende }} som fortsættende/modtagende selskab og {{ felt.ophoerende }} som ophørende/indskydende selskab i henhold til {{ felt.transaktion }}splanen dateret {{ felt.fusionsplan_dato }}, med regnskabsmæssig virkning fra {{ felt.virkningstidspunkt }}. Erklæringerne er afgivet på grundlag af {{ felt.regnskabsgrundlag }}.

{% if felt.kreditorerklaering %}## Erklæring om kreditorernes stilling (selskabslovens § 242)

### Konklusion

Det er vores opfattelse, at kreditorerne i hvert af de deltagende selskaber efter {{ felt.transaktion }}en må antages at være tilstrækkeligt sikrede i forhold til det enkelte selskabs nuværende situation.

### Grundlag for vurderingen

{{ felt.kreditor_vurdering }}

Vi har ved vurderingen taget hensyn til de deltagende selskabers egenkapital, likviditet, indtjeningsevne, eventualforpligtelser og stillede sikkerheder samt til de koncerninterne mellemværender, der bortfalder eller overtages ved {{ felt.transaktion }}en.

{% endif %}{% if felt.vederlagserklaering %}## Udtalelse om {{ felt.transaktion }}splanen og vederlaget (selskabslovens § 241)

### Konklusion

Det er vores opfattelse, at vederlaget for kapitalandelene i det ophørende selskab, {{ felt.vederlag }}, er rimeligt og sagligt begrundet.

### Metoder, værdier og vægtning

{{ felt.vederlag_metoder }}

Efter vores vurdering er de anvendte metoder passende, og den indbyrdes vægtning af metoderne er rimelig.

{% endif %}{% if felt.vurderingsberetning %}## Vurderingsberetning (selskabslovens § 240, jf. § 36)

### Konklusion

Det er vores opfattelse, at den ansatte økonomiske værdi af de aktiver og forpligtelser, der overgår fra {{ felt.ophoerende }}, mindst svarer til det aftalte vederlag, herunder den nominelle værdi af de kapitalandele, der udstedes i {{ felt.fortsaettende }}, med tillæg af eventuel overkurs ({{ felt.kapitalforhoejelse }}).

### Beskrivelse og vurderingsmetode

Indskuddet består af samtlige aktiver og forpligtelser i {{ felt.ophoerende }} som de fremgår af {{ felt.regnskabsgrundlag }}. Aktiver og forpligtelser er værdiansat efter den regnskabspraksis, der anvendes i det fortsættende selskab, korrigeret for begivenheder frem til datoen for denne erklæring.

{% endif %}## Grundlag for konklusionerne

Vi har udført vores arbejde i overensstemmelse med ISAE 3000 (Revideret), Andre erklæringsopgaver med sikkerhed end revision eller review af historiske finansielle oplysninger, og de yderligere krav, der er gældende i Danmark, med henblik på at opnå høj grad af sikkerhed for vores konklusioner. Vores handlinger har omfattet gennemgang af {{ felt.transaktion }}splanen og -redegørelsen, de regnskabsmæssige grundlag, likviditetsbudgetter, låneaftaler og sikkerhedsstillelser, forespørgsler til ledelserne i de deltagende selskaber, vurdering af begivenheder efter balancedagene samt indhentelse af ledelseserklæringer.

Vi er uafhængige af de deltagende selskaber i overensstemmelse med International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code) og de yderligere etiske krav, der er gældende i Danmark. Revisionsvirksomheden anvender ISQM 1. Det er vores opfattelse, at det opnåede bevis er tilstrækkeligt og egnet som grundlag for vores konklusioner.

## Ledelsens ansvar

De centrale ledelsesorganer i de deltagende selskaber har ansvaret for {{ felt.transaktion }}splanen, for fastsættelse af vederlaget og for de regnskabsmæssige grundlag, der ligger til grund for {{ felt.transaktion }}en.

## Vurderingsmandens ansvar

Vores ansvar er på grundlag af vores handlinger at udtrykke de konklusioner, der kræves efter selskabsloven. Vi har ikke vurderet de forretningsmæssige eller skattemæssige fordele ved {{ felt.transaktion }}en.

## Begrænsning i anvendelse

Erklæringerne er udarbejdet til brug for vedtagelse og registrering af {{ felt.transaktion }}en og skal offentliggøres via Erhvervsstyrelsen. De må ikke være mere end 3 måneder gamle på tidspunktet for vedtagelsen.{% if felt.kreditorerklaering %} Konkluderer en vurderingsmand, at kreditorerne ikke er tilstrækkeligt sikrede, har kreditorerne ret til at anmelde deres krav og kræve sikkerhed efter selskabslovens regler herom.{% endif %}

{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
