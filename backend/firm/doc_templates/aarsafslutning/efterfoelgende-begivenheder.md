---
{
  "title": "Efterfølgende begivenheder (ISA 560)",
  "description": "Arbejdspapir til gennemgang af begivenheder mellem balancedagen og påtegningsdatoen: korrigerende og ikke-korrigerende begivenheder, handlinger og konklusion.",
  "kind": "arbejdspapir",
  "references": ["ISA 560", "Årsregnskabsloven § 33, stk. 5, og § 11, stk. 2", "ISA 580"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "gennemgang_til", "label": "Gennemgang udført til og med (påtegningsdato)", "type": "date"},
    {"name": "seneste_maanedstal", "label": "Seneste måned med gennemgåede tal", "type": "text"},
    {"name": "begivenheder", "label": "Identificerede begivenheder", "type": "textarea"},
    {"name": "konklusion", "label": "Konklusion", "type": "select", "options": ["Ingen begivenheder, der kræver regulering eller oplysning", "Begivenheder er reguleret i regnskabet", "Begivenheder er oplyst i ledelsesberetning/note", "Opfølgning nødvendig"], "default": "Ingen begivenheder, der kræver regulering eller oplysning"}
  ]
}
---
# Efterfølgende begivenheder – {{ kunde.navn }}, {{ regnskab.aar }}

Balancedag: {{ regnskab.slut }}  Gennemgang udført til: {{ felt.gennemgang_til }}
Udarbejdet af: {{ medarbejder.navn }}, {{ dato.idag }}

**Korrigerende begivenheder** giver yderligere bevis for forhold, der eksisterede på balancedagen, og reguleres i regnskabet (ÅRL § 33, stk. 5 – fx konkurs hos debitor, afgørelse i retssag, salg af varer under kostpris). **Ikke-korrigerende begivenheder** opstår efter balancedagen og oplyses, hvis de er væsentlige (fx brand, opkøb, ny finansiering, kapitalforhøjelse). I klasse B følger oplysningspligten af kravet om retvisende billede (ÅRL § 11, stk. 2); i klasse C kræves særskilt beskrivelse (ÅRL § 98 d).

## 1. Handlinger (ISA 560, pkt. 6-7)
- [ ] Forespørgsel hos {{ kunde.ledelsesorgan }} om begivenheder efter balancedagen (se spørgsmål nedenfor)
- [ ] Gennemgang af bogføring og bankkonti efter balancedagen (seneste måned: {{ felt.seneste_maanedstal }}); usædvanlige posteringer og store betalinger
- [ ] Gennemgang af referater fra generalforsamling{% if kunde.selskabsform_kode == "as" %}, bestyrelses-{% endif %} og ledelsesmøder efter balancedagen
- [ ] Sammenligning af seneste perioderegnskab/budget med årsregnskabet
- [ ] Kontrol af betalinger efter balancedagen fra debitorer (nedskrivningsbehov) og til kreditorer (fuldstændighed af gæld)
- [ ] Kreditnotaer og returvarer efter balancedagen
{% if branche.lager %}- [ ] Salgspriser efter balancedagen for varer på lager (nettorealisationsværdi)
{% endif %}{% if branche.igangvaerende_arbejder %}- [ ] Slutafregning og tab på igangværende arbejder afsluttet efter balancedagen
{% endif %}{% if branche.ejendom %}- [ ] Nye vurderinger, salg af ejendomme, opsigelse fra væsentlige lejere
{% endif %}{% if branche.holding %}- [ ] Datterselskabernes resultater og begivenheder efter balancedagen; udbytte, kapitaltilskud
{% endif %}- [ ] Svar fra advokat og pengeinstitut er gennemgået for nye forhold
- [ ] Ledelseserklæringen bekræfter, at alle efterfølgende begivenheder er reguleret eller oplyst (ISA 560, pkt. 9)

## 2. Forespørgsler til ledelsen
| Spørgsmål | Svar |
|---|---|
| Er der indgået nye væsentlige aftaler, lån eller sikkerhedsstillelser? | |
| Er der solgt eller købt væsentlige aktiver/kapitalandele? | |
| Er der sket ændringer i kapitalforhold, udbytte eller ejerkreds? | |
| Er der opstået tab på debitorer, tvister eller retssager? | |
| Er der indtruffet skader, ulykker, konfiskation eller lignende? | |
| Er der sket væsentlige ændringer i aktiviteter, ledelse eller ansatte? | |
| Er der forhold, der kan påvirke fortsat drift? | |
| Er der usædvanlige posteringer/reguleringer efter balancedagen? | |

## 3. Identificerede begivenheder
{{ felt.begivenheder }}

| Begivenhed | Dato | Korrigerende/ikke-korrigerende | Beløb | Behandling (regulering/oplysning) | Arbejdspapir |
|---|---|---|---|---|---|
| | | | | | |

## 4. Forhold efter påtegningsdatoen (ISA 560, pkt. 10-17: pkt. 10-13 før og pkt. 14-17 efter offentliggørelse)
Bliver revisor efter påtegningsdatoen, men før årsrapporten er godkendt/offentliggjort, bekendt med forhold, der kunne have medført ændring af erklæringen, drøftes forholdet med ledelsen. Ændres regnskabet, udvides handlingerne til den nye påtegningsdato, og der afgives ny erklæring.

## 5. Konklusion
**{{ felt.konklusion }}**

Opgaveansvarlig: ______________________ Dato: ____________
