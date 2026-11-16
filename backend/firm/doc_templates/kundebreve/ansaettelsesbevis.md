---
{
  "title": "Ansættelsesbevis (ansættelseskontrakt)",
  "description": "Ansættelsesbevis efter lov om ansættelsesbeviser og visse arbejdsvilkår (lov nr. 501 af 16. maj 2023, gældende fra 1. juli 2023). Dækker alle oplysningspligter i § 3, inkl. funktionærer, overenskomst og uforudsigeligt arbejdsmønster.",
  "kind": "beslutning",
  "references": ["Ansættelsesbevisloven §§ 3-6 (lov nr. 501 af 16. maj 2023)", "Funktionærloven", "Ferieloven", "Arbejdstidsloven", "Lov om tidsbegrænset ansættelse", "Direktiv (EU) 2019/1152"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "medarbejder_navn", "label": "Medarbejderens navn", "type": "text"},
    {"name": "medarbejder_adresse", "label": "Medarbejderens adresse", "type": "textarea"},
    {"name": "stilling", "label": "Stilling/titel og kort beskrivelse af arbejdet", "type": "textarea"},
    {"name": "arbejdssted", "label": "Arbejdssted", "type": "text", "default": "{{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }}"},
    {"name": "skiftende_arbejdssted", "label": "Skiftende arbejdssteder / hjemmearbejde", "type": "checkbox"},
    {"name": "tiltraedelse", "label": "Tiltrædelsesdato", "type": "date"},
    {"name": "tidsbegraenset", "label": "Tidsbegrænset ansættelse – slutdato/forventet varighed", "type": "text"},
    {"name": "funktionaer", "label": "Medarbejderen er funktionær", "type": "checkbox", "default": true},
    {"name": "proevetid", "label": "Prøvetid (måneder, højst 6)", "type": "select", "options": ["Ingen", "1", "2", "3", "4", "5", "6"], "default": "3"},
    {"name": "loenform", "label": "Lønform", "type": "select", "options": ["Månedsløn", "Timeløn"], "default": "Månedsløn"},
    {"name": "loen", "label": "Løn (kr. pr. måned/time)", "type": "number"},
    {"name": "tillaeg", "label": "Tillæg, bonus, personalegoder", "type": "textarea"},
    {"name": "pension", "label": "Pension (arbejdsgiver/medarbejder %, pensionsselskab)", "type": "text"},
    {"name": "udbetaling", "label": "Lønudbetaling", "type": "select", "options": ["Bagud den sidste bankdag i måneden", "Forud den første bankdag i måneden", "Hver 14. dag"], "default": "Bagud den sidste bankdag i måneden"},
    {"name": "ugentlig_arbejdstid", "label": "Normal ugentlig arbejdstid (timer)", "type": "number", "default": "37"},
    {"name": "arbejdstid_placering", "label": "Arbejdstidens placering", "type": "text", "default": "Mandag til fredag inden for tidsrummet 8.00-17.00"},
    {"name": "overarbejde", "label": "Regler for overarbejde og betaling", "type": "textarea", "default": "Overarbejde udføres efter aftale og godtgøres med afspadsering eller betaling med tillæg."},
    {"name": "uforudsigeligt", "label": "Helt/overvejende uforudsigeligt arbejdsmønster (vagtplan)", "type": "checkbox"},
    {"name": "garanterede_timer", "label": "Garanterede betalte timer pr. uge/måned", "type": "text"},
    {"name": "referencetimer", "label": "Referencetimer og -dage, hvor der kan pålægges arbejde", "type": "text"},
    {"name": "varsel_vagt", "label": "Minimumsvarsel for vagter og frist for aflysning", "type": "text"},
    {"name": "overenskomst", "label": "Overenskomst (navn og parter) – tom hvis ingen", "type": "text"},
    {"name": "uddannelse", "label": "Ret til uddannelse", "type": "text", "default": "Medarbejderen deltager i den efteruddannelse, som stillingen kræver, efter aftale med virksomheden og for virksomhedens regning."},
    {"name": "opsigelse_varsel", "label": "Opsigelsesvarsler (ikke-funktionær)", "type": "text"},
    {"name": "tavshedspligt", "label": "Medtag tavshedspligt", "type": "checkbox", "default": true}
  ]
}
---
# Ansættelsesbevis

