---
{
  "title": "Påmindelse om frister (moms, A-skat, skat, årsrapport)",
  "description": "Oversigt og påmindelse om kundens kommende frister. Momsfrister tilpasses kundens momsperiode; A-skat efter virksomhedsstørrelse; selskabsskat/acontoskat eller B-skat efter selskabsform.",
  "kind": "brev",
  "references": ["Momsloven § 57", "Opkrævningsloven § 2, stk. 5-6 (A-skat og AM-bidrag)", "Selskabsskatteloven §§ 29 A ff. (acontoskat og restskat)", "Skattekontrolloven § 12 (selskabers oplysningsfrist)", "Årsregnskabsloven § 138"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "naeste_frist", "label": "Næste frist (dato)", "type": "date"},
    {"name": "naeste_frist_tekst", "label": "Næste frist gælder", "type": "text"},
    {"name": "a_skat_stoerrelse", "label": "A-skat: virksomhedens kategori", "type": "select", "options": ["Små og mellemstore virksomheder", "Stor virksomhed (fremrykket betaling)", "Ingen ansatte"], "default": "Små og mellemstore virksomheder"},
    {"name": "hvem_indberetter", "label": "Hvem indberetter moms", "type": "select", "options": ["Vi indberetter – I betaler", "I indberetter og betaler selv"], "default": "Vi indberetter – I betaler"},
    {"name": "beloeb", "label": "Forventet beløb til betaling (kr.)", "type": "number"},
    {"name": "materiale_frist", "label": "Vi skal have bilag senest", "type": "date"}
  ]
}
---
{{ kunde.navn }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Påmindelse: kommende frister

Kære {{ kunde.navn }}

**Næste frist: {{ felt.naeste_frist }} – {{ felt.naeste_frist_tekst }}**{% if felt.beloeb %}. Forventet beløb til betaling: {{ felt.beloeb }} kr.{% endif %}

{% if felt.materiale_frist %}For at vi kan nå det, skal alle bilag være uploadet og bankkonti afstemt senest **{{ felt.materiale_frist }}**.{% endif %}

Betalinger sker via jeres **skattekonto** med det betalings-ID, der fremgår af TastSelv Erhverv. Beløbet skal være på skattekontoen senest på fristdagen – ellers beregnes renter. En længere momsperiode forudsætter bl.a., at angivelse og betaling er sket rettidigt.

## Moms – jeres momsperiode: {{ kunde.momsperiode }}
({{ felt.hvem_indberetter }})

{% if kunde.momsperiode == "Halvår" %}| Periode | Frist for indberetning og betaling |
|---|---|
| 1. januar – 30. juni | 1. september |
| 1. juli – 31. december | 1. marts året efter |

Halvårsmoms gælder virksomheder med en momspligtig omsætning under 5 mio. kr. om året, der har indberettet og betalt til tiden.
{% elif kunde.momsperiode == "Kvartal" %}| Periode | Frist for indberetning og betaling |
|---|---|
| 1. kvartal (januar–marts) | 1. juni |
| 2. kvartal (april–juni) | 1. september |
| 3. kvartal (juli–september) | 1. december |
| 4. kvartal (oktober–december) | 1. marts året efter |

Kvartalsmoms gælder virksomheder med en momspligtig omsætning mellem 5 og 50 mio. kr. Nystartede virksomheder angiver kvartalsvis i mindst de første 18 måneder.
{% elif kunde.momsperiode == "Måned" %}Ved månedsmoms er fristen som hovedregel den 25. i måneden efter perioden; enkelte frister afviger (bl.a. for juni-perioden). Se de præcise datoer på skat.dk.

Månedsmoms gælder virksomheder med en momspligtig omsætning over 50 mio. kr. eller som selv har valgt det.
{% else %}Virksomheden er ikke momsregistreret. Husk, at virksomheden skal momsregistreres, når den momspligtige omsætning overstiger 50.000 kr. Fra 1. januar 2025 opgøres grænsen pr. kalenderår (småvirksomhedsordningen i momsloven § 71 e).
{% endif %}
Fristen flyttes til næste hverdag, hvis den falder på en weekend eller helligdag. Se de præcise datoer på skat.dk.

{% if felt.a_skat_stoerrelse != "Ingen ansatte" %}## A-skat og AM-bidrag (løn)
{% if felt.a_skat_stoerrelse == "Små og mellemstore virksomheder" %}Som lille/mellemstor virksomhed skal A-skat og AM-bidrag indberettes til eIndkomst og betales **senest den 10. i måneden efter** lønmåneden (fx løn for januar senest 10. februar); fristen i januar er dog den 17. januar (opkrævningsloven § 2, stk. 5).{% else %}Som stor virksomhed (fremrykket betaling) skal A-skat og AM-bidrag indberettes og betales **senest den sidste bankdag i den måned, som lønnen vedrører** (opkrævningsloven § 2, stk. 6). Reglerne for store virksomheder gælder, når A-skatten i en forudgående 12-måneders-periode har oversteget 1 mio. kr. eller AM-bidraget 250.000 kr.{% endif %} Kategorien fremgår af jeres registreringsbevis i TastSelv Erhverv. Indberetning skal ske, selv om der ikke er udbetalt løn i en måned, hvis I er registreret som arbejdsgiver.
{% endif %}
{% if kunde.er_kapitalselskab %}## Selskabsskat
| Hvad | Frist |
|---|---|
| Acontoskat, 1. rate (ordinær + evt. frivillig) | 20. marts |
| Acontoskat, 2. rate (ordinær + evt. frivillig) | 20. november |
| Frivillig 3. rate | 1. februar året efter indkomståret |
| Restskat for indkomståret med restskattetillæg | 1.–20. november året efter indkomståret |
| Selvangivelse (oplysningsskema) | 6 måneder efter indkomstårets udløb; for indkomstår, der udløber i perioden 1. – 31. marts, senest 1. september samme år (skattekontrolloven § 12) |

Acontoskatten beregnes som udgangspunkt som 50 % af gennemsnittet af de seneste tre års skat pr. rate. Går det bedre end ventet, kan frivillig indbetaling begrænse restskattetillægget – vi rådgiver gerne om beløbet.

## Årsrapport
Årsrapporten for {{ regnskab.aar }} skal være godkendt på generalforsamlingen og modtaget i Erhvervsstyrelsen senest **{{ regnskab.frist_aarsrapport }}**.
{% else %}## Personlig skat
| Hvad | Frist |
|---|---|
| B-skat (rater) | Den 20. i hver måned undtagen juni og december |
| Frivillig indbetaling af forventet restskat uden renter | Inden 1. januar året efter indkomståret (renten beregnes fra 1. januar) |
| Udvidet selvangivelse (oplysningsskema) | 1. juli året efter indkomståret |

Ændrer overskuddet sig væsentligt, bør forskudsopgørelsen tilrettes, så I undgår restskat. Vi hjælper gerne.
{% endif %}
Vi følger op på fristerne for jer. Har I spørgsmål, så kontakt {{ kunde.ansvarlig }}.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
