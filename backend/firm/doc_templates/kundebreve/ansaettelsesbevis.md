---
{
  "title": "Ansættelsesbevis (ansættelseskontrakt)",
  "description": "Ansættelsesbevis efter lov om ansættelsesbeviser og visse arbejdsvilkår (lov nr. 501 af 16. maj 2023, gældende fra 1. juli 2023). Dækker alle oplysningspligter i § 3, inkl. funktionærer, overenskomst og uforudsigeligt arbejdsmønster.",
  "kind": "beslutning",
  "references": ["Ansættelsesbevisloven §§ 3, 5, 6, 10 og 11 (lov nr. 501 af 16. maj 2023)", "Funktionærloven (LBK nr. 1002 af 24. august 2017) §§ 2, 2 a, 5", "Ferieloven (LBK nr. 152 af 20. februar 2024)", "Arbejdstidsloven (LBK nr. 982 af 12. august 2024) § 4", "Lov nr. 214 af 6. marts 2023 (store bededag) § 3", "Lov om tidsbegrænset ansættelse", "Direktiv (EU) 2019/1152"],
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
    {"name": "proevetid_varsel_medarbejder", "label": "Medarbejderens opsigelsesvarsel i prøvetiden (funktionær, udfyldes af rådgiver)", "type": "text"},
    {"name": "loenform", "label": "Lønform", "type": "select", "options": ["Månedsløn", "Timeløn"], "default": "Månedsløn"},
    {"name": "loen", "label": "Løn (kr. pr. måned/time)", "type": "number"},
    {"name": "bededag_afregning", "label": "Afregning af store bededag-tillæg (fast løn)", "type": "select", "options": ["Sammen med lønnen for maj og august", "Løbende med lønudbetalingen"], "default": "Sammen med lønnen for maj og august"},
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
    {"name": "arbejdsskadeforsikring", "label": "Arbejdsskadeforsikring (forsikringsselskab)", "type": "text"},
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
{% if felt.proevetid == "Ingen" %}Der er ingen prøvetid.{% else %}De første {{ felt.proevetid }} måneder af ansættelsen er prøvetid. Prøvetiden kan ikke overstige 6 måneder{% if felt.tidsbegraenset %} og ved tidsbegrænset ansættelse ikke en fjerdedel af ansættelsestiden{% endif %} (ansættelsesbevisloven § 6).{% if felt.funktionaer %} Er ansættelsen på prøve og vedvarer den ikke ud over 3 måneder, kan arbejdsgiveren opsige med mindst 14 dages varsel (funktionærloven § 2, stk. 5). Funktionærlovens regel om 1 måneds varsel fra medarbejderens side gælder ikke, når ansættelsen er på prøve og ikke vedvarer ud over 3 måneder (funktionærloven § 2, stk. 6); medarbejderens varsel i denne periode er: {{ felt.proevetid_varsel_medarbejder }}.{% endif %}{% endif %}

## 6. Løn
{% if felt.loenform == "Månedsløn" %}Lønnen udgør **{{ felt.loen }} kr. pr. måned**{% else %}Lønnen udgør **{{ felt.loen }} kr. pr. time**{% endif %} og udbetales {{ felt.udbetaling|lower }} til medarbejderens NemKonto.{% if felt.loenform == "Månedsløn" %} Herudover betales et løntillæg på 0,45 % af årslønnen som følge af afskaffelsen af store bededag som helligdag (lov nr. 214 af 6. marts 2023, § 3). Tillægget afregnes {{ felt.bededag_afregning|lower }}.{% endif %} Lønnen forhandles {% if felt.overenskomst %}efter overenskomsten{% else %}en gang årligt med virkning fra 1. april uden forpligtelse til forhøjelse{% endif %}.

Tillæg, bonus og personalegoder: {{ felt.tillaeg }}

**Pension:** {{ felt.pension }}

## 7. Arbejdstid
Den normale ugentlige arbejdstid er **{{ felt.ugentlig_arbejdstid }} timer** ekskl. frokostpause. Placering: {{ felt.arbejdstid_placering }}.

**Overarbejde:** {{ felt.overarbejde }} Den gennemsnitlige ugentlige arbejdstid inkl. overarbejde må ikke overstige 48 timer beregnet over en periode på 4 måneder (arbejdstidsloven § 4).
{% if felt.uforudsigeligt %}
**Variabelt arbejdsmønster (ansættelsesbevisloven § 3, stk. 2, nr. 12):** Arbejdstiden fastlægges i en vagtplan, der varierer.
- Garanterede betalte timer: {{ felt.garanterede_timer }}
- Arbejde ud over de garanterede timer betales med den aftalte timeløn{% if felt.overenskomst %} og tillæg efter overenskomsten{% endif %}.
- Referencetimer og -dage, hvor der kan pålægges arbejde: {{ felt.referencetimer }}
- Minimumsvarsel for arbejdsopgaver og frist for aflysning: {{ felt.varsel_vagt }}
{% endif %}
## 8. Ferie og fravær med løn
Medarbejderen har ret til 25 dages betalt ferie om året efter ferieloven (samtidighedsferie: 2,08 dage optjenes pr. måneds ansættelse). {% if felt.loenform == "Månedsløn" %}Der betales løn under ferie og et ferietillæg på 1 % af den ferieberettigede løn.{% else %}Der optjenes feriegodtgørelse på 12,5 % af den ferieberettigede løn.{% endif %}{% if felt.overenskomst %} Feriefridage gives efter overenskomsten.{% endif %} Ferie varsles og afholdes efter ferielovens regler (hovedferie 3 uger i perioden 1. maj – 30. september med 3 måneders varsel, øvrig ferie med 1 måneds varsel).

Sygdom: Medarbejderen skal give besked om sygdom hurtigst muligt og senest ved arbejdstids begyndelse. {% if felt.funktionaer %}Sygdom anses som lovligt forfald, og medarbejderen oppebærer som funktionær løn under sygdom (funktionærloven § 5).{% else %}Der betales sygedagpenge efter sygedagpengeloven{% if felt.overenskomst %} og løn under sygdom efter overenskomsten{% endif %}.{% endif %} Barsel og omsorgsfravær følger barselsloven{% if felt.overenskomst %} og overenskomsten{% endif %}.

## 9. Opsigelse
{% if felt.funktionaer %}Ansættelsesforholdet er omfattet af **funktionærloven**. Arbejdsgiverens opsigelsesvarsel er mindst 1 måned til fratræden ved en måneds udgang i de første 6 måneder efter ansættelsen og 3 måneder til fratræden ved en måneds udgang efter 6 måneders ansættelse; varslet forhøjes med 1 måned for hvert tredje ansættelsesår, dog højst til 6 måneder (funktionærloven § 2, stk. 2-3). Medarbejderen kan opsige med 1 måneds varsel til ophør ved en måneds udgang (§ 2, stk. 6). Opsiges en funktionær, der har været uafbrudt beskæftiget i virksomheden i 12 eller 17 år, betales ved fratræden et beløb svarende til henholdsvis 1 og 3 måneders løn (§ 2 a).{% else %}Opsigelse sker med følgende varsler: {{ felt.opsigelse_varsel }}{% if felt.overenskomst %} – i øvrigt efter overenskomsten{% endif %}.{% endif %} Opsigelse skal ske skriftligt.

## 10. Overenskomst
{% if felt.overenskomst %}Ansættelsesforholdet er omfattet af {{ felt.overenskomst }}. Overenskomstens bestemmelser gælder, hvor de giver medarbejderen bedre vilkår end dette ansættelsesbevis.{% else %}Ansættelsesforholdet er ikke omfattet af en kollektiv overenskomst.{% endif %}

## 11. Uddannelse
{{ felt.uddannelse }}

## 12. Sociale bidrag og forsikringer
Arbejdsgiveren indbetaler ATP-bidrag og bidrag til arbejdsmarkedets ordninger (AES/AUB, Barsel.dk m.fl.) og har tegnet arbejdsskadeforsikring hos {{ felt.arbejdsskadeforsikring }}. A-skat og AM-bidrag indeholdes og indbetales til Skattestyrelsen.{% if felt.pension %} Pensionsbidrag indbetales til pensionsselskabet som anført i pkt. 6.{% endif %}

{% if felt.tavshedspligt %}## 13. Tavshedspligt
Medarbejderen har under og efter ansættelsen tavshedspligt om forhold, der kommer til medarbejderens kendskab gennem arbejdet, og som efter deres natur bør hemmeligholdes, herunder forretningshemmeligheder (lov om forretningshemmeligheder) og personoplysninger.
{% endif %}
## Øvrigt
Ændringer i de vilkår, der er beskrevet her, meddeles skriftligt hurtigst muligt og senest den dag, ændringen træder i kraft (ansættelsesbevisloven § 5), medmindre ændringen alene følger af lov eller overenskomst. En medarbejder, der har været ansat i 6 måneder og har udstået en eventuel prøvetid, kan anmode om en ansættelsesform med mere forudsigelige og trygge arbejdsvilkår, hvis en sådan findes i virksomheden, og har krav på et skriftligt og begrundet svar senest 1 måned efter anmodningen – dog 3 måneder, hvis arbejdsgiveren er en fysisk person eller har færre end 35 ansatte (ansættelsesbevisloven § 10).

Dato: ______________________

______________________________________
for {{ kunde.navn }}

______________________________________
{{ felt.medarbejder_navn }}

*Ansættelsesbeviset er udleveret senest 7 kalenderdage efter tiltrædelse for så vidt angår pkt. 1-7 og senest 1 måned efter tiltrædelse for de øvrige punkter (ansættelsesbevisloven § 3, stk. 1: oplysningerne i § 3, stk. 2, nr. 1-5, 7 og 10-12, senest 7 kalenderdage og nr. 6, 8, 9 og 13-15 senest 1 måned efter ansættelsesforholdets begyndelse). Udarbejdet med bistand fra {{ firma.navn }}.*