## 1. Parterne
**Arbejdsgiver:** {{ kunde.navn }}, CVR {{ kunde.cvr }}, {{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }}

**Medarbejder:** {{ felt.medarbejder_navn }}, {{ felt.medarbejder_adresse }}

## 2. Arbejdssted
Arbejdsstedet er {{ felt.arbejdssted }}.{% if felt.skiftende_arbejdssted %} Medarbejderen arbejder på skiftende arbejdssteder{% if branche.byggeri %} (byggepladser){% endif %}{% if branche.rengoering %} (kundeadresser){% endif %}{% if branche.transport %} (kørsel i ind- og udland){% endif %}, eller kan delvist arbejde hjemmefra efter aftale. Arbejdsgiverens adresse er {{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }}.{% endif %}

## 3. Stilling og arbejdsopgaver
{{ felt.stilling }}

## 4. Tiltrædelse og varighed
Ansættelsen begynder den **{{ felt.tiltraedelse }}**.
{% if felt.tidsbegraenset %}Ansættelsen er tidsbegrænset og ophører uden yderligere varsel: {{ felt.tidsbegraenset }}.{% else %}Ansættelsen er tidsubegrænset.{% endif %}

## 5. Prøvetid
{% if felt.proevetid == "Ingen" %}Der er ingen prøvetid.{% else %}De første {{ felt.proevetid }} måneder af ansættelsen er prøvetid. Prøvetiden kan ikke overstige 6 måneder{% if felt.tidsbegraenset %} og står i forhold til ansættelsens forventede varighed og arbejdets art{% endif %} (ansættelsesbevisloven § 6).{% if felt.funktionaer %} Inden for de første 3 måneder af ansættelsen kan arbejdsgiveren opsige med 14 dages varsel til fratræden en hvilken som helst dag (funktionærloven § 2, stk. 5). Medarbejderens varsel er også i prøvetiden 1 måned til en måneds udgang.{% endif %}{% endif %}

## 6. Løn
{% if felt.loenform == "Månedsløn" %}Lønnen udgør **{{ felt.loen }} kr. pr. måned**{% else %}Lønnen udgør **{{ felt.loen }} kr. pr. time**{% endif %} og udbetales {{ felt.udbetaling|lower }} til medarbejderens NemKonto.{% if felt.loenform == "Månedsløn" and not felt.overenskomst %} Herudover betales et tillæg på 0,45 % af den årlige løn som kompensation for afskaffelsen af store bededag.{% endif %} Lønnen forhandles {% if felt.overenskomst %}efter overenskomsten{% else %}en gang årligt med virkning fra 1. april uden forpligtelse til forhøjelse{% endif %}.

Tillæg, bonus og personalegoder: {{ felt.tillaeg }}

**Pension:** {{ felt.pension }}

## 7. Arbejdstid
Den normale ugentlige arbejdstid er **{{ felt.ugentlig_arbejdstid }} timer** ekskl. frokostpause. Placering: {{ felt.arbejdstid_placering }}.

**Overarbejde:** {{ felt.overarbejde }} Den gennemsnitlige ugentlige arbejdstid inkl. overarbejde må ikke overstige 48 timer over en referenceperiode på 4 måneder (arbejdstidsloven).
{% if felt.uforudsigeligt %}
**Variabelt arbejdsmønster (ansættelsesbevisloven § 3, stk. 2, nr. 12):** Arbejdstiden fastlægges i en vagtplan, der varierer.
- Garanterede betalte timer: {{ felt.garanterede_timer }}
- Arbejde ud over de garanterede timer betales med den aftalte timeløn{% if felt.overenskomst %} og tillæg efter overenskomsten{% endif %}.
- Referencetimer og -dage, hvor der kan pålægges arbejde: {{ felt.referencetimer }}
- Minimumsvarsel for arbejdsopgaver og frist for aflysning: {{ felt.varsel_vagt }}
{% endif %}
## 8. Ferie og fravær med løn
Medarbejderen har ret til 25 dages betalt ferie om året efter ferieloven (samtidighedsferie: 2,08 dage optjenes pr. måneds ansættelse). {% if felt.loenform == "Månedsløn" %}Der betales løn under ferie og et ferietillæg på 1 % af den ferieberettigede løn.{% else %}Der optjenes feriegodtgørelse på 12,5 % af den ferieberettigede løn.{% endif %}{% if felt.overenskomst %} Feriefridage gives efter overenskomsten.{% endif %} Ferie varsles og afholdes efter ferielovens regler (hovedferie 3 uger i perioden 1. maj – 30. september med 3 måneders varsel, øvrig ferie med 1 måneds varsel).

