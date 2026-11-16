---
{
  "title": "Løbende overvågning og opdatering af kundekendskab",
  "description": "Tjekliste til løbende overvågning af kundeforholdet og periodisk eller hændelsesudløst opdatering af kundekendskab (hvidvasklovens § 10, nr. 1, og § 11, stk. 1, nr. 5), herunder røde flag fra bogføring og årsafslutning.",
  "kind": "tjekliste",
  "references": ["Hvidvaskloven (LBK nr. 433 af 17/04/2026) §§ 10, nr. 1, 11, stk. 1, nr. 5, 15, 15 a, 25 og 30", "Erhvervsstyrelsens vejledning om hvidvaskloven", "Erhvervsstyrelsens vejledning om vurdering af formål og tilsigtede beskaffenhed"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "anledning", "label": "Anledning", "type": "select", "options": ["Periodisk opdatering", "Årsafslutning", "Ændrede forhold hos kunden", "Ny ydelse", "Usædvanlig transaktion/aktivitet"], "default": "Årsafslutning"},
    {"name": "risiko_tidligere", "label": "Hidtidig risikoklassifikation", "type": "select", "options": ["Lav", "Normal", "Forhøjet", "Høj"], "default": "Normal"},
    {"name": "seneste_kyc", "label": "Dato for seneste fulde kundekendskab", "type": "date"},
    {"name": "risiko_ny", "label": "Ny risikoklassifikation", "type": "select", "options": ["Uændret", "Lav", "Normal", "Forhøjet", "Høj"], "default": "Uændret"},
    {"name": "bemaerkninger", "label": "Bemærkninger", "type": "textarea"}
  ]
}
---
# Løbende overvågning – {{ kunde.navn }}

| | |
|---|---|
| Kunde | {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }} |
| Branche / brancherisiko | {{ kunde.branchetekst }} / {{ branche.hvidvask_risiko }} |
| Regnskabsår | {{ regnskab.aar }} |
| Nøgletal | Omsætning {{ regnskab.omsaetning }} · Resultat {{ regnskab.resultat }} · Balance {{ regnskab.balancesum }} · Egenkapital {{ regnskab.egenkapital }} |
| Anledning | {{ felt.anledning }} |
| Hidtidig risiko / seneste fulde KYC | {{ felt.risiko_tidligere }} / {{ felt.seneste_kyc }} |
| Udført af / dato | {{ medarbejder.navn }} / {{ dato.idag }} |

Transaktioner og aktiviteter i kundeforholdet skal overvåges for at sikre, at de stemmer med vores viden om kunden, dens forretning og risikoprofil, og dokumenter og oplysninger skal løbende ajourføres (§ 11, stk. 1, nr. 5). Kundekendskabsprocedurer gennemføres også, når kundens relevante omstændigheder ændrer sig, og i øvrigt på passende tidspunkter (§ 10, nr. 1). Frekvensen afhænger af risikoen.

## 1. Opdatering af stamoplysninger

- [ ] CVR-udskrift kontrolleret: navn, adresse, branchekode, ledelse, tegningsregel, revisor, status
- [ ] Ændringer i ejerforhold eller reelle ejere? ☐ Nej ☐ Ja – ny erklæring indhentet; uoverensstemmelser med CVR indberettet til Erhvervsstyrelsen (§ 15 a)
- [ ] Ny ledelse? ☐ Nej ☐ Ja – legitimation og PEP-erklæring indhentet
- [ ] Legitimation stadig gyldig
- [ ] PEP-screening gentaget – resultat: ________
- [ ] Sanktionsscreening gentaget – resultat: ________
- [ ] Negativ mediesøgning gentaget – resultat: ________
- [ ] Ændret branchekode – har den betydning for risiko eller risikobranchekravet i årsregnskabslovens § 135, stk. 5?

## 2. Stemmer aktiviteten med vores kundekendskab?

| Forhold | Ja/Nej | Kommentar |
|---|---|---|
| Omsætning og resultat svarer til det forventede (væsentlige udsving forklaret) | | |
| Lønsum og antal ansatte står mål med aktiviteten | | |
| Ingen usædvanligt store, komplekse eller usædvanlige transaktioner uden åbenbart økonomisk eller lovligt formål | | |
| Ingen større kontantindsætninger/-hævninger uden forklaring | | |
| Ingen betalinger til/fra højrisikolande eller uventede udenlandske parter | | |
| Ingen betalinger fra/til tredjemand, der ikke indgår i forretningen | | |
| Mellemregning med ejere/ledelse er forklaret (lån til ejere/ledelse er dokumenteret, forsvarlige og vurderet skattemæssigt, LL § 16 E) | | |
| Kapitalindskud og lån har dokumenteret oprindelse | | |
| Leverandørfakturaer er reelle (leverandørens CVR, ansatte, adresse, aktivitet) | | |
| Udgifter passer til forretningsmodellen | | |
| Ejeres privatforbrug/aktiver står mål med indtjeningen | | |
| Kunden leverer ønsket dokumentation uden usædvanlig modvilje | | |

{% if branche.kontantintensiv %}**Kontantintensiv branche:** Sammenhold kontantandel, bruttoavance og omsætning med tidligere år og branchen. Kontrollér, at kontantindsættelser i banken svarer til registreret kontantsalg. ☐ Udført{% endif %}
{% if branche.byggeri or branche.vikar or branche.rengoering or branche.transport %}**Underleverandører og arbejdskraft:** Gennemgå de største underleverandører (nystiftet, ingen ansatte, skiftende ledelse, opløst efter kort tid) og omsætning pr. ansat. ☐ Udført{% endif %}
{% if branche.bilhandel %}**Bilhandel:** Gennemgå store kontante handler, køb/salg med udlandet og lagerbog. ☐ Udført{% endif %}
{% if branche.ejendom or branche.investeringsejendomme %}**Ejendom:** Gennemgå køb/salg af ejendomme i året – finansiering, pris og modpart. ☐ Udført{% endif %}
{% if branche.holding %}**Holding:** Gennemgå nye kapitalandele, lån til/fra koncern og ejere og udenlandske investeringer. ☐ Udført{% endif %}

## 3. Konklusion

- [ ] Ingen forhold – kundekendskabet er ajourført
- [ ] Forhold, der kræver yderligere oplysninger fra kunden (oplysninger er anmodet den ________)
- [ ] Usædvanlige forhold – undersøgelse efter § 25 iværksat (se internt notat). **Kunden må ikke orienteres om undersøgelsen.**
- [ ] Kunden har ikke leveret de nødvendige oplysninger – forbindelsen vurderes afviklet (§ 15)

Ny risikoklassifikation: **{{ felt.risiko_ny }}**

Næste opdatering: ☐ om 1 år ☐ om 2 år ☐ om 3 år ☐ ved næste årsafslutning

{% if felt.bemaerkninger %}Bemærkninger: {{ felt.bemaerkninger }}{% endif %}

| Rolle | Navn | Dato | Underskrift |
|---|---|---|---|
| Udført af | {{ medarbejder.navn }} | {{ dato.idag }} | |
| Godkendt (ved ændret risiko) | | | |
