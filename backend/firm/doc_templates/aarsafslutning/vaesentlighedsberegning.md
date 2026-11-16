---
{
  "title": "Væsentlighedsberegning (ISA 320/450)",
  "description": "Fastlæggelse af væsentlighed, arbejdsvæsentlighed og grænse for åbenlyst ubetydelige fejl. Benchmark foreslås ud fra branche (drift, holding, ejendom, nonprofit).",
  "kind": "arbejdspapir",
  "references": ["ISA 320", "ISA 450", "ISRE 2400 (review)", "Erklæringsstandard for udvidet gennemgang"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "benchmark", "label": "Valgt benchmark", "type": "select", "options": ["Resultat før skat", "Omsætning", "Bruttofortjeneste", "Balancesum", "Egenkapital", "Samlede omkostninger"], "default": "Resultat før skat"},
    {"name": "benchmark_beloeb", "label": "Benchmarkbeløb (kr.)", "type": "number"},
    {"name": "procent", "label": "Anvendt procentsats", "type": "number"},
    {"name": "vaesentlighed", "label": "Væsentlighed (kr., afrundet)", "type": "number"},
    {"name": "arbejds_procent", "label": "Arbejdsvæsentlighed i % af væsentlighed", "type": "select", "options": ["50", "60", "65", "70", "75"], "default": "65"},
    {"name": "arbejdsvaesentlighed", "label": "Arbejdsvæsentlighed (kr.)", "type": "number"},
    {"name": "ubetydelig", "label": "Grænse for åbenlyst ubetydelige fejl (kr.)", "type": "number"},
    {"name": "specifik_vaesentlighed", "label": "Specifik (lavere) væsentlighed for særlige poster", "type": "textarea"},
    {"name": "begrundelse", "label": "Begrundelse for valg af benchmark og procent", "type": "textarea"}
  ]
}
---
# Væsentlighed – {{ kunde.navn }}, {{ regnskab.aar }}

Udarbejdet af: {{ medarbejder.navn }}  Dato: {{ dato.idag }}

## 1. Data fra bogføringen (foreløbige tal)
| Post | Beløb |
|---|---|
| Omsætning | {{ regnskab.omsaetning }} |
| Resultat | {{ regnskab.resultat }} |
| Balancesum | {{ regnskab.balancesum }} |
| Egenkapital | {{ regnskab.egenkapital }} |

## 2. Vejledende benchmarks
| Benchmark | Typisk interval | Anvendes typisk når |
|---|---|---|
| Resultat før skat (normaliseret) | 5 % (3–10 %) | Overskudsgivende driftsvirksomheder med stabil indtjening |
| Omsætning | 0,5–2 % | Resultat er lavt, svingende eller negativt |
| Bruttofortjeneste | 1–3 % | Klasse B-virksomheder, der præsenterer bruttofortjeneste (ÅRL § 32) |
| Balancesum | 1–2 % | Ejendomsselskaber og aktivtunge virksomheder |
| Egenkapital | 1–5 % | Holdingselskaber og investeringsselskaber |
| Samlede omkostninger | 0,5–2 % | Foreninger, fonde og nonprofit |

{% if branche.holding %}**Branchevurdering:** Holdingselskab – regnskabsbrugerne fokuserer på egenkapital og værdien af kapitalandele. Egenkapital eller balancesum er normalt det relevante benchmark. Overvej en lavere specifik væsentlighed for resultatopgørelsen og for transaktioner med nærtstående parter.
{% elif branche.ejendom %}**Branchevurdering:** Ejendomsselskab – balancen (ejendommenes værdi) er det centrale. Brug balancesum (1–2 %) for værdiansættelse af ejendomme; overvej en lavere specifik væsentlighed for lejeindtægter og driftsomkostninger, fx 5 % af resultat før dagsværdireguleringer.
{% elif branche.forening %}**Branchevurdering:** Forening/nonprofit – formålet er ikke overskud. Samlede omkostninger eller indtægter (tilskud, kontingenter) er relevante benchmarks.
{% elif branche.igangvaerende_arbejder %}**Branchevurdering:** Virksomhed med igangværende arbejder – resultatet er følsomt over for skøn over færdiggørelsesgrad. Er resultatet svingende, brug omsætning eller bruttofortjeneste.
{% elif branche.kontantintensiv %}**Branchevurdering:** Kontantintensiv virksomhed med lave marginer – omsætning eller bruttofortjeneste giver oftest et mere stabilt benchmark end resultatet. Fuldstændighedsrisikoen på omsætningen kan begrunde en lav procentsats.
{% else %}**Branchevurdering:** Driftsvirksomhed – normaliseret resultat før skat er udgangspunktet. Ved lavt eller negativt resultat anvendes omsætning eller bruttofortjeneste.
{% endif %}

## 3. Fastlagt væsentlighed
| | Beløb |
|---|---|
| Benchmark | {{ felt.benchmark }} |
| Benchmarkbeløb | {{ felt.benchmark_beloeb }} kr. |
| Procentsats | {{ felt.procent }} % |
| **Væsentlighed for regnskabet som helhed** | **{{ felt.vaesentlighed }} kr.** |
| Arbejdsvæsentlighed ({{ felt.arbejds_procent }} %) | {{ felt.arbejdsvaesentlighed }} kr. |
| Grænse for åbenlyst ubetydelige fejl (typisk 3–5 % af væsentlighed) | {{ felt.ubetydelig }} kr. |

**Specifik væsentlighed for særlige poster (ISA 320, pkt. 10):** {{ felt.specifik_vaesentlighed }}

Typiske poster med lavere væsentlighed: vederlag til ledelse, transaktioner med nærtstående parter, kapitalejerlån, noteoplysninger, der er lovpligtige uanset beløb.

## 4. Begrundelse
{{ felt.begrundelse }}

Overvejelser om arbejdsvæsentlighed (lav ende 50–60 % ved: første års revision, mange fejl sidste år, svagt kontrolmiljø, høj risiko; høj ende 70–75 % ved: få fejl, stabil virksomhed, kendt kunde).

- [ ] Kvalitative forhold er overvejet (lånebetingelser/covenants, overgang fra overskud til underskud, egenkapital tæt på kapitaltab, selskabsretlig kapitalkrav)
- [ ] Væsentligheden er revurderet ved afslutningen på grundlag af de endelige tal (ISA 320, pkt. 12-13)
- [ ] Ikke-korrigerede fejl er sammenholdt med væsentligheden og meddelt ledelsen (ISA 450)

## 5. Revurdering ved afslutning
| | Planlægning | Afslutning |
|---|---|---|
| Benchmarkbeløb | {{ felt.benchmark_beloeb }} | |
| Væsentlighed | {{ felt.vaesentlighed }} | |
| Ændring nødvendig? (ja/nej, begrundelse) | | |

Godkendt af opgaveansvarlig: ______________________ Dato: ____________
