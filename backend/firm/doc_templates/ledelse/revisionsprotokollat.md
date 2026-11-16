---
{
  "title": "Revisionsprotokollat til bestyrelsen – revision af årsrapport",
  "description": "Protokollat til revisionsprotokollen for selskaber med bestyrelse (A/S og ApS med bestyrelse). Revisorlovens § 20 om revisionsprotokollat gælder kun virksomheder af interesse for offentligheden; fører revisor en revisionsprotokol, underskrives den af det øverste ledelsesorgans medlemmer (selskabsloven § 129). Indeholder revisionens omfang og konklusion, væsentlighed, betydelige risici (branchetilpasset), intern kontrol, besvigelser, oplysninger om uafhængighed og modtagne oplysninger samt bestyrelsens underskrift. Opfylder samtidig ISA 260 og ISA 265.",
  "kind": "brev",
  "references": ["Revisorloven § 20 (kun virksomheder af interesse for offentligheden) og § 22 (LBK nr. 206 af 20/02/2025)", "Selskabsloven § 129", "ISA 260", "ISA 265", "ISA 450", "ISA 240", "ISA 570", "Selskabsloven §§ 115 og 117", "Erklæringsbekendtgørelsen"],
  "legal_forms": ["as", "aps", "holding", "fmba", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "protokol_nr", "label": "Protokollatets nummer/sidenummerering (fortløbende)", "type": "text"},
    {"name": "moede_dato", "label": "Dato for bestyrelsesmødet", "type": "text"},
    {"name": "paategning", "label": "Påtegningens udformning", "type": "select", "options": ["uden modifikation", "uden modifikation, men med fremhævelse af forhold", "uden modifikation, men med supplerende oplysninger", "med forbehold", "med afkræftende konklusion", "med manglende konklusion"], "default": "uden modifikation"},
    {"name": "paategning_forklaring", "label": "Forklaring til modifikation/fremhævelse/supplerende oplysninger", "type": "textarea"},
    {"name": "vaesentlighed", "label": "Væsentlighedsniveau for regnskabet som helhed (kr.)", "type": "number"},
    {"name": "vaesentlighed_grundlag", "label": "Grundlag for væsentlighed (fx 1 % af omsætningen)", "type": "text"},
    {"name": "ubetydelig", "label": "Grænse for åbenlyst ubetydelige fejl (kr.)", "type": "number"},
    {"name": "risici_ekstra", "label": "Øvrige betydelige risici og vores handlinger (valgfrit)", "type": "textarea"},
    {"name": "korrigerede_fejl", "label": "Væsentlige korrektioner foretaget efter vores forslag", "type": "textarea"},
    {"name": "ukorrigerede_fejl", "label": "Ukorrigerede fejl (beskrivelse og virkning, tom = ingen)", "type": "textarea"},
    {"name": "intern_kontrol", "label": "Observationer om intern kontrol og it (tom = ingen væsentlige)", "type": "textarea"},
    {"name": "andre_ydelser", "label": "Andre ydelser end revision leveret i året", "type": "textarea"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "sted", "label": "Sted", "type": "text"}
  ]
}
---
# Revisionsprotokol – {{ kunde.navn }}

**Protokollat vedrørende revision af årsrapporten for {{ regnskab.aar }}**
Side {{ felt.protokol_nr }}

## 1. Indledning

Vi har afsluttet revisionen af årsrapporten for {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}, for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}, som ledelsen har aflagt i overensstemmelse med årsregnskabsloven (regnskabsklasse {{ kunde.regnskabsklasse }}).

Protokollatet indeholder vores rapportering til bestyrelsen om revisionens formål, omfang og resultat samt om de forhold, vi er forpligtet til at rapportere efter revisorloven og de internationale standarder om revision. Protokollatet skal læses sammen med opdragsbrevet og vores tidligere protokollater.

## 2. Konklusion på revisionen

{% if felt.paategning == "med forbehold" or felt.paategning == "med afkræftende konklusion" or felt.paategning == "med manglende konklusion" %}Revisionen har givet anledning til en modificeret konklusion, jf. nedenfor.{% else %}Revisionen har ikke givet anledning til forbehold.{% endif %} Vi forventer at forsyne årsrapporten med en revisionspåtegning {{ felt.paategning }}.

