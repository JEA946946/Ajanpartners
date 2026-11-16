---
{
  "title": "Materialeliste – personlig årsopgørelse",
  "description": "Liste til kunden over oplysninger og bilag til den personlige årsopgørelse/selvangivelse (lønmodtager, selvstændig, hovedaktionær, udlejning, aktier, udland), med frister og kontrolpunkter i TastSelv.",
  "kind": "brev",
  "references": ["Skattekontrolloven §§ 2-5", "Personskatteloven", "Virksomhedsskatteloven", "Aktieavancebeskatningsloven", "Ligningsloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "modtager", "label": "Modtager (navn)", "type": "text"},
    {"name": "indkomstaar", "label": "Indkomstår", "type": "text", "default": "{{ dato.aar }}"},
    {"name": "frist_materiale", "label": "Frist for fremsendelse af materiale", "type": "date"},
    {"name": "selvstaendig", "label": "Kunden har selvstændig virksomhed", "type": "checkbox", "default": true},
    {"name": "hovedaktionaer", "label": "Kunden er hovedaktionær/ejer af selskab", "type": "checkbox"},
    {"name": "udland", "label": "Kunden har indkomst/formue i udlandet", "type": "checkbox"},
    {"name": "udlejning", "label": "Kunden har udlejning (bolig/sommerhus/værelse)", "type": "checkbox"}
  ]
}
---
**{{ firma.navn }}**
{{ firma.adresse }} · {{ firma.telefon }} · {{ firma.email }}

{{ felt.modtager }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ kunde.by }}, {{ dato.idag }}

# Materialeliste til din årsopgørelse for {{ felt.indkomstaar }}

Kære {{ felt.modtager }}

For at vi kan udarbejde og kontrollere din årsopgørelse for {{ felt.indkomstaar }}, beder vi dig sende følgende til os senest **{{ felt.frist_materiale }}**. Har du allerede givet os adgang til din TastSelv, henter vi selv de forhåndsudfyldte oplysninger.

{% if felt.selvstaendig %}Som selvstændigt erhvervsdrivende har du **udvidet selvangivelse**. Fristen for oplysningsskemaet er **1. juli** i året efter indkomståret (skattekontrollovens § 4). Skattestyrelsen kan pålægge et dagligt tillæg ved for sen indberetning.{% else %}Er der fejl eller mangler i din forhåndsudfyldte årsopgørelse, skal de rettes senest **1. maj** i året efter indkomståret.{% endif %}

## 1. Generelle oplysninger
- [ ] Ændringer i civilstand, adresse, børn eller ægtefælles indkomst i året.
- [ ] Adgang til TastSelv (rådgiverfuldmagt) – se særskilt fuldmagt.
- [ ] Seneste årsopgørelse, hvis vi ikke har den.

## 2. Løn, pension og overførselsindkomster
- [ ] Lønsedler for december (eller årsoversigt) fra alle arbejdsgivere.
- [ ] Personalegoder: fri bil (bilens værdi og ibrugtagningsdato), fri telefon/internet, sundhedsforsikring, helårsbolig, sommerbolig, lystbåd.
- [ ] Udbetalinger fra pensionsordninger, efterløn, dagpenge, SU, honorarer og B-indkomst.
- [ ] Rejse- og befordringsgodtgørelse modtaget (skattefri/skattepligtig) og kørselsregnskab.

## 3. Fradrag
- [ ] Befordring mellem hjem og arbejde (antal dage og km) – Skattestyrelsen beregner ofte, men kontrollér.
- [ ] Faglige kontingenter, A-kasse, fagforening, arbejdsværelse, dobbelt husførelse.
- [ ] Indbetalinger til private pensionsordninger (rate/livsvarig) uden for arbejdsgiver.
- [ ] Underholdsbidrag (dokumentation), gaver til godkendte foreninger, servicefradrag (håndværker- og serviceydelser – betalt elektronisk med faktura).
- [ ] Renteudgifter til private lån, der ikke er indberettet (fx lån i udlandet eller mellem private).

