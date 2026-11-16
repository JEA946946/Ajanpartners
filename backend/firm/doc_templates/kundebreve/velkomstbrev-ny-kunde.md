---
{
  "title": "Velkomstbrev til ny kunde",
  "description": "Velkomst og onboarding: hvem gør hvad, adgange og fuldmagter, legitimation efter hvidvaskloven, bogføringsprogrammet og hvad vi skal bruge for at komme i gang.",
  "kind": "brev",
  "references": ["Hvidvaskloven §§ 10-12 (kundekendskab)", "Bogføringsloven §§ 12, 15 (opbevaring, digital bogføring)", "Revisorloven § 18 (revisorskifte)"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "ydelser", "label": "Aftalte ydelser", "type": "textarea", "default": "Bogføring, moms og årsrapport"},
    {"name": "startdato", "label": "Samarbejdet starter", "type": "date"},
    {"name": "frist_materiale", "label": "Frist for at sende det første materiale", "type": "date"},
    {"name": "revisorskifte", "label": "Kunden kommer fra en anden revisor/bogholder", "type": "checkbox"},
    {"name": "tidligere_revisor", "label": "Tidligere revisor/bogholder", "type": "text"},
    {"name": "loen", "label": "Vi skal køre løn", "type": "checkbox"}
  ]
}
---
{{ kunde.navn }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Velkommen til {{ firma.navn }}

Kære {{ kunde.navn }}

Tak for jeres tillid. Vi glæder os til samarbejdet, som starter den {{ felt.startdato }}. Jeres faste kontaktperson er **{{ kunde.ansvarlig }}**, som I altid kan kontakte på {{ firma.telefon }} eller {{ firma.email }}.

**Aftalte ydelser:** {{ felt.ydelser }}

Det præcise indhold af vores opgaver og ansvarsfordelingen fremgår af opdragsbrevet/kundeaftalen{% if kunde.aftalereference %} ({{ kunde.aftalereference }}){% endif %}, som vi beder jer læse og underskrive digitalt.

## Hvad sker der nu?
1. **Opdragsbrev og betingelser.** I modtager opdragsbrevet til digital underskrift. Første gang I logger ind i bogføringsprogrammet, skal I også acceptere forretningsbetingelserne og databehandleraftalen.
2. **Legitimation (hvidvaskloven).** Vi er efter hvidvaskloven forpligtet til at kende vores kunder. Vi skal derfor have oplysninger om ejere og ledelse og kopi af legitimation – se listen nedenfor.
3. **Adgange og fuldmagter.** I giver os adgang til Skattestyrelsen, Erhvervsstyrelsen og jeres bank – se nedenfor.
4. **Bogføringsprogrammet.** I får adgang til vores gratis bogføringsprogram, hvor I uploader bilag, og hvor vi bogfører, afstemmer og indberetter moms.{% if kunde.er_kapitalselskab %} Kapitalselskaber skal efter bogføringsloven bogføre i et digitalt bogføringssystem.{% else %} Personligt ejede virksomheder med en nettoomsætning over 300.000 kr. i to år i træk skal efter bogføringsloven bogføre i et digitalt bogføringssystem.{% endif %} Bilag og regnskabsmateriale skal opbevares i 5 år fra udgangen af det regnskabsår, materialet vedrører.

## Det skal vi bruge fra jer
**Kundekendskab**
- [ ] Kopi af pas eller kørekort for {% if kunde.er_kapitalselskab %}direktør og reelle ejere (personer, der direkte eller indirekte ejer eller kontrollerer mere end 25 %){% else %}indehaver(e){% endif %}
- [ ] Dokumentation for adresse (fx sundhedskort), hvis den ikke fremgår af legitimationen
- [ ] Oplysning om virksomhedens formål, forventede omsætning, væsentligste kunder/leverandører og om der er handel med udlandet
- [ ] Oplysning om, hvorvidt nogen i ejerkreds eller ledelse er politisk eksponeret person (PEP) eller nær familie/samarbejdspartner til en PEP
{% if kunde.er_kapitalselskab %}- [ ] Ejerbog og evt. ejeraftale; seneste vedtægter
{% endif %}
**Adgange (giv adgang via MitID Erhverv)**
- [ ] Adgang til TastSelv Erhverv for {{ firma.navn }} (CVR {{ firma.cvr }}) som rådgiver – moms{% if felt.loen %}, A-skat og eIndkomst{% endif %}{% if kunde.er_kapitalselskab %}, selskabsskat{% endif %}
- [ ] Adgang til Virk/Erhvervsstyrelsen til indberetning af årsrapport
- [ ] Læseadgang til netbank eller automatisk bankintegration til bogføringsprogrammet
{% if not kunde.er_kapitalselskab %}- [ ] Fuldmagt til jeres personlige skatteoplysninger (forskudsopgørelse og årsopgørelse)
{% endif %}
**Regnskabsmateriale**
- [ ] Seneste årsrapport/årsregnskab og skatteopgørelse
- [ ] Saldobalance og åbne poster (debitorer, kreditorer) pr. startdatoen
- [ ] Låneaftaler, leasingaftaler, lejekontrakt og forsikringspolicer
- [ ] Anlægskartotek/oversigt over aktiver
{% if felt.loen %}- [ ] Lønoplysninger: medarbejderliste, ansættelseskontrakter, overenskomst, pensionsaftaler og seneste lønsedler
{% endif %}{% if branche.lager %}- [ ] Seneste lageropgørelse og oplysning om lagersystem
{% endif %}{% if branche.kontantintensiv %}- [ ] Oplysning om kasseapparat/POS-system og rutine for daglig kasseafstemning
{% endif %}{% if branche.igangvaerende_arbejder %}- [ ] Liste over igangværende opgaver/projekter og jeres tidsregistreringssystem
{% endif %}{% if branche.ejendom %}- [ ] Lejeliste og lejekontrakter, seneste ejendomsvurdering
{% endif %}{% if branche.holding %}- [ ] Koncernoversigt og årsrapporter for datterselskaber
{% endif %}
{% if felt.revisorskifte %}## Skift fra {{ felt.tidligere_revisor }}
Vi kontakter {{ felt.tidligere_revisor }} for at få overdraget nødvendige oplysninger og materiale. Vi beder jer give jeres tidligere rådgiver besked om skiftet og om, at de må udlevere materiale til os.{% if kunde.er_kapitalselskab %} Er vi valgt som revisor, skal valget registreres i Erhvervsstyrelsen.{% endif %}
{% endif %}

Vi beder jer sende materialet senest **{{ felt.frist_materiale }}** – helst ved upload i bogføringsprogrammet.

## Vigtige frister
Vi holder styr på fristerne og giver jer besked i god tid. Jeres momsperiode er: **{{ kunde.momsperiode }}**. Vi sender jer en oversigt over årets frister.

Vi ser frem til samarbejdet.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