{% if felt.paategning_forklaring %}{{ felt.paategning_forklaring }}

{% endif %}Vi har læst ledelsesberetningen. Den er i overensstemmelse med årsregnskabet og udarbejdet i overensstemmelse med årsregnskabslovens krav, og vi har ikke fundet væsentlig fejlinformation i den.

## 3. Revisionens formål og omfang

Revisionen er udført i overensstemmelse med internationale standarder om revision og de yderligere krav, der er gældende i Danmark, med henblik på at opnå høj grad af sikkerhed for, at årsregnskabet som helhed ikke indeholder væsentlig fejlinformation. Revisionen er risikobaseret og tilrettelagt ud fra vores forståelse af selskabet, dets forretningsmodel og interne kontrol. Revisionen har omfattet de væsentlige processer og regnskabsposter og er udført ved en kombination af test af kontroller, analytiske handlinger og detailtest af transaktioner og saldi.

Revisionen er ikke tilrettelagt med henblik på at afdække alle fejl og uregelmæssigheder, men vi har tilrettelagt den således, at der er høj sandsynlighed for at opdage væsentlige fejl, herunder væsentlige fejl som følge af besvigelser.

## 4. Væsentlighed

Vi har fastsat væsentlighedsniveauet for årsregnskabet som helhed til {{ felt.vaesentlighed }} kr. ({{ felt.vaesentlighed_grundlag }}). Fejl under {{ felt.ubetydelig }} kr. anses som åbenlyst ubetydelige og akkumuleres ikke. Vi har desuden vurderet forhold, der er kvalitativt væsentlige, uanset beløb, fx transaktioner med ledelse og kapitalejere.

## 5. Betydelige risici og vores revisionsmæssige reaktion

**Ledelsens tilsidesættelse af kontroller.** Vi har gennemgået manuelle posteringer og reguleringer ved periodeafslutningen, vurderet væsentlige regnskabsmæssige skøn for tendenser og gennemgået usædvanlige transaktioner. Vi har ikke konstateret forhold, der indikerer tilsidesættelse af kontroller.

**Indregning af omsætning.** Vi har testet periodeafgrænsning, afstemt omsætningen til momsangivelser og gennemført analytiske handlinger på omsætning og bruttoavance.{% if branche.kontantintensiv %} På grund af det betydelige kontantsalg har vi særligt testet kasseafstemninger, z-rapporter, bankindsætninger og sammenhængen mellem vareforbrug og omsætning.{% endif %}

{% if branche.lager %}**Varelager.** Vi har overværet lageroptællingen pr. {{ regnskab.slut }}, testet kostpriser til fakturaer og vurderet ledelsens nedskrivning af ukurante varer og nettorealisationsværdier.

{% endif %}{% if branche.igangvaerende_arbejder %}**Igangværende arbejder.** Vi har for udvalgte projekter testet færdiggørelsesgrad, forventede restomkostninger og indtjening, sammenholdt med efterkalkulationer på afsluttede projekter og vurderet behovet for tabshensættelser.

{% endif %}{% if branche.investeringsejendomme %}**Måling af investeringsejendomme.** Vi har vurderet afkastmodellen, afstemt lejeindtægter til lejekontrakter, vurderet afkastkravet i forhold til markedsdata og testet beregningen af dagsværdireguleringer og udskudt skat.

{% endif %}{% if branche.momsfritaget %}**Moms og lønsumsafgift.** Vi har gennemgået opgørelsen af delvis fradragsret, årsregulering og lønsumsafgift.

{% endif %}{% if branche.landbrug %}**Biologiske aktiver og landbrugsstøtte.** Vi har vurderet optælling og måling af besætninger og afgrøder samt indregning af støtteordninger.

{% endif %}{% if felt.risici_ekstra %}{{ felt.risici_ekstra }}

{% endif %}## 6. Regnskabspraksis, skøn og fortsat drift