## 4. Bolig og fast ejendom
- [ ] Køb/salg af ejendom (skøde, købsaftale, refusionsopgørelse) – vurdér parcelhusreglen.
{% if felt.udlejning %}- [ ] **Udlejning:** lejeindtægter pr. lejemål og periode, udgifter (ejendomsskat, forsikring, vedligeholdelse) og valg af metode (bundfradrag eller regnskabsmæssig opgørelse). Udlejning via platforme indberettes af platformen – kontrollér beløbet.
{% endif %}

## 5. Kapitalindkomst, aktier og kryptoaktiver
- [ ] Årsoversigter fra alle pengeinstitutter (renter, lån), også udenlandske.
- [ ] Aktier, investeringsbeviser, aktiesparekonto: depotoversigter og købs-/salgsnotaer for handler i året, især for værdipapirer, der ikke er indberettet (fx udenlandske depoter eller unoterede aktier).
- [ ] Kryptovaluta: komplet transaktionshistorik fra alle platforme og wallets; avance/tab opgøres pr. transaktion (FIFO).
- [ ] Lån mellem private, gældsbreve, valutalån.

{% if felt.hovedaktionaer %}## 6. Selskaber du ejer
- [ ] Udbytte modtaget og indeholdt udbytteskat (aktieindkomst: 27 % op til 79.400 kr. i 2026 / 158.800 kr. for ægtefæller, 42 % herover).
- [ ] Løn og personalegoder fra selskabet (kontrollér mod eIndkomst).
- [ ] Mellemregning med selskabet – private udgifter eller hævninger fra selskabet beskattes som løn/udbytte (ligningslovens § 16 E).
- [ ] Salg, køb eller stiftelse af kapitalandele (anskaffelsessum, salgssum, dato).
- [ ] Skattemæssig ejerskab og nærtstående transaktioner (husleje, lån, aktiver stillet til rådighed).
{% endif %}
{% if felt.selvstaendig %}## 7. Din virksomhed
- [ ] Adgang til bogføringen i bogføringssystemet ({{ firma.navn }} har adgang, hvis du bruger Ajan Partners Bogføring), eller fuld eksport med bilag.
- [ ] Kontoudtog for alle erhvervskonti pr. 31. december.
- [ ] Varelager pr. 31. december (optælling, opgjort til kostpris){% if branche.lager %} – **vigtigt for din branche**{% endif %}.
- [ ] Debitorer og kreditorer pr. 31. december, uafsluttede arbejder{% if branche.igangvaerende_arbejder %} (igangværende arbejder opgjort pr. sag){% endif %}.
- [ ] Køb og salg af driftsmidler, biler og ejendomme (fakturaer, salgsaftaler).
- [ ] Kørselsregnskab, hvis privat bil anvendes erhvervsmæssigt, eller privat brug af erhvervsbil (firmabil på gule/hvide plader).
- [ ] Lån, leasingaftaler og afdrag.
- [ ] Ønske om brug af virksomhedsordningen, kapitalafkastordningen eller personskattelovens regler – og forventede private hævninger.
- [ ] Hjemmekontor, telefon og internet: erhvervsmæssig andel.
{% if branche.kontantintensiv %}- [ ] Kasseopgørelser og Z-rapporter for hele året samt dokumentation for kontanthævninger og -indsætninger.
{% endif %}{% if branche.landbrug %}- [ ] Landbrugsstøtte, EU-tilskud, besætningsopgørelse og afgrødeoversigt.
{% endif %}{% if branche.byggeri %}- [ ] Oversigt over underentreprenører og RUT-registrerede udenlandske virksomheder.
{% endif %}{% endif %}
{% if felt.udland %}## 8. Udland
- [ ] Udenlandsk løn, pension, renter, udbytte og ejendom: årsoversigter og betalt udenlandsk skat (til lempelse).
- [ ] Ophold i udlandet (datoer) og evt. skattepligt i andet land.
- [ ] Udenlandske bank- og depotkonti (oplysningspligt efter skattekontrolloven).
{% endif %}

Har du spørgsmål, er du velkommen til at kontakte os. Vi sender et udkast til gennemsyn, inden noget indberettes.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
