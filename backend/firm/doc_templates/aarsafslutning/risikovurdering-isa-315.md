---
{
  "title": "Risikovurdering (ISA 315) og besvigelsesrisici (ISA 240)",
  "description": "Identifikation og vurdering af risici for væsentlig fejlinformation på regnskabs- og revisionsmålsniveau, med branchespecifikke betydelige risici og formodede besvigelsesrisici.",
  "kind": "arbejdspapir",
  "references": ["ISA 315 (ajourført 2019)", "ISA 240", "ISA 330", "ISA 540", "ISA 550", "ISA 570"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "it_miljoe", "label": "It-miljø (systemer, integrationer, adgang)", "type": "textarea", "default": "Bogføring i {{ firma.navn }}s bogføringsprogram (digitalt standardbogføringssystem)."},
    {"name": "kontrolmiljoe", "label": "Vurdering af kontrolmiljø og funktionsadskillelse", "type": "textarea"},
    {"name": "forespoergsel_ledelse", "label": "Svar fra ledelsen om kendte/mistænkte besvigelser", "type": "textarea"},
    {"name": "afkraeft_indtaegt", "label": "Formodningen om besvigelsesrisiko ved indtægtsindregning afkræftes (begrund nedenfor)", "type": "checkbox"},
    {"name": "begrundelse_afkraeft", "label": "Begrundelse for afkræftelse", "type": "textarea"}
  ]
}
---
# Risikovurdering – {{ kunde.navn }}, {{ regnskab.aar }}

Udarbejdet af: {{ medarbejder.navn }}  Dato: {{ dato.idag }}  Branche: {{ kunde.branchetekst }} ({{ branche.navn }})

## 1. Risikovurderingshandlinger udført (ISA 315)
- [ ] Forespørgsler hos {{ kunde.ledelsesorgan }} og relevante medarbejdere
- [ ] Analytiske handlinger på foreløbige tal (sammenligning med sidste år, budget og branchenøgletal)
- [ ] Observation og inspektion (besøg på adresse, gennemgang af forretningsgange)
- [ ] Gennemgang af referater, kontrakter og korrespondance
- [ ] Drøftelse i opgaveteamet om risici for væsentlig fejlinformation, herunder besvigelser

## 2. Forståelse af de inhærente risikofaktorer
| Faktor | Vurdering |
|---|---|
| Kompleksitet | |
| Subjektivitet (skøn) | |
| Ændringer (nye aktiviteter, systemer, ledelse) | |
| Usikkerhed | |
| Tilbøjelighed til ledelsesbias eller besvigelser | |

## 3. Kontrolmiljø og it
**It-miljø:** {{ felt.it_miljoe }}

**Kontrolmiljø:** {{ felt.kontrolmiljoe }}

I mindre virksomheder er funktionsadskillelsen typisk begrænset, og den daglige leders involvering er både en kontrol og en risiko (mulighed for tilsidesættelse). Medmindre der er dokumenterede, effektive kontroller, planlægges en substansbaseret tilgang (ISA 330).

## 4. Besvigelsesrisici (ISA 240)
**Forespørgsel hos ledelsen om kendte eller mistænkte besvigelser:** {{ felt.forespoergsel_ledelse }}

| Risiko | Revisionsmål | Planlagte handlinger |
|---|---|---|
| **Ledelsens tilsidesættelse af kontroller** (kan ikke afkræftes) | Alle | Test af journalposter og andre reguleringer (manuelle posteringer, posteringer efter statusdagen, runde beløb, posteringer foretaget af ledelsen); gennemgang af regnskabsmæssige skøn for bias; vurdering af forretningsmæssig begrundelse for væsentlige, usædvanlige transaktioner |
| **Indtægtsindregning** (formodet risiko) | Forekomst, periodeafgrænsning{% if branche.kontantintensiv %}, fuldstændighed{% endif %} | Periodeafgrænsningstest omkring {{ regnskab.slut }}, analytisk review af omsætning pr. måned, test af kreditnotaer efter statusdagen{% if branche.kontantintensiv %}, afstemning af Z-rapporter til kasse/bank og bruttoavancekontrol{% endif %}{% if branche.igangvaerende_arbejder %}, gennemgang af færdiggørelsesgrad og forventet resultat på væsentlige sager{% endif %} |
{% if branche.kontantintensiv %}| **Uregistreret kontantsalg / underslæb** | Fuldstændighed | Nummerkontrol af Z-rapporter, sammenligning af vareforbrug og salg, gennemgang af kassedifferencer, kortindløsning vs. bank |
{% endif %}{% if branche.lager %}| **Manipulation af varelager** (overvurdering for at forbedre resultat eller opfylde covenants) | Eksistens, værdiansættelse | Deltagelse i optælling, test af kostpriser, test af ukurans, periodeafgrænsning af varekøb |
{% endif %}{% if branche.vikar or branche.rengoering or branche.byggeri %}| **Fiktive leverandører/underentreprenører eller sort løn** | Forekomst | Gennemgang af nye leverandører (CVR, momsregistrering), betalinger til private konti, sammenhæng mellem lønsum og aktivitet |
{% endif %}{% if branche.holding %}| **Transaktioner med nærtstående parter uden forretningsmæssig begrundelse** | Forekomst, præsentation | Gennemgang af mellemregninger, overførsler mellem selskaber og til ejere |
{% endif %}

