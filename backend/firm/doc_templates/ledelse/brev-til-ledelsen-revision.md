---
{
  "title": "Brev til ledelsen efter revision (ApS uden bestyrelse)",
  "description": "Afsluttende revisionsbrev til direktionen i selskaber uden bestyrelse, hvor der ikke føres revisionsprotokol. Opfylder kommunikationskravene i ISA 260 og ISA 265: påtegning, væsentlighed, risici, fejl, intern kontrol, uafhængighed og ledelsens ansvar.",
  "kind": "brev",
  "references": ["ISA 260", "ISA 265", "ISA 450", "Revisorloven §§ 16 og 24 (LBK nr. 206 af 20/02/2025)", "Selskabsloven §§ 115-118 og 127", "Ligningsloven § 16 E"],
  "legal_forms": ["aps", "ivs", "holding", "pmv", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "paategning", "label": "Påtegningens udformning", "type": "select", "options": ["uden modifikation", "uden modifikation, men med fremhævelse af forhold", "uden modifikation, men med supplerende oplysninger", "med forbehold", "med afkræftende konklusion", "med manglende konklusion"], "default": "uden modifikation"},
    {"name": "paategning_forklaring", "label": "Forklaring (hvis ikke uden modifikation)", "type": "textarea"},
    {"name": "vaesentlighed", "label": "Væsentlighed (kr.)", "type": "number"},
    {"name": "observationer", "label": "Vores væsentligste observationer (tekst eller punkter)", "type": "textarea"},
    {"name": "ukorrigerede_fejl", "label": "Ukorrigerede fejl (tom = ingen)", "type": "textarea"},
    {"name": "intern_kontrol", "label": "Mangler i intern kontrol (tom = ingen betydelige)", "type": "textarea"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Afslutning af revisionen af årsrapporten for {{ regnskab.aar }}

Vi har afsluttet revisionen af årsrapporten for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}. Da selskabet ikke har en bestyrelse, føres der ikke revisionsprotokol, og vi giver i stedet med dette brev direktionen vores rapportering om revisionen.

## Revisionens resultat

Vi forventer at forsyne årsrapporten med en revisionspåtegning {{ felt.paategning }}.{% if felt.paategning_forklaring %} {{ felt.paategning_forklaring }}{% endif %}

Revisionen er udført i overensstemmelse med internationale standarder om revision og de yderligere krav, der er gældende i Danmark, med henblik på at opnå høj grad af sikkerhed for, at årsregnskabet ikke indeholder væsentlig fejlinformation. Vi har anvendt et væsentlighedsniveau på {{ felt.vaesentlighed }} kr.

## Væsentlige områder

Revisionen har særligt været rettet mod indregning af omsætning, ledelsens tilsidesættelse af kontroller og de regnskabsposter, der er forbundet med skøn{% if branche.lager %}, herunder varelagerets optælling og måling{% endif %}{% if branche.igangvaerende_arbejder %}, igangværende arbejder og tabsgivende projekter{% endif %}{% if branche.investeringsejendomme %}, dagsværdien af investeringsejendomme{% endif %}{% if branche.kontantintensiv %}, fuldstændigheden af kontantsalget{% endif %}{% if branche.momsfritaget %}, delvis momsfradrag og lønsumsafgift{% endif %}.

{% if felt.observationer %}{{ felt.observationer }}

{% endif %}## Fejl og korrektioner

{% if felt.ukorrigerede_fejl %}Følgende fejl er ikke korrigeret, idet de efter ledelsens og vores vurdering er uvæsentlige for årsregnskabet som helhed: {{ felt.ukorrigerede_fejl }}{% else %}Alle de korrektioner, vi har foreslået, er indarbejdet i årsregnskabet.{% endif %}

## Intern kontrol

{% if felt.intern_kontrol %}{{ felt.intern_kontrol }}{% else %}Vi har ikke konstateret betydelige mangler i den interne kontrol. Vi gør dog opmærksom på, at funktionsadskillelsen i en mindre virksomhed naturligt er begrænset, og at direktionens løbende opfølgning på bogføring, afstemninger og betalinger derfor er en vigtig kontrol.{% endif %}

## Direktionens ansvar

Vi minder om, at direktionen efter selskabslovens § 117 forestår den daglige ledelse og skal sørge for, at bogføringen sker i overensstemmelse med lovgivningen, og at formueforvaltningen foregår forsvarligt. Direktionen skal desuden løbende sikre, at selskabets kapitalberedskab og likviditet er forsvarligt, og at eventuelle lån til kapitalejere og ledelse er i selskabets interesse og forsvarlige. Vi gør opmærksom på, at sådanne lån til personlige kapitalejere beskattes efter ligningslovens § 16 E.

## Uafhængighed

Vi bekræfter, at vi er uafhængige af selskabet i overensstemmelse med revisorloven og IESBA Code, og at vi har modtaget alle de oplysninger, vi har anmodet om.

Vi står gerne til rådighed for en gennemgang af årsrapporten og af dette brev.

Med venlig hilsen

**{{ firma.navn }}**

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
