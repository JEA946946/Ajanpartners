---
{
  "title": "Erklæring om mellembalance ved ekstraordinært udbytte eller kapitalnedsættelse",
  "description": "Revisors reviewerklæring på mellembalance, der skal ligge til grund for ekstraordinært udbytte (SL §§ 182-183) eller – efter aftale – kapitalnedsættelse til udbetaling (SL § 188, stk. 1, nr. 2). SL § 183, stk. 4, kræver, at en mellembalance ved ekstraordinært udbytte er gennemgået af revisor, hvis selskabet er revisionspligtigt; SL §§ 185-193 indeholder ikke et tilsvarende krav ved kapitalnedsættelse. Valgfrit afsnit med vurderingsberetning ved udlodning i andre værdier end kontanter (SL § 183, stk. 5, og § 190).",
  "kind": "erklaering",
  "references": ["Selskabsloven §§ 179-183 og 188-194 (LBK nr. 331 af 20/03/2025)", "ISRE 2410 / ISRE 2400 (Revideret)", "ISAE 3000 (ved vurderingsberetning)", "Selskabsloven § 183, stk. 5, og § 190, jf. §§ 36-37 (udlodning i andre værdier end kontanter)", "Erklæringsbekendtgørelsen (BEK nr. 518 af 24/05/2024) §§ 18-21", "Erhvervsstyrelsens vejledning om anvendelse af vurderingsberetninger"],
  "legal_forms": ["aps", "as", "holding", "ivs"],
  "industry_aware": false,
  "fields": [
    {"name": "formaal", "label": "Formål", "type": "select", "options": ["ekstraordinært udbytte", "kapitalnedsættelse til udbetaling til kapitalejerne"], "default": "ekstraordinært udbytte"},
    {"name": "balancedato", "label": "Mellembalancens balancedag (ved ekstraordinært udbytte højst 6 måneder før beslutningen, SL § 183, stk. 4)", "type": "text"},
    {"name": "frie_reserver", "label": "Frie reserver ifølge mellembalancen (kr.)", "type": "number"},
    {"name": "udlodning", "label": "Foreslået udlodning/udbetaling i alt (kr.)", "type": "number"},
    {"name": "nedsaettelse_nominelt", "label": "Kapitalnedsættelse – nominelt beløb (kr., kun ved kapitalnedsættelse)", "type": "number"},
    {"name": "standard", "label": "Standard for gennemgangen", "type": "select", "options": ["ISRE 2410 (review udført af selskabets valgte revisor)", "ISRE 2400 (Revideret)"], "default": "ISRE 2410 (review udført af selskabets valgte revisor)"},
    {"name": "naturalier", "label": "Udlodningen sker helt eller delvis i andre værdier end kontanter (vurderingsberetning)", "type": "checkbox", "default": false},
    {"name": "naturalier_beskrivelse", "label": "Beskrivelse af de udloddede aktiver og vurderingsmetode", "type": "textarea"},
    {"name": "naturalier_vaerdi", "label": "Ansat værdi af de udloddede aktiver (kr.)", "type": "number"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Den uafhængige revisors reviewerklæring om mellembalance

Til {{ kunde.ledelsesorgan }} og {{ kunde.kapitalejere }} i {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}

## Indledning

Vi har udført review af den medfølgende mellembalance for {{ kunde.navn }} pr. {{ felt.balancedato }}, der omfatter balance, egenkapitalopgørelse og noter, herunder anvendt regnskabspraksis. Mellembalancen er udarbejdet af ledelsen til brug for beslutning om {{ felt.formaal }}{% if felt.formaal == "ekstraordinært udbytte" %}, jf. selskabslovens §§ 182 og 183{% else %}, jf. selskabslovens § 188, stk. 1, nr. 2. Selskabsloven stiller ikke krav om revisors gennemgang af en mellembalance ved kapitalnedsættelse, og erklæringen er afgivet efter aftale med selskabet{% endif %}.

## Ledelsens ansvar

Ledelsen har ansvaret for udarbejdelsen af mellembalancen i overensstemmelse med indregnings- og målingsbestemmelserne i årsregnskabsloven og den regnskabspraksis, der er anvendt i selskabets seneste årsrapport, og for den interne kontrol, som ledelsen anser for nødvendig for at udarbejde en mellembalance uden væsentlig fejlinformation. Ledelsen har endvidere ansvaret for at vurdere, om udlodningen er forsvarlig under hensyn til selskabets økonomiske stilling og begivenheder efter balancedagen, jf. selskabslovens § 179, stk. 2, og § 115.

## Revisors ansvar

Vores ansvar er at udtrykke en konklusion om mellembalancen på grundlag af vores review. Vi har udført vores review i overensstemmelse med {{ felt.standard }} og de yderligere krav, der er gældende i Danmark. Et review består af forespørgsler, primært til de personer, der er ansvarlige for økonomi og regnskab, analytiske handlinger og andre reviewhandlinger. Et review er væsentligt mindre omfattende end en revision udført efter internationale standarder om revision og giver os derfor ikke mulighed for at opnå sikkerhed for, at vi er blevet bekendt med alle betydelige forhold, som kunne være blevet identificeret ved en revision. Vi udtrykker derfor ikke en revisionskonklusion.

Vi er uafhængige af selskabet i overensstemmelse med International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code) og de yderligere etiske krav, der er gældende i Danmark.

## Konklusion

Ved vores review er vi ikke blevet opmærksomme på forhold, der giver os grund til at mene, at mellembalancen pr. {{ felt.balancedato }} ikke i alle væsentlige henseender er udarbejdet i overensstemmelse med indregnings- og målingsbestemmelserne i årsregnskabsloven og den regnskabspraksis, der er anvendt i selskabets seneste årsrapport.

## Oplysninger om udlodningsgrundlaget

Det fremgår af mellembalancen, at selskabets frie reserver pr. {{ felt.balancedato }} udgør {{ felt.frie_reserver }} kr. Den foreslåede {% if felt.formaal == "ekstraordinært udbytte" %}udlodning af ekstraordinært udbytte{% else %}udbetaling i forbindelse med kapitalnedsættelsen (nominelt {{ felt.nedsaettelse_nominelt }} kr.){% endif %} udgør i alt {{ felt.udlodning }} kr.{% if felt.formaal == "ekstraordinært udbytte" %} Vi har påset, at udlodningen ikke overstiger de midler, der efter selskabslovens § 182, stk. 3, kan anvendes som ekstraordinært udbytte, opgjort på grundlag af mellembalancen med fradrag af udlodninger og andre dispositioner over de frie reserver efter balancedagen, som vi er blevet bekendt med.{% endif %}

Vores konklusion omfatter ikke ledelsens vurdering af, om udlodningen er forsvarlig, jf. selskabslovens § 179, stk. 2.{% if felt.formaal == "kapitalnedsættelse til udbetaling til kapitalejerne" %} Vi gør opmærksom på, at kapitalnedsættelse til udbetaling forudsætter opfordring til kreditorerne efter selskabslovens § 192, stk. 1, medmindre kapitalen samtidig forhøjes ved tegning af mindst samme nominelle beløb med tillæg af overkurs som nedsættelsesbeløbet, jf. § 192, stk. 2.{% endif %}

{% if felt.naturalier %}## Vurderingsberetning ved udlodning i andre værdier end kontanter

Udlodningen sker helt eller delvis i andre værdier end kontanter. Som uvildig og sagkyndig vurderingsmand, jf. selskabslovens § 37, stk. 1, har vi efter selskabslovens {% if felt.formaal == "ekstraordinært udbytte" %}§ 183, stk. 5{% else %}§ 190{% endif %} udført en erklæringsopgave med høj grad af sikkerhed i overensstemmelse med ISAE 3000 (Revideret) vedrørende de udloddede aktiver.

{{ felt.naturalier_beskrivelse }}

Det er vores opfattelse, at {% if felt.formaal == "ekstraordinært udbytte" %}udbyttebeløbet{% else %}kapitalnedsættelsen med tillæg af eventuel overkurs{% endif %} mindst svarer til den ansatte værdi af de andre værdier end kontanter, der udloddes, på {{ felt.naturalier_vaerdi }} kr.

{% endif %}## Begrænsning i anvendelse

{% if felt.formaal == "ekstraordinært udbytte" %}Erklæringen er udelukkende udarbejdet til brug for selskabets beslutning om ekstraordinært udbytte, og mellembalancen skal indgå i protokollen som bilag til beslutningen, jf. selskabslovens § 183, stk. 6. Mellembalancen må ikke have balancedag, der ligger mere end 6 måneder forud for beslutningen, jf. § 183, stk. 4. Erklæringen er ikke egnet til andre formål.{% else %}Erklæringen er udelukkende udarbejdet til brug for selskabets beslutning om kapitalnedsættelse og er ikke egnet til andre formål.{% endif %}

{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
