---
{
  "title": "Oplysningsskema til kunden – legitimation og dokumentation",
  "description": "Brev og skema til ny eller eksisterende kunde med anmodning om legitimation, ejer- og ledelsesoplysninger, formål med samarbejdet og dokumentation for midlernes oprindelse efter hvidvaskloven, inkl. oplysning om behandling af personoplysninger (§ 16).",
  "kind": "brev",
  "references": ["Hvidvaskloven (LBK nr. 433 af 17/04/2026) §§ 11, 14, 16, 18 og 30", "Databeskyttelsesforordningen art. 13"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "kontaktperson", "label": "Kontaktperson", "type": "text"},
    {"name": "anledning", "label": "Anledning", "type": "select", "options": ["Ny kunde", "Periodisk opdatering", "Ændrede forhold"], "default": "Ny kunde"},
    {"name": "frist", "label": "Svarfrist", "type": "date"},
    {"name": "upload", "label": "Hvordan sendes materialet", "type": "select", "options": ["Upload i bogføringsprogrammet under Dokumenter", "Sikker e-mail", "Medbringes til møde"], "default": "Upload i bogføringsprogrammet under Dokumenter"},
    {"name": "midler", "label": "Bed om dokumentation for midlernes oprindelse", "type": "checkbox", "default": false}
  ]
}
---
**{{ kunde.navn }}**
{% if felt.kontaktperson %}Att.: {{ felt.kontaktperson }}{% endif %}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Oplysninger til brug for kundekendskab

{% if felt.anledning == "Ny kunde" %}Velkommen som kunde hos {{ firma.navn }}. Som revisions- og regnskabsvirksomhed er vi omfattet af hvidvaskloven og skal derfor kende vores kunder, før vi kan gå i gang med opgaverne.{% else %}Vi er efter hvidvaskloven forpligtet til løbende at holde vores oplysninger om vores kunder opdaterede. Vi beder jer derfor bekræfte eller opdatere oplysningerne nedenfor.{% endif %} Det gælder alle vores kunder og er ikke udtryk for mistillid.

Vi beder jer sende oplysningerne og dokumenterne senest **{{ felt.frist }}**. Materialet sendes: {{ felt.upload }}. Send ikke pas eller CPR-numre i almindelig, ukrypteret e-mail.

## 1. Virksomheden

{% if kunde.er_kapitalselskab or kunde.selskabsform_kode == "forening" or kunde.selskabsform_kode == "fmba" %}- [ ] Gældende vedtægter
- [ ] Ejerbog/aktiebog eller oversigt over ejere med ejerandele
- [ ] Organisationsdiagram, hvis selskabet ejes gennem andre selskaber (helt op til de personer, der ejer i sidste ende)
- [ ] Udfyldt **erklæring om reelle ejere** (vedlagt)
{% if kunde.selskabsform_kode == "forening" %}- [ ] Referat fra seneste generalforsamling med valg af bestyrelse
{% endif %}{% endif %}{% if kunde.selskabsform_kode == "is" %}- [ ] Interessentskabskontrakt
{% endif %}- [ ] Seneste årsrapport eller regnskab (hvis I ikke er nystartede)
- [ ] Navn på jeres tidligere revisor/bogholder, og hvorfor I skifter

## 2. Personer

For {% if kunde.er_personlig %}ejeren/indehaveren{% if kunde.selskabsform_kode == "is" %} og alle interessenter{% endif %}{% else %}hver person i direktionen{% if kunde.selskabsform_kode == "as" %} og bestyrelsen{% endif %}, hver reel ejer og den, der er vores kontaktperson{% endif %}:

- [ ] Kopi af gyldigt **pas** eller **kørekort** (begge sider) – eller identifikation med MitID efter aftale med os
- [ ] Dokumentation for adresse, hvis den ikke fremgår af legitimationen (fx sundhedskort eller brev fra en offentlig myndighed højst 3 måneder gammelt)
- [ ] Udfyldt og underskrevet **PEP-erklæring** (vedlagt)
- [ ] Er en person ikke dansk statsborger: pas og eventuelt opholdsdokument

## 3. Om samarbejdet og jeres forretning

Besvar venligst kort:

| Spørgsmål | Svar |
|---|---|
| Hvad laver virksomheden (produkter/ydelser, kunder, leverandører)? | |
| Hvor foregår aktiviteten (Danmark, andre lande)? | |
| Forventet omsætning og antal ansatte det kommende år | |
| Handler I med kunder eller leverandører uden for EU? Hvilke lande? | |
| Modtager eller betaler I kontanter? Ca. hvor stor en andel? | |
| Hvilken bank bruger I? | |
| Hvilke ydelser ønsker I fra os, og hvad er formålet? | |

{% if branche.byggeri or branche.rengoering or branche.vikar or branche.transport %}| Bruger I underleverandører eller udenlandsk arbejdskraft? Er udenlandske virksomheder registreret i RUT? | |
{% endif %}{% if branche.kontantintensiv %}| Hvilket kassesystem bruger I, og hvor indsættes kontanterne? | |
{% endif %}{% if branche.bilhandel %}| Køber eller sælger I biler til/fra udlandet? | |
{% endif %}{% if branche.ejendom %}| Hvordan er jeres ejendomme finansieret? | |
{% endif %}

{% if felt.midler %}## 4. Midlernes oprindelse

Vi beder om dokumentation for, hvor midlerne til virksomheden kommer fra, fx:

- [ ] Stiftelseskapital, kapitalforhøjelser og lån fra ejere (kontoudtog, låneaftale)
- [ ] Køb af større aktiver (ejendomme, biler, maskiner) – købsaftale og finansiering
- [ ] Arv, gave, salg af virksomhed eller ejendom (skifteretsattest, gaveanmeldelse, slutseddel)
- [ ] Seneste årsopgørelse for ejeren
{% endif %}

## Sådan behandler vi jeres oplysninger

{{ firma.navn }} er dataansvarlig for de oplysninger, vi indsamler efter hvidvaskloven. Oplysningerne bruges kun til at forebygge hvidvask og finansiering af terrorisme og til at overholde vores lovpligtige forpligtelser (databeskyttelsesforordningens art. 6, stk. 1, litra c, og hvidvasklovens § 16). Vi opbevarer oplysningerne i 5 år efter kundeforholdets ophør og sletter dem derefter, medmindre andet er fastsat i anden lovgivning (§ 30, stk. 2). Oplysningerne kan efter loven videregives til Hvidvasksekretariatet og Erhvervsstyrelsen. I har ret til indsigt, berigtigelse og til at klage til Datatilsynet; retten til indsigt er begrænset for oplysninger om undersøgelser og underretninger efter hvidvaskloven (§ 25, stk. 4, og § 26, stk. 7). Læs mere i vores privatlivspolitik.

Hvis vi ikke modtager oplysningerne, kan vi efter hvidvaskloven ikke påbegynde eller fortsætte samarbejdet (§ 14, stk. 5).

Kontakt os gerne, hvis I har spørgsmål.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
{{ firma.telefon }} · {{ firma.email }}

Bilag: PEP-erklæring{% if kunde.er_kapitalselskab %} · Erklæring om reelle ejere{% endif %}
