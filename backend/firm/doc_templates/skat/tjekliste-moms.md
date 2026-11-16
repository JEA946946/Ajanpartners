---
{
  "title": "Tjekliste – moms og lønsumsafgift",
  "description": "Periodisk og årlig momsafstemning: angivelse og frister, fradragsret, repræsentation, EU-handel, delvis fradrag ved momsfrie aktiviteter, byggeri (pålægsmoms, omvendt betalingspligt ved udenlandske leverandører), brugtmoms ved bilhandel og lønsumsafgift.",
  "kind": "tjekliste",
  "references": ["Momsloven (ML) §§ 4, 13, 37, 38, 42, 46, 69-71", "Momsbekendtgørelsen", "Lønsumsafgiftsloven", "Opkrævningsloven", "Bogføringsloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "periode", "label": "Momsperiode der afstemmes", "type": "text"},
    {"name": "salgsmoms", "label": "Salgsmoms iflg. bogføring (kr.)", "type": "number"},
    {"name": "koebsmoms", "label": "Købsmoms iflg. bogføring (kr.)", "type": "number"},
    {"name": "angivet", "label": "Angivet tilsvar (kr.)", "type": "number"},
    {"name": "fradragsprocent", "label": "Foreløbig fradragsprocent (delvis fradrag)", "type": "number"},
    {"name": "loensumsmetode", "label": "Lønsumsafgift – metode", "type": "select", "options": ["Ikke relevant", "Metode 1 (organisationer, fonde, foreninger m.fl.)", "Metode 2 (finansiel virksomhed)", "Metode 3 (aviser)", "Metode 4 (øvrige – lønsum + overskud)"], "default": "Ikke relevant"}
  ]
}
---
# Tjekliste – moms {{ felt.periode }}

