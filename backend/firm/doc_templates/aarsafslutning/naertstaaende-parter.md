---
{
  "title": "Nærtstående parter (ISA 550)",
  "description": "Identifikation af nærtstående parter, transaktioner og mellemværender, vurdering af markedsvilkår, kapitalejerlån og noteoplysning.",
  "kind": "arbejdspapir",
  "references": ["ISA 550", "Årsregnskabsloven §§ 72, 98 c", "Selskabsloven §§ 115, 127, 206", "Ligningsloven §§ 2, 16 E", "Skattekontrolloven § 37"],
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
- [ ] Selskabsret: selskabslovens særlige regler om kapitalejerlån (§§ 210-212 og rentekravet i § 215) er ophævet med virkning fra 1. januar 2025 (lov nr. 1668 af 30. december 2024). Lånet skal dog fortsat være forsvarligt i forhold til selskabets økonomi (SL § 115), i selskabets interesse, på forretningsmæssige vilkår og må ikke give en utilbørlig fordel (SL § 127). Reglerne om selvfinansiering (SL § 206) gælder fortsat
- [ ] Lån ydet før 1. januar 2025 i strid med de dagældende regler er ikke blevet lovlige med tilbagevirkende kraft – overvej konsekvenserne og drøft med ledelsen
- [ ] Skat: lån til personlig kapitalejer med bestemmende indflydelse eller dennes nærtstående beskattes som udbytte eller løn (ligningsloven § 16 E). Er der ikke indeholdt udbytteskat/A-skat, vurderes, om der er tale om en skatteretlig overtrædelse, som skal omtales i erklæringen (erklæringsbekendtgørelsen – ledelsesansvar)
- [ ] Balance: tilgodehavender hos kapitalejere og ledelse vises som særskilt post; noteoplysning om lån til ledelsesmedlemmer (ÅRL § 72): beløb, rente, vilkår, tilbagebetalinger
{% else %}- [ ] Ikke kapitalselskab: private hævninger og indskud er opgjort; mellemregning med ejer er afstemt
{% endif %}

## 4. Noteoplysninger og skat
- [ ] Oplysning om nærtstående parter (ÅRL § 98 c) er givet i det omfang, klasse B kræver – særligt transaktioner, der ikke er gennemført på normale markedsvilkår
- [ ] Oplysning om kontrollerende part/modervirksomhed
- [ ] Skattemæssig oplysningspligt om kontrollerede transaktioner (skattekontrolloven § 37 – blanket 05.022 ved selskabets selvangivelse) og evt. dokumentationspligt
- [ ] Ledelseserklæringen bekræfter, at alle nærtstående parter og transaktioner er oplyst (ISA 550, pkt. 26)

## 5. Konklusion
- [ ] Nærtstående parter og transaktioner er identificeret, regnskabsmæssigt behandlet og oplyst korrekt.

Bemærkninger: ____________________________________________

Opgaveansvarlig: ______________________ Dato: ____________
