---
{
  "title": "Opgørelse af igangværende arbejder for fremmed regning",
  "description": "Arbejdspapir til opgørelse og revision af igangværende arbejder/entreprisekontrakter efter produktionsmetoden, med tabsgivende kontrakter og præsentation.",
  "kind": "arbejdspapir",
  "references": ["Årsregnskabsloven § 49, stk. 1 (produktionsmetoden), § 13, stk. 1 (forsigtighed og bruttoværdi)", "ISA 540 (ajourført)", "ISA 501"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "metode", "label": "Indregningsmetode", "type": "select", "options": ["Produktionsmetoden (salgsværdi)", "Kostpris (færdiggørelsesmetoden)"], "default": "Produktionsmetoden (salgsværdi)"},
    {"name": "faerdiggoerelse", "label": "Opgørelse af færdiggørelsesgrad", "type": "select", "options": ["Afholdte omkostninger i forhold til forventede samlede omkostninger", "Medgåede timer i forhold til forventede timer", "Fysisk opmåling/milepæle"], "default": "Afholdte omkostninger i forhold til forventede samlede omkostninger"},
    {"name": "bemaerkninger", "label": "Bemærkninger", "type": "textarea"}
  ]
}
---
# Igangværende arbejder pr. {{ regnskab.slut }} – {{ kunde.navn }}

Udarbejdet af: {{ medarbejder.navn }}, {{ dato.idag }}
Metode: **{{ felt.metode }}** · Færdiggørelsesgrad: {{ felt.faerdiggoerelse }}

## 1. Opgørelse pr. sag
| Sag nr. / kunde | Kontraktsum (A) | Forventede samlede omk. (B) | Forventet resultat (A-B) | Afholdte omk. til dato (C) | Færdiggørelsesgrad (C/B) | Salgsværdi (A × grad) | Faktureret aconto | Netto (aktiv + / passiv -) | Tab hensat |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
| **I alt** | | | | | | | | | |

## 2. Regnskabsmæssige principper
- Klasse B-virksomheder kan undlade at indregne indtægter i takt med udførelsen efter produktionsmetoden (ÅRL § 49, stk. 1). Ved produktionsmetoden indregnes indtægt i takt med udførelsen, når det samlede resultat kan opgøres pålideligt. Salgsværdien måles ud fra færdiggørelsesgraden.
- Kan resultatet ikke opgøres pålideligt, indregnes salgsværdien kun med de afholdte omkostninger, der sandsynligvis kan genindvindes.
- **Forventede tab indregnes straks fuldt ud** som en hensat forpligtelse/nedskrivning, når det er sandsynligt, at de samlede omkostninger overstiger kontraktsummen.
- Præsentation: sager med salgsværdi større end aconto vises som aktiv (tilgodehavende); sager med aconto større end salgsværdi vises som forpligtelse ("igangværende arbejder for fremmed regning" under kortfristet gæld). Sager vurderes hver for sig (bruttoværdiprincippet, ÅRL § 13, stk. 1, nr. 8).
- Forudbetalinger fra kunder, der ikke vedrører udført arbejde, præsenteres som forudbetalinger.

## 3. Revisionshandlinger
- [ ] Sagslisten er afstemt til saldobalancen (igangværende arbejder, acontofaktureringer, hensatte tab)
- [ ] Kontraktsum og tillæg er kontrolleret til underskrevne kontrakter/ordrebekræftelser for udvalgte sager
- [ ] Afholdte omkostninger (materialer, underleverandører, timer × kostpris) er stikprøvekontrolleret til bilag og timeregistrering
- [ ] Forventede restomkostninger er drøftet med projektleder; sammenholdt med historisk præcision (realiseret vs. forventet for sager afsluttet efter sidste statusdag)
- [ ] Sager afsluttet efter statusdagen: faktisk resultat sammenholdt med forventet (ISA 560)
- [ ] Ekstraarbejder er kun indregnet, når de er aftalt eller sandsynligt godkendt af kunden
- [ ] Tabsgivende kontrakter er identificeret og hensat fuldt ud
{% if branche.byggeri %}- [ ] Tvister, mangelsager og dagbøder er vurderet; 1-/5-års eftersyn og garantiforpligtelser hensat
- [ ] Sikkerhedsstillelser (garantier efter AB 18/ABT 18) er oplyst som eventualforpligtelser
- [ ] Tilbageholdte beløb og omvendt betalingspligt for moms er håndteret korrekt
{% endif %}{% if branche.liberalt_erhverv or branche.it %}- [ ] Ikke-fakturerede timer er værdiansat til salgsværdi (timepris) med fradrag for forventet nedskrivning ("write-down") på opgaven; timer på fastprisopgaver vurderes mod resterende budget
{% endif %}- [ ] Skøn er vurderet for ledelsesbias (ISA 540): sammenhæng med sidste år og indikatorer for "udjævning" af resultatet
- [ ] Skattemæssig behandling og udskudt skat er vurderet
- [ ] Noteoplysning om regnskabspraksis, usikkerhed ved skøn og nettopræsentation er korrekt

## 4. Bemærkninger og konklusion
{{ felt.bemaerkninger }}

- [ ] Igangværende arbejder er indregnet og målt korrekt, og forventede tab er hensat.

Opgaveansvarlig: ______________________ Dato: ____________
