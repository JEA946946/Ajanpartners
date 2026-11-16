---
{
  "title": "Going concern-vurdering (ISA 570)",
  "description": "Arbejdspapir til vurdering af ledelsens forudsætning om fortsat drift: indikatorer, ledelsens planer, likviditetsbudget, konklusion og konsekvens for påtegningen.",
  "kind": "arbejdspapir",
  "references": ["ISA 570 (ajourført)", "ISA 560", "ISA 580", "Årsregnskabsloven § 13, stk. 1, nr. 4", "Selskabsloven §§ 115, 119"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "vurderingsperiode_slut", "label": "Vurderingsperioden løber til (mindst 12 mdr. efter regnskabets dato, ISA 570 pkt. 13)", "type": "date"},
    {"name": "selskabskapital", "label": "Selskabskapital (kr.)", "type": "number"},
    {"name": "likviditet_ultimo", "label": "Likvider og ubenyttet kredit ultimo (kr.)", "type": "number"},
    {"name": "kreditfacilitet_udloeb", "label": "Udløb af væsentlige kreditfaciliteter", "type": "text"},
    {"name": "ledelsens_planer", "label": "Ledelsens planer og tiltag", "type": "textarea"},
    {"name": "konklusion", "label": "Konklusion", "type": "select", "options": ["Ingen væsentlig usikkerhed", "Væsentlig usikkerhed – tilstrækkeligt oplyst (afsnit om væsentlig usikkerhed vedrørende fortsat drift)", "Væsentlig usikkerhed – ikke tilstrækkeligt oplyst (modificeret konklusion)", "Forudsætningen er ikke passende (afkræftende konklusion)"], "default": "Ingen væsentlig usikkerhed"}
  ]
}
---
# Vurdering af fortsat drift – {{ kunde.navn }}, {{ regnskab.aar }}

Udarbejdet af: {{ medarbejder.navn }}  Dato: {{ dato.idag }}
Balancedag: {{ regnskab.slut }}  Vurderingsperiode til: {{ felt.vurderingsperiode_slut }}

Årsrapporten udarbejdes under forudsætning af fortsat drift (going concern), medmindre driften ikke skal eller ikke antages at kunne fortsætte (ÅRL § 13, stk. 1, nr. 4). Dækker ledelsens vurdering mindre end 12 måneder fra regnskabets dato, skal revisor anmode ledelsen om at forlænge vurderingsperioden til mindst 12 måneder (ISA 570, pkt. 13). Revisor skal opnå tilstrækkeligt og egnet bevis for, at forudsætningen er passende, og konkludere, om der er en væsentlig usikkerhed (ISA 570).

## 1. Nøgletal
| | Beløb |
|---|---|
| Resultat for året | {{ regnskab.resultat }} |
| Egenkapital ultimo | {{ regnskab.egenkapital }} |
| Balancesum | {{ regnskab.balancesum }} |
{% if kunde.er_kapitalselskab %}| Selskabskapital | {{ felt.selskabskapital }} |
{% endif %}| Likvider og ubenyttet kredit | {{ felt.likviditet_ultimo }} |
| Udløb af væsentlige kreditfaciliteter | {{ felt.kreditfacilitet_udloeb }} |

