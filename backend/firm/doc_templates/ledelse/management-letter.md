---
{
  "title": "Management letter – anbefalinger til ledelsen",
  "description": "Brev med revisors anbefalinger til forbedringer af bogføring, intern kontrol, it, likviditetsstyring, moms og løn. Kan bruges efter revision, udvidet gennemgang, review eller opstilling. Prioriteret oversigt med ansvar og frist samt branchespecifikke anbefalinger.",
  "kind": "brev",
  "references": ["ISA 265, afsnit 10, litra b (andre mangler)", "Bogføringsloven (lov nr. 700 af 24/05/2022)", "Selskabsloven §§ 115-118 og 127", "Ligningsloven § 16 E", "Momsloven", "Hvidvaskloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "opgave", "label": "Opgavetype", "type": "select", "options": ["revision", "udvidet gennemgang", "review", "opstilling"], "default": "revision"},
    {"name": "a1", "label": "Anbefaling 1 (observation og anbefaling)", "type": "textarea"},
    {"name": "a1_prioritet", "label": "Anbefaling 1 – prioritet", "type": "select", "options": ["Høj", "Middel", "Lav"], "default": "Høj"},
    {"name": "a2", "label": "Anbefaling 2", "type": "textarea"},
    {"name": "a2_prioritet", "label": "Anbefaling 2 – prioritet", "type": "select", "options": ["Høj", "Middel", "Lav"], "default": "Middel"},
    {"name": "a3", "label": "Anbefaling 3", "type": "textarea"},
    {"name": "a3_prioritet", "label": "Anbefaling 3 – prioritet", "type": "select", "options": ["Høj", "Middel", "Lav"], "default": "Middel"},
    {"name": "standardanbefalinger", "label": "Medtag generelle anbefalinger (afstemninger, adgange, digital bogføring m.v.)", "type": "checkbox", "default": true},
    {"name": "opfoelgning_sidste_aar", "label": "Status på sidste års anbefalinger (valgfrit)", "type": "textarea"},
    {"name": "revisor_titel", "label": "Underskrivers titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor", "revisor", "regnskabschef"], "default": "statsautoriseret revisor"}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Anbefalinger efter {{ felt.opgave }} af årsregnskabet for {{ regnskab.aar }}

I forbindelse med vores {{ felt.opgave }} af årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} har vi gjort nogle observationer, som vi med dette brev giver videre som anbefalinger. Formålet er at hjælpe jer med at styrke bogføringen og den interne kontrol, mindske risikoen for fejl og besvigelser og gøre årsafslutningen hurtigere og billigere.

Observationerne er ikke udtryk for en fuldstændig gennemgang af {% if kunde.er_kapitalselskab %}selskabets{% else %}virksomhedens{% endif %} interne kontrol{% if felt.opgave == "revision" %}, og de påvirker ikke vores revisionspåtegning{% endif %}. Betydelige mangler i den interne kontrol meddeles særskilt.

## Prioriterede anbefalinger

| Nr. | Observation og anbefaling | Prioritet |
|---|---|---|
{% if felt.a1 %}| 1 | {{ felt.a1 }} | {{ felt.a1_prioritet }} |
{% endif %}{% if felt.a2 %}| 2 | {{ felt.a2 }} | {{ felt.a2_prioritet }} |
{% endif %}{% if felt.a3 %}| 3 | {{ felt.a3 }} | {{ felt.a3_prioritet }} |
{% endif %}
{% if felt.standardanbefalinger %}## Generelle anbefalinger

- **Månedlige afstemninger:** Afstem bank, debitorer, kreditorer, moms og skyldig A-skat/AM-bidrag hver måned, og lad en anden end bogholderen gennemse afstemningerne.
- **Godkendelse af betalinger:** Indfør to-personers godkendelse i netbanken for betalinger over en fastsat beløbsgrænse, og fjern adgange for fratrådte medarbejdere straks.
- **Digital bogføring og opbevaring:** Sørg for, at bogføringssystemet opfylder bogføringslovens krav til digitale bogføringssystemer, at alle bilag registreres løbende, og at regnskabsmaterialet opbevares sikkert i 5 år.
- **It-sikkerhed:** Brug to-faktor-login til bank, bogføring og e-mail, tag løbende backup, og vær opmærksom på falske betalingsanmodninger (CEO-svindel).
- **Likviditet og budget:** Udarbejd et årligt budget og en løbende likviditetsprognose, og følg op på afvigelser kvartalsvis.
{% if kunde.er_kapitalselskab %}- **Mellemregning med ejere og ledelse:** Undgå private udgifter afholdt af selskabet. Forbuddet mod kapitalejerlån i selskabslovens § 210 er ophævet pr. 1. januar 2025, men lån til kapitalejere og ledelse skal fortsat være i selskabets interesse og forsvarlige (selskabslovens §§ 115-118 og 127), og lån til personlige kapitalejere og disses nærtstående kan blive beskattet efter ligningslovens § 16 E. Ældre lån ydet i strid med de tidligere regler er fortsat ulovlige og omfattet af tilbagebetalingspligten i den dagældende § 215.
{% endif %}{% endif %}
{% if branche.lager or branche.igangvaerende_arbejder or branche.kontantintensiv or branche.momsfritaget or branche.investeringsejendomme or branche.landbrug or branche.byggeri or branche.restauration %}## Branchespecifikke anbefalinger

{% if branche.lager %}- **Varelager:** Indfør løbende lagerstyring med cyklisk optælling, og gennemgå varer uden bevægelse i de seneste 12 måneder for ukurans. Dokumentér optællingen pr. balancedagen med lister, der underskrives af optæller.
{% endif %}{% if branche.igangvaerende_arbejder %}- **Projekter:** Registrér timer og materialer pr. projekt, lav efterkalkulation på afsluttede projekter, og vurdér hvert kvartal færdiggørelsesgrad og risiko for tab.
{% endif %}{% if branche.byggeri %}- **Byggeri:** Kontrollér omvendt betalingspligt for moms ved køb af ydelser vedrørende fast ejendom fra udenlandske leverandører (momslovens § 46, stk. 1, nr. 3), og hold styr på sikkerhedsstillelser og garantiperioder efter aftalegrundlaget.
{% endif %}{% if branche.kontantintensiv %}- **Kontantsalg:** Lav daglig kasseafstemning med z-rapport, sæt kontanter i banken løbende, og analysér bruttoavancen månedligt. Overhold hvidvasklovens kontantforbud.
{% endif %}{% if branche.restauration %}- **Restauration:** Sørg for korrekt registrering af drikkepenge og personaleforplejning, og afstem kortindbetalinger og leveringsplatforme til omsætningen.
{% endif %}{% if branche.momsfritaget %}- **Moms:** Dokumentér fordelingen mellem momspligtig og momsfritaget aktivitet, beregn fradragsprocenten korrekt, og husk årsregulering og lønsumsafgift.
{% endif %}{% if branche.investeringsejendomme %}- **Ejendomme:** Før en lejeliste med lejeregulering, depositum og tomgang, og dokumentér forudsætningerne for dagsværdien hvert år.
{% endif %}{% if branche.landbrug %}- **Landbrug:** Før registre over besætninger og beholdninger, og dokumentér overholdelse af betingelser for landbrugsstøtte.
{% endif %}
{% endif %}{% if felt.opfoelgning_sidste_aar %}## Opfølgning på sidste års anbefalinger

{{ felt.opfoelgning_sidste_aar }}

{% endif %}Vi drøfter gerne anbefalingerne med jer og kan bistå med at gennemføre dem.

Med venlig hilsen

**{{ firma.navn }}**

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
