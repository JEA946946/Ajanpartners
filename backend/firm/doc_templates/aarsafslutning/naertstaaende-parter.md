---
{
  "title": "Nærtstående parter (ISA 550)",
  "description": "Identifikation af nærtstående parter, transaktioner og mellemværender, vurdering af markedsvilkår, kapitalejerlån og noteoplysning.",
  "kind": "arbejdspapir",
  "references": ["ISA 550", "Årsregnskabsloven §§ 11, 73, 98 c", "Selskabsloven §§ 115, 127, 206", "Ligningsloven §§ 2, 16 E", "Skattekontrolloven §§ 37-38"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "ejere", "label": "Kapitalejere/ejere (navn, andel)", "type": "textarea"},
    {"name": "ledelse", "label": "Ledelsesmedlemmer", "type": "textarea"},
    {"name": "koncern", "label": "Koncernselskaber og ejers andre selskaber", "type": "textarea"},
    {"name": "familie", "label": "Nærtstående familiemedlemmer ansat/involveret", "type": "textarea"}
  ]
}
---
# Nærtstående parter – {{ kunde.navn }}, {{ regnskab.aar }}

Udarbejdet af: {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Identifikation af nærtstående parter
| Kategori | Parter |
|---|---|
| {{ kunde.kapitalejere }} med bestemmende/betydelig indflydelse | {{ felt.ejere }} |
| Medlemmer af {{ kunde.ledelsesorgan }} | {{ felt.ledelse }} |
| Koncernselskaber og selskaber, ejer/ledelse kontrollerer | {{ felt.koncern }} |
| Nærtstående familie (ægtefælle, børn, forældre) | {{ felt.familie }} |

- [ ] Liste er indhentet fra ledelsen og sammenholdt med CVR (ejerregister, reelle ejere, ledelsesposter i andre selskaber)
- [ ] Sammenholdt med sidste års arbejdspapirer og hvidvaskdokumentation (reelle ejere)
- [ ] Teamet er orienteret om de identificerede parter

## 2. Transaktioner og mellemværender i året
| Part | Type (køb, salg, leje, lån, løn/honorar, garanti, kaution) | Beløb i året | Saldo ultimo | Markedsvilkår? (ja/nej, dokumentation) | Godkendt af |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

**Handlinger**
- [ ] Gennemgang af mellemregningskonti, private posteringer og betalinger til ejere/ledelse
- [ ] Gennemgang af væsentlige, usædvanlige transaktioner uden for normal drift – forretningsmæssig begrundelse (ISA 550, pkt. 23)
- [ ] Kontrakter med nærtstående parter (lejeaftaler, managementaftaler, låneaftaler) er indhentet
- [ ] Vederlag til ledelsen er afstemt til lønsedler/eIndkomst og evt. GF-beslutning
{% if branche.holding %}- [ ] Koncernmellemværender er afstemt med modparten; management fee og renter er fastsat på armslængdevilkår (transfer pricing – ligningsloven § 2)
- [ ] Sambeskatning: fordeling af skat og hæftelse
{% endif %}{% if branche.ejendom %}- [ ] Leje af ejendom til/fra ejer eller koncernselskab: lejeniveau er sammenholdt med markedsleje
{% endif %}
## 3. Kapitalejerlån og lån til ledelsen
{% if kunde.er_kapitalselskab %}- [ ] Har selskabet direkte eller indirekte ydet lån eller stillet sikkerhed for {{ kunde.kapitalejere }}, ledelsen eller nærtstående til disse (herunder debetsaldo på mellemregning)?
- [ ] Selskabsret: selskabslovens særlige regler om kapitalejerlån (§§ 210-212) er ophævet med virkning fra 1. januar 2025 (lov nr. 1668 af 30. december 2024). Ledelsen skal dog fortsat sikre et forsvarligt kapitalberedskab (SL § 115, nr. 5) og må ikke disponere, så dispositionen er åbenbart egnet til at skaffe nogen en utilbørlig fordel på andre kapitalejeres eller selskabets bekostning (SL § 127). Reglerne om selvfinansiering (SL §§ 206-215) gælder fortsat; lovlig bistand efter § 206, stk. 2, kræver reserve for udlån og sikkerhedsstillelse (ÅRL § 35 a)
- [ ] Lån ydet før 1. januar 2025 vurderes efter de dagældende regler i SL §§ 210-212 – overvej konsekvenserne og drøft med ledelsen
- [ ] Skat: lån til personlig kapitalejer med bestemmende indflydelse eller dennes nærtstående beskattes som udbytte eller løn (ligningsloven § 16 E, stk. 1). For lån ydet fra 1. januar 2026 anses tilbagebetalinger som et rentefrit anfordringslån til selskabet, og selskabet skal føre en skattemæssig mellemregningskonto (§ 16 E, stk. 2-4, indsat ved lov nr. 749 af 20. juni 2025). Er der ikke indeholdt udbytteskat/A-skat, vurderes, om der er tale om en overtrædelse, som skal omtales i erklæringen (erklæringsbekendtgørelsen)
- [ ] Note om tilgodehavender hos og sikkerhedsstillelser for ledelsesmedlemmer (ÅRL § 73): sum pr. ledelseskategori, væsentligste vilkår inkl. rentefod, tilbagebetalte beløb, nedskrivninger/afkald
{% else %}- [ ] Ikke kapitalselskab: private hævninger og indskud er opgjort; mellemregning med ejer er afstemt
{% endif %}

## 4. Noteoplysninger og skat
- [ ] Oplysning om nærtstående parter: ÅRL § 98 c gælder regnskabsklasse C (klasse C kan begrænse oplysningerne til transaktioner, der ikke er gennemført på normale markedsvilkår, § 98 c, stk. 6). For klasse B er § 98 c ikke blandt de bestemmelser, der gælder (ÅRL § 22, stk. 1) – vurder, om oplysning er nødvendig for et retvisende billede (ÅRL § 11, stk. 2). Regnskabsklasse: {{ kunde.regnskabsklasse }}
- [ ] Navn og hjemsted for modervirksomhed, der udarbejder koncernregnskab for den mindste koncern (ÅRL § 71)
- [ ] Skattemæssig oplysningspligt om kontrollerede transaktioner (skattekontrolloven § 37, stk. 1, nr. 6, og § 38 – afgives digitalt sammen med selskabets oplysningsskema, bilagsblanket 05.021) og evt. dokumentationspligt
- [ ] Ledelseserklæringen bekræfter, at alle nærtstående parter og transaktioner er oplyst (ISA 550, pkt. 26)

## 5. Konklusion
- [ ] Nærtstående parter og transaktioner er identificeret, regnskabsmæssigt behandlet og oplyst korrekt.

Bemærkninger: ____________________________________________

Opgaveansvarlig: ______________________ Dato: ____________