## 2. Indikatorer (sæt kryds hvis til stede)
**Finansielle**
- [ ] Negativ egenkapital eller negativ arbejdskapital
- [ ] Kortfristede lån forfalder uden realistisk udsigt til forlængelse; afhængighed af kassekredit, der kan opsiges
- [ ] Negative pengestrømme fra driften eller gentagne underskud
- [ ] Brud på lånebetingelser (covenants), restancer til SKAT (skattekonto i minus, inddrivelse hos Gældsstyrelsen) eller til leverandører
- [ ] Manglende evne til at betale løn, moms og A-skat rettidigt
{% if kunde.er_kapitalselskab %}- [ ] Kapitaltab: egenkapitalen udgør mindre end halvdelen af den tegnede kapital (SL § 119 – ledelsen skal sikre, at der afholdes generalforsamling senest 6 måneder efter konstateringen, hvor ledelsen redegør for den økonomiske stilling)
{% endif %}
**Driftsmæssige**
- [ ] Tab af væsentlig kunde, leverandør, licens eller nøglemedarbejder
- [ ] Mangel på arbejdskraft eller væsentlige råvarer
{% if branche.byggeri %}- [ ] Tabsgivende entrepriser, store tvister eller tilbageholdte betalinger; faldende ordrebeholdning
{% endif %}{% if branche.restauration or branche.hotel %}- [ ] Sæsonudsving, høj gearing på inventar, husleje- og leasingforpligtelser
{% endif %}{% if branche.landbrug %}- [ ] Høj gearing og afhængighed af bankens fortsatte støtte; prisudsving på afregningspriser
{% endif %}{% if branche.ejendom %}- [ ] Refinansiering af ejendomslån, tomgang, faldende ejendomsværdier, rentestigning
{% endif %}{% if branche.holding %}- [ ] Afhængighed af udbytte fra datterselskaber eller af datterselskabernes evne til at betale koncerntilgodehavender; kautioner/sambeskatningshæftelse
{% endif %}
**Andre**
- [ ] Verserende retssager eller krav, der kan true virksomheden
- [ ] Lovændringer eller myndighedskrav med væsentlig betydning
- [ ] Virksomheden er under rekonstruktion eller har anmodet om det

## 3. Ledelsens vurdering og planer
**Ledelsens planer:** {{ felt.ledelsens_planer }}

- [ ] Ledelsens skriftlige vurdering er modtaget og dækker mindst 12 måneder fra regnskabets dato (ISA 570, pkt. 13)
- [ ] Likviditetsbudget er gennemgået; forudsætninger (omsætning, marginer, investeringer, afdrag) er realistiske og sammenholdt med historik og efterfølgende måneders faktiske tal
- [ ] Følsomhed er vurderet (fx 10-20 % lavere omsætning)
- [ ] Bekræftelse af finansiering: tilsagn fra bank, kapitalejere (støtteerklæring/kapitaltilsagn) eller moderselskab – underskrevet og med tilstrækkelig økonomisk evne bag
- [ ] Efterfølgende begivenheder frem til påtegningsdatoen er gennemgået (ISA 560)
- [ ] Ledelsens oplysninger om usikkerhed i ledelsesberetning/note er dækkende
- [ ] Ledelseserklæringen indeholder ledelsens planer og vurdering af fortsat drift (ISA 580)

## 4. Konklusion
**{{ felt.konklusion }}**

| Konklusion | Konsekvens for erklæringen |
|---|---|
| Ingen væsentlig usikkerhed | Ingen. Overvej at drøfte forholdet med ledelsen, hvis der var indikatorer. |
| Væsentlig usikkerhed, tilstrækkeligt oplyst | Afsnit "Væsentlig usikkerhed vedrørende fortsat drift" i erklæringen med henvisning til noten |
| Væsentlig usikkerhed, ikke tilstrækkeligt oplyst | Konklusion med forbehold eller afkræftende konklusion |
| Forudsætningen er ikke passende | Afkræftende konklusion; overvej regnskab på realisationsbasis |
| Ledelsen vil ikke foretage/forlænge vurdering | Overvej konsekvenser for erklæringen (manglende bevis) |

- [ ] Forholdet er kommunikeret til den øverste ledelse (ISA 570, ISA 260)
{% if kunde.er_kapitalselskab %}- [ ] Hvis selskabet har tabt kapitalen og ledelsen ikke handler: ledelsen er gjort opmærksom på ansvar og evt. pligt til at overveje rekonstruktion/konkursbegæring
{% endif %}

Opgaveansvarlig: ______________________ Dato: ____________
