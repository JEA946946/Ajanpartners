---
{
  "title": "Regnskabsmæssige skøn (ISA 540)",
  "description": "Arbejdspapir til oversigt og vurdering af væsentlige regnskabsmæssige skøn: metode, forudsætninger, data, estimeringsusikkerhed, ledelsesbias og tilbageblik på sidste års skøn. Brancheafhængige skøn foreslås.",
  "kind": "arbejdspapir",
  "references": ["ISA 540 (ajourført)", "ISA 315", "ISA 580", "Årsregnskabsloven § 13 og § 77 (usikkerhed ved indregning og måling)"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "konklusion", "label": "Konklusion/bemærkninger", "type": "textarea"}
  ]
}
---
# Regnskabsmæssige skøn – {{ kunde.navn }}, {{ regnskab.aar }}

Udarbejdet af: {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Oversigt over væsentlige skøn
| Skøn | Beløb | Metode | Væsentlige forudsætninger og data | Estimeringsusikkerhed (lav/middel/høj) | Tilbageblik (sidste års skøn vs. faktisk) | Arbejdspapir |
|---|---|---|---|---|---|---|
| Nedskrivning på tilgodehavender | | | Aldersfordeling, betalinger efter statusdag | | | |
| Brugstider og restværdier for anlæg | | | | | | |
| Feriepenge og andre lønforpligtelser | | | | | | |
| Udskudt skat/skatteaktiv (udnyttelse af underskud) | | | Budget for kommende år | | | |
{% if branche.lager %}| Nedskrivning på varelager (ukurans, nettorealisationsværdi) | | | Omsætningshastighed, salgspriser efter statusdag | | | |
{% endif %}{% if branche.igangvaerende_arbejder %}| Igangværende arbejder (færdiggørelsesgrad, restomkostninger, tab) | | | Projektbudgetter, timer | | | |
{% endif %}{% if branche.byggeri %}| Garantiforpligtelser og mangelsager | | | Historiske garantiomkostninger | | | |
{% endif %}{% if branche.ejendom %}| Dagsværdi af investeringsejendomme | | Afkastmetode/DCF | Afkastkrav, markedsleje, tomgang, vedligehold | | | |
{% endif %}{% if branche.holding %}| Nedskrivningstest af kapitalandele og koncerntilgodehavender | | | Datterselskabers indre værdi og budgetter | | | |
{% endif %}{% if branche.landbrug %}| Dagsværdi af biologiske aktiver (besætning, afgrøder) | | | Noteringspriser, vægt, alder | | | |
{% endif %}{% if branche.it %}| Aktiverede udviklingsomkostninger (genindvindingsværdi) | | | Forventet indtjening, teknisk gennemførlighed | | | |
{% endif %}| Hensatte forpligtelser (retssager, tvister) | | | Advokatsvar | | | |

## 2. Handlinger pr. væsentligt skøn (ISA 540)
- [ ] Forståelse af, hvordan ledelsen foretager skønnet (metode, data, forudsætninger, kontrol)
- [ ] Valg af tilgang: (a) test af ledelsens metode, data og forudsætninger, (b) eget punktestimat/interval, eller (c) begivenheder efter balancedagen
- [ ] Forudsætningernes rimelighed og konsistens med andre forhold (budget, markedsdata, sidste år)
- [ ] Dataenes nøjagtighed og fuldstændighed
- [ ] Følsomhed: hvilke forudsætninger ville ændre beløbet væsentligt?
- [ ] Indikatorer for ledelsesbias – samlet vurdering på tværs af skøn (alle i samme retning?)
- [ ] Tilbageblik: resultat af sidste års skøn sammenholdt med faktisk udfald
- [ ] Oplysninger om usikkerhed ved indregning og måling i noter/ledelsesberetning er tilstrækkelige
- [ ] Ledelseserklæringen indeholder bekræftelse af, at metoder, forudsætninger og data er rimelige (ISA 580)

## 3. Konklusion
{{ felt.konklusion }}

- [ ] De regnskabsmæssige skøn og tilhørende oplysninger er rimelige i forhold til den regnskabsmæssige begrebsramme.

Opgaveansvarlig: ______________________ Dato: ____________