Sygdom: Medarbejderen skal give besked om sygdom hurtigst muligt og senest ved arbejdstids begyndelse. {% if felt.funktionaer %}Medarbejderen er som funktionær berettiget til fuld løn under sygdom (funktionærloven § 5).{% else %}Der betales sygedagpenge efter sygedagpengeloven{% if felt.overenskomst %} og løn under sygdom efter overenskomsten{% endif %}.{% endif %} Barsel og omsorgsfravær følger barselsloven{% if felt.overenskomst %} og overenskomsten{% endif %}.

## 9. Opsigelse
{% if felt.funktionaer %}Ansættelsesforholdet er omfattet af **funktionærloven**. Arbejdsgiverens opsigelsesvarsel er (efter prøvetid) 1 måned til fratræden ved en måneds udgang inden 6 måneders ansættelse, 3 måneder efter 6 måneder, og forlænges med 1 måned for hver 3 års ansættelse op til 6 måneder (funktionærloven § 2). Medarbejderen kan opsige med 1 måneds varsel til en måneds udgang. Ved opsigelse efter 12, 15 eller 18 års ansættelse gælder funktionærlovens regler om fratrædelsesgodtgørelse (§ 2 a).{% else %}Opsigelse sker med følgende varsler: {{ felt.opsigelse_varsel }}{% if felt.overenskomst %} – i øvrigt efter overenskomsten{% endif %}.{% endif %} Opsigelse skal ske skriftligt.

## 10. Overenskomst
{% if felt.overenskomst %}Ansættelsesforholdet er omfattet af {{ felt.overenskomst }}. Overenskomstens bestemmelser gælder, hvor de giver medarbejderen bedre vilkår end dette ansættelsesbevis.{% else %}Ansættelsesforholdet er ikke omfattet af en kollektiv overenskomst.{% endif %}

## 11. Uddannelse
{{ felt.uddannelse }}

## 12. Sociale bidrag og forsikringer
Arbejdsgiveren indbetaler ATP-bidrag og bidrag til arbejdsmarkedets ordninger (AES/AUB, Barsel.dk m.fl.) og har tegnet lovpligtig arbejdsskadeforsikring. A-skat og AM-bidrag indeholdes og indbetales til Skattestyrelsen.{% if felt.pension %} Pensionsbidrag indbetales til pensionsselskabet som anført i pkt. 6.{% endif %}

{% if felt.tavshedspligt %}## 13. Tavshedspligt
Medarbejderen har under og efter ansættelsen tavshedspligt om forhold, der kommer til medarbejderens kendskab gennem arbejdet, og som efter deres natur bør hemmeligholdes, herunder forretningshemmeligheder (lov om forretningshemmeligheder) og personoplysninger.
{% endif %}
## Øvrigt
Ændringer i de vilkår, der er beskrevet her, meddeles skriftligt hurtigst muligt og senest den dag, ændringen træder i kraft (ansættelsesbevisloven § 5), medmindre ændringen alene følger af lov eller overenskomst. Medarbejderen kan efter 6 måneders ansættelse anmode om en ansættelsesform med mere forudsigelige og sikre arbejdsvilkår og skal have et begrundet skriftligt svar inden for 1 måned.

Dato: ______________________

______________________________________
for {{ kunde.navn }}

______________________________________
{{ felt.medarbejder_navn }}

*Ansættelsesbeviset er udleveret senest 7 kalenderdage efter tiltrædelse for så vidt angår pkt. 1-7 og senest 1 måned efter tiltrædelse for de øvrige punkter (ansættelsesbevisloven § 3, stk. 1). Udarbejdet med bistand fra {{ firma.navn }}.*
