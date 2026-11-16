---
{
  "title": "Opgørelse af udskudt skat",
  "description": "Arbejdspapir for udskudt skat efter balanceorienteret gældsmetode: midlertidige forskelle pr. aktivtype, skatteaktiv af underskud og vurdering af udnyttelse, satsændringer og afstemning til resultatopgørelsen.",
  "kind": "arbejdspapir",
  "references": ["Årsregnskabsloven § 37 og § 48", "Selskabsskatteloven §§ 12 og 17", "Afskrivningsloven", "Ejendomsavancebeskatningsloven"],
  "legal_forms": ["aps", "as", "holding", "ivs", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "skattesats", "label": "Skattesats for udskudt skat (%)", "type": "text", "default": "22"},
    {"name": "udskudt_primo", "label": "Udskudt skat primo (kr., + = forpligtelse)", "type": "number"},
    {"name": "underskud", "label": "Fremførbart skattemæssigt underskud ultimo (kr.)", "type": "number", "default": "0"},
    {"name": "indregn_aktiv", "label": "Skatteaktiv indregnes", "type": "select", "options": ["Ja – fuldt", "Delvist", "Nej – udnyttelse ikke sandsynlig"], "default": "Ja – fuldt"},
    {"name": "begrundelse", "label": "Begrundelse for vurdering af skatteaktiv", "type": "textarea"}
  ]
}
---
# Udskudt skat pr. {{ regnskab.slut }}

**Kunde:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}
**Udarbejdet af:** {{ medarbejder.navn }}, {{ dato.idag }}

**Metode:** Udskudt skat måles efter den balanceorienterede gældsmetode af alle midlertidige forskelle mellem regnskabsmæssige og skattemæssige værdier, med den skattesats, der er vedtaget på balancedagen, og som forventes at gælde, når forskellen udlignes: **{{ felt.skattesats }} %**. {% if branche.finans %}Finansielle selskaber med forhøjet sats anvender denne. {% endif %}En nedsættelse af selskabsskatten, der er varslet men ikke vedtaget på balancedagen, indregnes ikke; vedtages en satsændring efter balancedagen, oplyses den som efterfølgende begivenhed.

{% if kunde.regnskabsklasse == "B" %}*Regnskabsklasse B:* Små virksomheder kan undlade at indregne udskudt skat, men det er god skik og forudsat i de fleste anvendte regnskabspraksisser at indregne den (ÅRL § 37 og bilag). Undlades indregning, oplyses den udskudte skat i noterne.{% endif %}

## 1. Midlertidige forskelle
| Post | Regnskabsmæssig værdi | Skattemæssig værdi | Midlertidig forskel | Udskudt skat ({{ felt.skattesats }} %) |
|---|---|---|---|---|
| Immaterielle aktiver (goodwill, software, rettigheder) | | | | |
| Grunde og bygninger | | | | |
| Driftsmidler og inventar | | | | |
| Leasingaktiver/-forpligtelser | | | | |
{% if branche.investeringsejendomme or branche.ejendom %}| Investeringsejendomme (dagsværdi vs. anskaffelsessum ÷ afskrivninger, inkl. genvundne afskrivninger og ejendomsavance) | | | | |
{% endif %}{% if branche.igangvaerende_arbejder or branche.byggeri %}| Igangværende arbejder (regnskab vs. skat) | | | | |
{% endif %}{% if branche.lager %}| Varelager (ukurans ikke godkendt skattemæssigt) | | | | |
{% endif %}| Tilgodehavender (nedskrivning til tab ikke konstateret skattemæssigt) | | | | |
| Hensatte forpligtelser (garanti, omstrukturering) | | | | |
| Periodiseringer (fx feriepengeforpligtelse, forudbetalinger) | | | | |
| Kapitalandele (kun hvis skattepligtig avance – porteføljeaktier, lagerprincip) | | | | |
| Genbeskatningssaldo / succession | | | | |
| **I alt midlertidige forskelle** | | | | |

## 2. Skatteaktiv af fremførbart underskud
Fremførbart underskud: {{ felt.underskud }} kr. → skatteværdi {{ felt.skattesats }} %.

Vurdering: **{{ felt.indregn_aktiv }}**

{{ felt.begrundelse }}

Et skatteaktiv indregnes kun, hvis det er sandsynligt, at det kan udnyttes ved modregning i fremtidig skattepligtig indkomst inden for en overskuelig periode (typisk 3-5 år), understøttet af budgetter og historisk indtjening. Begrænsningen i SEL § 12 (fuld modregning op til grundbeløbet, derefter 60 %) indgår i vurderingen. Skatteaktiver og -forpligtelser modregnes inden for samme skattesubjekt (eller sambeskatningskreds).

## 3. Bevægelse
| | Kr. |
|---|---|
| Udskudt skat primo | {{ felt.udskudt_primo }} |
| Årets ændring indregnet i resultatopgørelsen | |
| Ændring indregnet direkte på egenkapitalen | |
| Effekt af ændret skattesats | |
| Regulering vedrørende tidligere år | |
| **Udskudt skat ultimo** | |
| Heraf udskudt skatteaktiv (opført under tilgodehavender) | |
| Heraf udskudt skatteforpligtelse (hensatte forpligtelser) | |

## 4. Kontrol
- [ ] Skattemæssige værdier afstemt til afskrivningsark og selvangivelse for sidste år.
- [ ] Ændring i udskudt skat afstemt til skatteberegningens afskrivningsforskelle.
- [ ] Ikke-udnyttede skatteaktiver oplyst i noterne.
- [ ] Ved sambeskatning: fordeling af underskud og udskudt skat mellem selskaberne vurderet.
