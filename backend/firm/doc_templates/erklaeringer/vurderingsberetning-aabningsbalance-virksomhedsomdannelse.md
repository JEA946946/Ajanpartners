---
{
  "title": "Vurderingsberetning med åbningsbalance ved virksomhedsomdannelse",
  "description": "Vurderingsberetning (ISAE 3000, høj grad af sikkerhed) ved stiftelse af kapitalselskab ved indskud af en bestående personligt ejet virksomhed, herunder skattefri virksomhedsomdannelse. Indeholder revisors erklæring om åbningsbalancen uden forbehold (SL § 36, stk. 3) og omtale af perioden mellem omdannelsestidspunktet og stiftelsen.",
  "kind": "erklaering",
  "references": ["Selskabsloven §§ 36-37 og § 36, stk. 3 (LBK nr. 331 af 20/03/2025)", "Virksomhedsomdannelsesloven §§ 2, 4 og 5", "Erhvervsstyrelsens vejledning om anvendelse af vurderingsberetninger ved registreringer", "ISAE 3000 (Revideret)", "ISA 805 (åbningsbalance)", "Årsregnskabsloven"],
  "legal_forms": ["enk", "is", "pmv", "aps", "as"],
  "industry_aware": true,
  "fields": [
    {"name": "virksomhed", "label": "Den indskudte virksomhed (navn og CVR-nr.)", "type": "text", "default": "{{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}"},
    {"name": "ejer", "label": "Indskyder/stifter (ejer af virksomheden)", "type": "text"},
    {"name": "selskab", "label": "Det nye selskabs navn (fx Navn ApS)", "type": "text"},
    {"name": "selskabsform_ny", "label": "Selskabsform", "type": "select", "options": ["anpartsselskab", "aktieselskab"], "default": "anpartsselskab"},
    {"name": "skattefri", "label": "Skattefri virksomhedsomdannelse efter virksomhedsomdannelsesloven", "type": "checkbox", "default": true},
    {"name": "omdannelsestidspunkt", "label": "Omdannelsestidspunkt/åbningsbalancedag (fx 1. januar 2026)", "type": "text"},
    {"name": "vurderingsdato", "label": "Dato for vurderingen (højst 4 uger før stiftelsesdokumentet)", "type": "text"},
    {"name": "nettoaktiver", "label": "Nettoaktiver ifølge åbningsbalancen (kr.)", "type": "number"},
    {"name": "nominel_kapital", "label": "Nominel selskabskapital (kr.)", "type": "number", "default": "40000"},
    {"name": "overkurs", "label": "Overkurs (kr., tom = kurs pari)", "type": "number"},
    {"name": "gaeldsbrev", "label": "Andet vederlag end kapitalandele (ikke tilladt ved skattefri omdannelse, ud over evt. mellemregning ved tilbagevirkende kraft)", "type": "text"},
    {"name": "vurderingsmetode", "label": "Vurderingsmetode og væsentlige poster", "type": "textarea", "default": "Aktiver og forpligtelser er indregnet efter årsregnskabslovens bestemmelser og den regnskabspraksis, selskabet vil anvende. Der er ikke indregnet goodwill eller andre merværdier, der ikke er dokumenteret ved en uafhængig vurdering."},
    {"name": "revisionspligtig", "label": "Selskabet bliver revisionspligtigt (åbningsbalancen revideres)", "type": "checkbox", "default": true},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Vurderingsberetning ved stiftelse af {{ felt.selskab }} ved indskud af bestående virksomhed

Til stifteren af {{ felt.selskab }}, {{ felt.ejer }}

I forbindelse med stiftelsen af {{ felt.selskab }} ({{ felt.selskabsform_ny }}) ved indskud af den personligt ejede virksomhed {{ felt.virksomhed }}{% if felt.skattefri %}, der gennemføres som skattefri virksomhedsomdannelse efter virksomhedsomdannelsesloven,{% endif %} afgiver vi som uvildig og sagkyndig vurderingsmand, jf. selskabslovens § 37, stk. 1, vurderingsberetning efter selskabslovens § 36 med åbningsbalance efter § 36, stk. 3.

## Konklusion

**Vurderingen.** Det er vores opfattelse, at den ansatte økonomiske værdi af den indskudte virksomhed, som udgør nettoaktiver på {{ felt.nettoaktiver }} kr. ifølge åbningsbalancen pr. {{ felt.omdannelsestidspunkt }}, mindst svarer til det aftalte vederlag, herunder den nominelle værdi af de kapitalandele, der skal udstedes, på {{ felt.nominel_kapital }} kr.{% if felt.overkurs %} med tillæg af overkurs på {{ felt.overkurs }} kr.{% endif %}{% if felt.gaeldsbrev %} og andet vederlag i form af {{ felt.gaeldsbrev }}.{% endif %}

**Åbningsbalancen.** Det er vores opfattelse, at åbningsbalancen pr. {{ felt.omdannelsestidspunkt }} i alle væsentlige henseender er udarbejdet i overensstemmelse med indregnings- og målingsbestemmelserne i årsregnskabsloven og den regnskabspraksis, som selskabet vil anvende ved udarbejdelsen af sin årsrapport, som beskrevet i noten til åbningsbalancen.

## Beskrivelse af indskuddet

Indskuddet omfatter samtlige aktiver og forpligtelser i virksomheden {{ felt.virksomhed }}, som de fremgår af den medfølgende åbningsbalance pr. {{ felt.omdannelsestidspunkt }}.{% if felt.skattefri %} Efter virksomhedsomdannelsesloven skal alle aktiver og passiver, der tilhører virksomheden, overdrages til selskabet, og vederlaget skal udelukkende bestå af kapitalandele, bortset fra en eventuel mellemregning som følge af omdannelse med tilbagevirkende kraft.{% endif %}

{% if branche.lager %}Varebeholdningerne er optalt pr. åbningsbalancedagen og målt til kostpris eller lavere nettorealisationsværdi.
{% endif %}{% if branche.igangvaerende_arbejder %}Igangværende arbejder for fremmed regning er målt til salgsværdien af det udførte arbejde med fradrag af acontofaktureringer og forventede tab.
{% endif %}{% if branche.investeringsejendomme %}Investeringsejendomme er målt til dagsværdi opgjort efter en afkastbaseret model, og der er hensat til udskudt skat af forskellen mellem regnskabsmæssig og skattemæssig værdi.
{% endif %}{% if branche.landbrug %}Biologiske aktiver (besætninger og afgrøder) er målt til dagsværdi med fradrag af salgsomkostninger, og jord og bygninger er målt efter den valgte regnskabspraksis.
{% endif %}
## Anvendte vurderingsmetoder

{{ felt.vurderingsmetode }}{% if felt.skattefri %} Der er indregnet udskudt skat af forskellen mellem de regnskabsmæssige værdier og de skattemæssige værdier, som selskabet succederer i efter virksomhedsomdannelsesloven.{% endif %}

## Perioden mellem omdannelsestidspunktet og stiftelsen

{% if felt.skattefri %}Omdannelsen har regnskabsmæssig og skattemæssig virkning fra {{ felt.omdannelsestidspunkt }}, jf. virksomhedsomdannelseslovens § 5. Driften i perioden fra omdannelsestidspunktet til stiftelsen anses for at være drevet for selskabets regning. {% endif %}Vi har vurderet driften og eventuelle hævninger i perioden fra {{ felt.omdannelsestidspunkt }} til {{ felt.vurderingsdato }} og har ikke konstateret forhold, der har forringet værdien af det indskudte, så den ikke længere mindst svarer til vederlaget. Ejerens private hævninger i perioden er behandlet som mellemregning med selskabet eller er fradraget ved opgørelsen af vederlaget.

## Grundlag for konklusion

Vi har udført vores arbejde i overensstemmelse med ISAE 3000 (Revideret), Andre erklæringsopgaver med sikkerhed end revision eller review af historiske finansielle oplysninger, og de yderligere krav, der er gældende i Danmark, med henblik på at opnå høj grad af sikkerhed for vores konklusion om vurderingen.{% if felt.revisionspligtig %} Åbningsbalancen har vi revideret i overensstemmelse med internationale standarder om revision, herunder ISA 805, og de yderligere krav, der er gældende i Danmark, idet selskabet bliver revisionspligtigt, jf. selskabslovens § 36, stk. 3.{% endif %}

Vi er uafhængige af stifteren og af det kommende selskab i overensstemmelse med International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code) og de yderligere etiske krav, der er gældende i Danmark, ligesom vi har opfyldt vores øvrige etiske forpligtelser i henhold til disse krav og IESBA Code. Revisionsvirksomheden anvender ISQM 1. Det er vores opfattelse, at det opnåede bevis er tilstrækkeligt og egnet som grundlag for vores konklusion.

## Ledelsens og stifterens ansvar

Stifteren har ansvaret for udarbejdelsen af åbningsbalancen i overensstemmelse med årsregnskabslovens indregnings- og målingsbestemmelser og den regnskabspraksis, selskabet vil anvende, og for den interne kontrol, der er nødvendig for at udarbejde en åbningsbalance uden væsentlig fejlinformation. Stifteren har ligeledes ansvaret for at fastsætte vederlaget{% if felt.skattefri %} og for, at betingelserne i virksomhedsomdannelsesloven er opfyldt, herunder at stiftelsen sker rettidigt og at Skattestyrelsen underrettes om omdannelsen inden for lovens frist{% endif %}.

## Vurderingsmandens ansvar

Vores ansvar er at udtrykke en konklusion om, hvorvidt den ansatte økonomiske værdi af den indskudte virksomhed mindst svarer til vederlaget, og om åbningsbalancen i alle væsentlige henseender er udarbejdet i overensstemmelse med det anførte regnskabsgrundlag. Vores handlinger har omfattet kontrol af ejerforhold og eksistens af væsentlige aktiver, afstemning af bank, tilgodehavender, gæld og skyldige skatter og afgifter, gennemgang af periodeafgrænsning, vurdering af måling og nedskrivningsbehov, gennemgang af perioden efter omdannelsestidspunktet samt indhentelse af ledelseserklæring.

## Begrænsning i anvendelse

Beretningen er udarbejdet til opfyldelse af selskabslovens § 36 og skal vedlægges stiftelsesdokumentet. Den er ikke udarbejdet tidligere end 4 uger før underskrivelsen af stiftelsesdokumentet, jf. § 36, stk. 2. Beretningen er ikke egnet til andre formål.

{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