{% if felt.afkraeft_indtaegt %}**Formodningen om besvigelsesrisiko ved indtægtsindregning afkræftes:** {{ felt.begrundelse_afkraeft }}{% endif %}

## 5. Betydelige risici og andre identificerede risici
| # | Risiko | Post/revisionsmål | Inhærent risiko (lav/middel/høj/betydelig) | Kontrolrisiko | Respons (arbejdspapir) |
|---|---|---|---|---|---|
| 1 | Ledelsens tilsidesættelse af kontroller | Alle | Betydelig | Høj | |
| 2 | Indtægtsindregning | Omsætning | Betydelig | | |
{% if branche.igangvaerende_arbejder %}| | Værdiansættelse af igangværende arbejder (skøn – ISA 540) | Igangværende arbejder, omsætning | Betydelig | | |
{% endif %}{% if branche.lager %}| | Eksistens og værdiansættelse af varelager | Varebeholdninger | Høj/betydelig | | |
{% endif %}{% if branche.ejendom %}| | Dagsværdi af investeringsejendomme (afkastkrav, lejeniveau) | Investeringsejendomme, udskudt skat | Betydelig | | |
{% endif %}{% if branche.holding %}| | Værdiansættelse af kapitalandele og koncerntilgodehavender | Finansielle anlægsaktiver | Høj | | |
{% endif %}{% if branche.landbrug %}| | Værdiansættelse af biologiske aktiver og fortsat drift ved høj gearing | Besætning, afgrøder, gæld | Høj | | |
{% endif %}{% if branche.bilhandel %}| | Brugtmoms og registreringsafgift; værdiansættelse af brugtvogne | Moms, varelager | Høj | | |
{% endif %}{% if branche.transport %}| | Skattefri godtgørelser og værdiansættelse af køretøjer | Løn, anlæg | Middel/høj | | |
{% endif %}{% if branche.momsfritaget %}| | Delvis momsfradrag og lønsumsafgift | Moms, omkostninger | Middel | | |
{% endif %}{% if branche.it %}| | Periodisering af abonnementer/licenser og aktiverede udviklingsprojekter | Omsætning, immaterielle aktiver | Middel/høj | | |
{% endif %}| | Fortsat drift (ISA 570) | Præsentation | | | |
| | Nærtstående parter og kapitalejerlån (ISA 550, LL § 16 E) | Tilgodehavender, noter | | | |
| | Fuldstændighed af gæld og eventualforpligtelser | Gæld, noter | | | |

## 6. Hvidvask
Kundens risikoprofil efter hvidvaskloven: **{{ branche.hvidvask_risiko }}**. Usædvanlige transaktioner, der opdages under revisionen, undersøges og noteres (hvidvaskloven § 25). Underretningspligt til Hvidvasksekretariatet (hvidvaskloven § 26) vurderes af opgaveansvarlig. Risikoprofilen ovenfor er revisionsvirksomhedens egen indikative vurdering ud fra branchen og skal efterprøves i den konkrete risikovurdering.

## 7. Konklusion
Risikovurderingen er grundlag for revisionsplanen (ISA 330). Den ajourføres, hvis der under revisionen fremkommer nye oplysninger.

Opgaveansvarlig: ______________________ Dato: ____________
