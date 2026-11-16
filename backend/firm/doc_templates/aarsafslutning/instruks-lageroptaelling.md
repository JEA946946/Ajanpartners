---
{
  "title": "Instruks for lageroptælling",
  "description": "Instruks til kunden for planlægning og gennemførelse af lageroptælling pr. statusdagen, med revisors observationspunkter (ISA 501).",
  "kind": "brev",
  "references": ["ISA 501, pkt. 4-8", "Årsregnskabsloven §§ 44-46 (varebeholdninger)", "Bogføringsloven §§ 4 og 12 (regnskabsmateriale og opbevaring)"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "optaellingsdato", "label": "Optællingsdato", "type": "date"},
    {"name": "tidspunkt", "label": "Tidspunkt", "type": "text"},
    {"name": "lokationer", "label": "Lagerlokationer", "type": "textarea"},
    {"name": "ansvarlig_kunde", "label": "Ansvarlig hos kunden", "type": "text"},
    {"name": "revisor_deltager", "label": "Revisor deltager i optællingen", "type": "checkbox", "default": true}
  ]
}
---
**{{ firma.navn }}**

{{ kunde.navn }}
{{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Instruks for lageroptælling pr. {{ regnskab.slut }}

Varelageret skal optælles og værdiansættes pr. statusdagen. Optællingen er grundlaget for varelagerets størrelse i årsrapporten, og en omhyggelig optælling er derfor afgørende. Nedenfor finder I vores anbefalinger til, hvordan optællingen planlægges og gennemføres.

**Optællingsdato:** {{ felt.optaellingsdato }}, kl. {{ felt.tidspunkt }}
**Lokationer:** {{ felt.lokationer }}
**Ansvarlig hos jer:** {{ felt.ansvarlig_kunde }}
{% if felt.revisor_deltager %}**Revisor deltager:** Ja – {{ medarbejder.navn }} deltager som observatør og foretager stikprøveoptællinger (ISA 501).{% endif %}

## 1. Før optællingen
- [ ] Udpeg en ansvarlig for optællingen og fordel lageret i optællingsområder (zoner, reoler, hylder)
- [ ] Sæt hold af to personer: én tæller, én noterer. Holdene bør så vidt muligt ikke være de medarbejdere, der til daglig har ansvaret for det pågældende lager
- [ ] Udskriv nummererede optællingslister uden forudtrykte antal (blind optælling) eller brug håndscanner med log
- [ ] Ryd op og saml ens varer; marker varer, der ikke tilhører jer (kommissionsvarer, kundevarer til reparation), og varer, der er solgt, men ikke afhentet
- [ ] Udskil og marker ukurante, beskadigede og udløbne varer
- [ ] Stop eller registrér særskilt alle vareflytninger under optællingen

## 2. Periodeafgrænsning (cut-off)
- [ ] Notér nummeret på den sidste følgeseddel/varemodtagelse og den sidste udleveringsseddel før optællingen
- [ ] Varer modtaget før optællingen skal tælles med og være bogført som køb; varer modtaget efter skal holdes adskilt
- [ ] Varer afsendt til kunder før optællingen må ikke tælles med og skal være faktureret
{% if branche.fremstilling %}- [ ] Produktion i gang: varer i arbejde tælles og påføres færdiggørelsesgrad; stop produktionen eller registrer flytninger mellem lagre
{% endif %}
## 3. Under optællingen
- [ ] Tæl, vej eller mål alle varer. Notér varenummer, beskrivelse, antal, enhed og tilstand (kurant/ukurant)
- [ ] Markér optalte områder (fx med farvet tape eller seddel), så intet tælles to gange eller springes over
- [ ] Rettelser foretages ved overstregning, så det oprindelige tal kan læses, og parafres
- [ ] Optællingslister underskrives af både tæller og noterer
- [ ] Alle udleverede optællingslister indsamles – også ubrugte og fejlagtige – og nummerrækken kontrolleres
- [ ] Varer på eksterne lagre eller hos tredjemand bekræftes skriftligt af lagerholderen
{% if branche.landbrug %}- [ ] Besætning tælles pr. kategori; beholdninger af korn, foder og gødning opmåles (siloer, lader) og dokumenteres med beregning
{% endif %}{% if branche.bilhandel %}- [ ] Hver bil kontrolleres fysisk med stelnummer og km-stand; demobiler og biler hos tredjemand registreres særskilt
{% endif %}{% if branche.restauration %}- [ ] Optælling af drikkevarer, råvarer og emballage i køkken, bar og kølerum; åbne flasker vurderes skønsmæssigt
{% endif %}
## 4. Efter optællingen
- [ ] Optællingslister overføres til lagerliste og sammenholdes med lagersystemet; væsentlige differencer undersøges og forklares
- [ ] Værdiansæt til kostpris (seneste købspris/FIFO eller vejet gennemsnit) med dokumentation for priser
- [ ] Nedskriv ukurante og langsomt omsættelige varer til nettorealisationsværdi
- [ ] Hvis optællingen ikke sker på statusdagen: opgør til- og afgang mellem optællingsdagen og {{ regnskab.slut }}
- [ ] Send optællingslister (originaler/kopi), lagerliste og differenceopgørelse til os

## 5. Revisors handlinger ved observation (internt)
- [ ] Vurdering af instruks og om den følges
- [ ] Stikprøveoptællinger begge veje: fra liste til lager (eksistens) og fra lager til liste (fuldstændighed)
- [ ] Kopi af udvalgte optællingslister og cut-off-oplysninger tages med
- [ ] Iagttagelse af ukurante varer og varer, der tilhører andre
- [ ] Senere: afstemning af endelig lagerliste mod optællingslister og stikprøver

Har I spørgsmål til optællingen, er I velkomne til at kontakte {{ kunde.ansvarlig }}.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