**Kunde:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }} · **Momsperiode:** {{ kunde.momsperiode }}
**Udarbejdet af:** {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Angivelse og frister
- [ ] Momsperiode er korrekt efter omsætningen: halvårlig (under 5 mio. kr.), kvartalsvis (5-50 mio. kr.), månedlig (over 50 mio. kr.); nye virksomheder starter som udgangspunkt kvartalsvis.
- [ ] Frister: halvår – 1. september og 1. marts; kvartal – den 1. i den 3. måned efter kvartalet (fx 1. juni for 1. kvartal); måned – den 25. i den følgende måned. Også 0-angivelser skal indsendes.
- [ ] Angivelse via TastSelv Erhverv (eller system-til-system) og betaling til skattekontoen senest på fristdagen; betalingen skal være på skattekontoen ved fristens udløb.

## 2. Afstemning
| | Kr. |
|---|---|
| Salgsmoms iflg. bogføring | {{ felt.salgsmoms }} |
| Moms af EU-køb og ydelser fra udlandet (erhvervelsesmoms/omvendt betalingspligt) | |
| ÷ Købsmoms iflg. bogføring | -{{ felt.koebsmoms }} |
| ÷ Fradrag for erhvervelsesmoms | |
| Energiafgifter m.v. (godtgørelse) | |
| **Tilsvar iflg. bogføring** | |
| Angivet tilsvar | {{ felt.angivet }} |
| **Difference** (forklares) | |

- [ ] Momskonti afstemt til angivelserne for alle perioder i året; årsafstemning af omsætning × 25 % mod salgsmoms.
- [ ] Rubrik A/B/C (EU-køb/-salg og eksport) afstemt; EU-salgsliste (listesystemet) indberettet for varer og ydelser til momsregistrerede i EU.
- [ ] Fejl i tidligere perioder korrigeret i TastSelv (ikke blot i næste periode, hvis beløbet er væsentligt).

## 3. Fradragsret (ML § 37) og begrænsninger
- [ ] Gyldige fakturaer med køberens navn og momsbeløb (ML § 52 a / momsbekendtgørelsen) – kreditnotaer og forudbetalinger håndteret korrekt.
- [ ] Ingen fradrag for: kost til ejer/personale, gaver over bagatelgrænsen, personbiler (undtagen særlige erhverv), bolig for ejer/personale, private udgifter (ML § 42).
- [ ] Repræsentation: 25 % fradrag for hotel- og restaurationsydelser, ellers ingen fradrag (ML § 42, stk. 2).
- [ ] Biler: kun fradrag for varebiler på gule plader; leasing af personbil – begrænset fradrag for erhvervsmæssig brug (ML § 42); brændstof og reparation med erhvervsmæssig andel.
- [ ] Blandede udgifter (telefon, internet, kontor i hjemmet) – kun erhvervsmæssig andel.
- [ ] Investeringsgoder (fast ejendom og maskiner > 100.000 kr. ekskl. moms) – reguleringsforpligtelse registreret (ML §§ 43-44; 5 år for driftsmidler, 10 år for fast ejendom).

{% if branche.momsfritaget %}
## 4. Momsfrie aktiviteter og delvis fradrag ({{ branche.navn }})
Selskabet driver helt eller delvis momsfri virksomhed (ML § 13).
- [ ] Afgrænsning af momsfrie og momspligtige aktiviteter (fx sundhedsydelser vs. kosmetisk behandling, undervisning vs. kursusvirksomhed, udlejning af fast ejendom vs. frivillig registrering, finansielle ydelser vs. rådgivning).
- [ ] Udgifter fordelt på (a) ren momspligtig – fuldt fradrag, (b) ren momsfri – intet fradrag, (c) fællesudgifter – delvis fradrag efter ML § 38, stk. 1.
- [ ] Fradragsprocent = momspligtig omsætning / samlet omsætning (oprundet til nærmeste hele procent). Foreløbig procent i år: {{ felt.fradragsprocent }} %. Endelig procent opgøres efter årets udløb, og fradraget reguleres i første periode i det nye regnskabsår.
- [ ] Investeringsgoder reguleres årligt ved ændret fradragsprocent.
- [ ] Frivillig momsregistrering for udlejning af erhvervslokaler vurderet (ML § 51).
- [ ] **Lønsumsafgift:** Momsfritaget virksomhed skal registreres for og betale lønsumsafgift (se afsnit 7).
{% endif %}

{% if branche.byggeri %}
## 5. Byggeri
- [ ] **Byggeri for egen regning (ML §§ 6-7 – pålægsmoms):** Ved salg af nye bygninger og byggegrunde er salget momspligtigt (ML § 13, stk. 1, nr. 9). Ved byggeri for egen regning med henblik på udlejning/salg skal der afregnes moms af værdien af egne ydelser (pålægsmoms). Kontrollér om virksomheden har sådan aktivitet.
- [ ] **Omvendt betalingspligt:** Danmark har ikke generel indenlandsk omvendt betalingspligt for byggeydelser. Ved køb af bygge- og anlægsydelser fra udenlandske virksomheder uden dansk momsregistrering betaler den danske momsregistrerede køber momsen (ML § 46, stk. 1). Køb af metalskrot, guld, CO2-kvoter, mobiltelefoner m.v. fra danske leverandører er omfattet af indenlandsk omvendt betalingspligt (ML § 46, stk. 1).
- [ ] Udenlandske underentreprenører er registreret i RUT (Registret for Udenlandske Tjenesteydere); kopi af RUT-kvittering indhentet.
- [ ] Acontofaktureringer og igangværende arbejder: moms afregnes ved fakturering/betaling efter faktureringsreglerne, ikke ved regnskabsmæssig indtægtsførsel.
- [ ] Byggeleverancer til private: korrekt moms på arbejdsløn og materialer; ingen momsfri "sort" betaling.
{% endif %}

{% if branche.bilhandel %}
## 6. Bilhandel – brugtmoms (ML §§ 69-71)
- [ ] Brugte biler købt af private eller købt under brugtmomsordningen: moms af avancen (salgspris ÷ indkøbspris, × 20 %); ingen købsmoms ved indkøb.
- [ ] Lagerregnskab/fortegnelse pr. bil (købs- og salgspris, sælger, køber) opfylder kravene til brugtmomsordningen; bilag opbevares.
- [ ] Fakturaer under brugtmoms angiver "Brugtmoms – brugte genstande" og ikke momsbeløbet.
- [ ] Negativ avance kan ikke modregnes i andre biler (individuel avanceberegning).
- [ ] Biler købt med fuld moms (fx fra leasingselskaber): almindelig moms ved salg.
- [ ] Nye transportmidler til/fra EU: særlige regler (moms i bestemmelseslandet); registreringsafgift og eksportgodtgørelse afstemt med Motorstyrelsen.
- [ ] Demobiler og egne biler: privat brug og momsregulering vurderet.
{% endif %}

{% if branche.restauration or branche.hotel %}
## Hotel og restauration
- [ ] Salg af mad og drikke: 25 %; ingen nedsat sats i Danmark. Drikkepenge og serviceafgift behandlet korrekt.
- [ ] Kasseapparatets Z-rapporter afstemt til salgsmoms; kortindløsning afstemt til omsætning.
{% endif %}

## 7. Lønsumsafgift
{% if felt.loensumsmetode == "Ikke relevant" %}{% if branche.momsfritaget %}- [ ] **OBS:** Virksomheden er i en momsfritaget branche – vurdér registreringspligt for lønsumsafgift.{% else %}- [ ] Ikke relevant (virksomheden er fuldt momspligtig).{% endif %}
{% else %}
Metode: **{{ felt.loensumsmetode }}**

| Metode | Grundlag | Sats (kontrollér for indkomståret) |
|---|---|---|
| 1 – organisationer, fonde, foreninger m.fl. | Lønsum | 6,37 % |
| 2 – finansiel virksomhed | Lønsum | Forhøjet sats for finanssektoren |
| 3 – udgivelse/import af aviser | Omsætning | Særlig sats |
| 4 – øvrige (fx sundhed, undervisning, ejendomshandel, personbefordring) | Lønsum + skattemæssigt overskud (÷ underskud), med reguleringer | 4,12 % |

- [ ] Registrering for lønsumsafgift ved momsfrie aktiviteter (lønsumsafgiftsloven § 1); bagatelgrænse for registrering (årligt grundlag) kontrolleret.
- [ ] Metode 4: kvartalsvis acontoangivelse af lønsum; årlig angivelse af overskud efter indkomstårets udløb; reguleringer (fx renter, afskrivninger, udbytte) kontrolleret.
- [ ] Ved delvis momspligt: kun lønsum/overskud vedrørende momsfri aktivitet medregnes (forholdsmæssig fordeling).
- [ ] Lønsumsafgift indgår som fradragsberettiget omkostning i skatteopgørelsen.
{% endif %}

## 8. Konklusion
- [ ] Ingen væsentlige differencer / differencer korrigeret.
- [ ] Bemærkninger til kunden: \_\_\_\_\_\_
