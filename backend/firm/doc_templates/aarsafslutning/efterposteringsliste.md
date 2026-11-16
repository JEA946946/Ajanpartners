---
{
  "title": "Efterposteringsliste – korrektioner og ikke-korrigerede fejl",
  "description": "Kladde til årsafslutningsposteringer (efterposteringer) med bilag og godkendelse, samt opgørelse af ikke-korrigerede fejlinformationer til ledelseserklæringen (ISA 450).",
  "kind": "arbejdspapir",
  "references": ["ISA 450", "ISA 580", "Bogføringsloven §§ 7, 8 og 10 (registrering, dokumentation, rettelser)"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "ubetydelig", "label": "Grænse for åbenlyst ubetydelige fejl (kr.)", "type": "number"},
    {"name": "vaesentlighed", "label": "Væsentlighed (kr.)", "type": "number"},
    {"name": "journal", "label": "Journal efterposteringerne bogføres i", "type": "text", "default": "Årsafslutning {{ regnskab.aar }}"}
  ]
}
---
# Efterposteringsliste – {{ kunde.navn }}, {{ regnskab.aar }}

Regnskabsperiode: {{ regnskab.start }} – {{ regnskab.slut }} · Journal: {{ felt.journal }}
Udarbejdet af: {{ medarbejder.navn }}, {{ dato.idag }}

Efterposteringerne bogføres i bogføringsprogrammet med dato {{ regnskab.slut }}, bilagsnummer og forklaring, så der er et fuldstændigt kontrolspor (bogføringsloven). Bogførte og validerede posteringer ændres ikke – fejl rettes med en ny postering/tilbageføring.

## 1. Korrektioner, der bogføres
| Nr. | Konto (debet) | Konto (kredit) | Beløb | Tekst/begrundelse | Bilag/arbejdspapir | Resultatpåvirkning | Godkendt af kunde |
|---|---|---|---|---|---|---|---|
| E1 | | | | | | | |
| E2 | | | | | | | |
| E3 | | | | | | | |
| E4 | | | | | | | |
| E5 | | | | | | | |
| **I alt** | | | | | | | |

Typiske efterposteringer: afskrivninger, periodeafgrænsning (skyldige/forudbetalte omkostninger), nedskrivning på debitorer og varelager, feriepengeforpligtelse, igangværende arbejder, skat af årets resultat og udskudt skat, foreslået udbytte, afstemningsdifferencer på moms/løn, private andele.

## 2. Resultat og egenkapital efter korrektioner
| | Før korrektioner | Korrektioner | Efter korrektioner |
|---|---|---|---|
| Resultat før skat | {{ regnskab.resultat }} | | |
| Skat af årets resultat | | | |
| Årets resultat | | | |
| Egenkapital | {{ regnskab.egenkapital }} | | |
| Balancesum | {{ regnskab.balancesum }} | | |

## 3. Ikke-korrigerede fejlinformationer (ISA 450)
Fejl under grænsen for åbenlyst ubetydelige fejl ({{ felt.ubetydelig }} kr.) registreres ikke.

| Nr. | Beskrivelse | Type (faktisk/skøn/ekstrapoleret) | Resultat | Aktiver | Forpligtelser | Egenkapital | Ledelsens begrundelse for ikke at korrigere |
|---|---|---|---|---|---|---|---|
| U1 | | | | | | | |
| U2 | | | | | | | |
| **I alt** | | | | | | | |

- [ ] Samlede ikke-korrigerede fejl (inkl. primoeffekt fra sidste år) er sammenholdt med væsentlighed ({{ felt.vaesentlighed }} kr.) – også kvalitativt
- [ ] Ledelsen er anmodet om at korrigere alle fejl (ISA 450, pkt. 8)
- [ ] Opgørelse over ikke-korrigerede fejl er vedlagt ledelseserklæringen, og ledelsen erklærer, at virkningen er uvæsentlig (ISA 450, pkt. 14; ISA 580)

## 4. Kundens godkendelse
Vi har gennemgået og godkender ovenstående efterposteringer (afsnit 1) og har noteret de ikke-korrigerede forhold (afsnit 3).

Dato: ______________________

______________________________________
{{ kunde.navn }} – for {{ kunde.ledelsesorgan }}