Den anvendte regnskabspraksis er uændret i forhold til sidste år og passende for selskabet. De væsentlige regnskabsmæssige skøn er efter vores vurdering rimelige og tilstrækkeligt oplyst. Vi er enige i ledelsens vurdering af, at årsregnskabet kan aflægges under forudsætning af fortsat drift.

## 7. Korrektioner og ikke-korrigerede fejl

{% if felt.korrigerede_fejl %}Følgende væsentlige korrektioner er foretaget på vores foranledning: {{ felt.korrigerede_fejl }}

{% endif %}{% if felt.ukorrigerede_fejl %}Ledelsen har valgt ikke at korrigere følgende fejl, som efter ledelsens og vores vurdering er uvæsentlige for årsregnskabet som helhed: {{ felt.ukorrigerede_fejl }} Oversigten er vedlagt ledelseserklæringen.{% else %}Der er ingen ikke-korrigerede fejl ud over åbenlyst ubetydelige forhold.{% endif %}

## 8. Intern kontrol, it og bogføring

{% if felt.intern_kontrol %}{{ felt.intern_kontrol }}{% else %}Vi har under revisionen ikke konstateret betydelige mangler i den interne kontrol eller i it-sikkerheden. Bogføringen er efter vores vurdering ført i overensstemmelse med bogføringsloven.{% endif %}

## 9. Besvigelser, lovgivning og nærtstående parter

Vi har forespurgt bestyrelsen og direktionen om kendskab til besvigelser eller mistanke herom samt om overholdelse af love og øvrig regulering. Vi er ikke blevet bekendt med besvigelser, væsentlige overtrædelser af lovgivningen eller transaktioner med nærtstående parter, som ikke er behandlet korrekt i årsregnskabet. Vi har ikke konstateret lån eller sikkerhedsstillelser til kapitalejere eller ledelse, som ikke er i selskabets interesse eller er uforsvarlige, jf. selskabslovens §§ 115-118 og 127, eller ikke-tilbagebetalte lån ydet før 1. januar 2025 i strid med de dagældende regler i selskabslovens § 210.

## 10. Bestyrelsens og direktionens ansvar

Vi henleder bestyrelsens opmærksomhed på, at bestyrelsen efter selskabslovens § 115 skal sikre en forsvarlig organisation af selskabets virksomhed, at bogføring og regnskabsaflæggelse er tilrettelagt tilfredsstillende, at der er etableret de nødvendige procedurer for risikostyring og interne kontroller, at bestyrelsen løbende modtager den nødvendige rapportering om selskabets finansielle forhold, og at direktionen udøver sit hverv på behørig måde. Bestyrelsen skal endvidere løbende vurdere, om selskabets kapitalberedskab og likviditet er forsvarligt.

## 11. Ledelseserklæring

Vi har i overensstemmelse med ISA 580 indhentet en skriftlig ledelseserklæring fra bestyrelsen og direktionen, som underskrives samtidig med årsrapporten.

## 12. Uafhængighed og modtagne oplysninger

Vi oplyser:

- at vi opfylder lovgivningens krav til uafhængighed, og at vi ikke har ydet ydelser, der er uforenelige med uafhængigheden;
- at vi under revisionen har modtaget alle de oplysninger, vi har anmodet om;
- at revisionen ikke har givet anledning til andre bemærkninger end dem, der fremgår af dette protokollat.

{% if felt.andre_ydelser %}Vi har i regnskabsåret ud over revisionen leveret følgende ydelser: {{ felt.andre_ydelser }} Ydelserne er vurderet i forhold til uafhængighedsreglerne og er ikke fundet at true vores uafhængighed.

{% endif %}{{ felt.sted }}, den {{ dato.idag }}

**{{ firma.navn }}**

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}

## Bestyrelsens underskrift

Forelagt på bestyrelsesmødet den {{ felt.moede_dato }}. Bestyrelsens medlemmer underskriver revisionsprotokollen, jf. selskabslovens § 129, og bekræfter herved at have gjort sig bekendt med indholdet af dette protokollat.

______________________________ (formand)

______________________________

______________________________
