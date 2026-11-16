---
{
  "title": "Afvikling af kundeforhold ved manglende kundekendskab",
  "description": "Rykker og afviklingsbrev til kunde, der ikke leverer oplysninger til kundekendskab (hvidvasklovens §§ 14-15), samt intern vurdering af, om afviklingen giver grundlag for underretning. Brevet er neutralt og afslører ikke en eventuel mistanke.",
  "kind": "brev",
  "references": ["Hvidvaskloven (LBK nr. 433 af 17/04/2026) §§ 14, 15, 26, 30 og 38", "Revisorloven § 18, stk. 2", "Selskabsloven § 146"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "trin", "label": "Brevtype", "type": "select", "options": ["Rykker", "Meddelelse om ophør"], "default": "Rykker"},
    {"name": "anmodet_dato", "label": "Dato for første anmodning", "type": "date"},
    {"name": "mangler", "label": "Manglende oplysninger/dokumenter", "type": "textarea"},
    {"name": "frist", "label": "Ny frist (rykker) / ophørsdato (meddelelse)", "type": "date"},
    {"name": "er_revisor", "label": "Vi er valgt som revisor for kunden", "type": "checkbox", "default": false}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

{% if felt.trin == "Rykker" %}# Påmindelse – manglende oplysninger til kundekendskab

Den {{ felt.anmodet_dato }} bad vi jer om oplysninger og dokumenter, som vi efter hvidvaskloven skal have for at kunne samarbejde med jer. Vi har endnu ikke modtaget:

{{ felt.mangler }}

Vi beder jer sende materialet senest **{{ felt.frist }}**.

Vi gør opmærksom på, at vi efter hvidvaskloven ikke må fortsætte et kundeforhold, hvis vi ikke kan gennemføre de lovpligtige kundekendskabsprocedurer (§§ 14-15). Modtager vi ikke materialet inden fristen, vil vi derfor være nødt til at afslutte samarbejdet.

Kontakt os gerne, hvis der er spørgsmål, eller hvis I har brug for hjælp til at finde dokumenterne.
{% else %}# Ophør af samarbejdet

Vi har flere gange bedt jer om oplysninger, som vi efter hvidvaskloven skal have for at kunne fortsætte samarbejdet, senest med frist den {{ felt.anmodet_dato }}. Da vi ikke har modtaget oplysningerne, er vi forpligtet til at afslutte kundeforholdet (hvidvasklovens § 14).

Samarbejdet ophører derfor den **{{ felt.frist }}**. Vi afslutter ikke igangværende opgaver efter denne dato.

{% if felt.er_revisor %}Vi fratræder samtidig som revisor for selskabet og giver Erhvervsstyrelsen meddelelse herom, jf. selskabslovens § 146. Selskabet skal sørge for at vælge en ny revisor, hvis det er revisionspligtigt. En ny revisor skal rette henvendelse til os, jf. revisorlovens § 18, stk. 2.
{% endif %}
Selskabets eget materiale udleveres efter aftale, og jeres egne brugere kan fortsat eksportere alle data fra bogføringsprogrammet. Udestående honorar forfalder ved ophøret.
{% endif %}

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}

* * *

### Intern vurdering (sendes ikke)

- [ ] Kunden har fået mindst én rykker med rimelig frist
- [ ] Skyldes manglende oplysninger blot uorden, eller er der tegn på, at kunden vil skjule ejere, midlernes oprindelse eller aktiviteter?
- [ ] Er der grundlag for mistanke? ☐ Nej ☐ Ja – udfyld internt notat og underret Hvidvasksekretariatet (§ 26) **før** afviklingen, og formulér brevet neutralt (§ 38)
- [ ] Partner har godkendt ophøret – navn/dato: ________
- [ ] Revisors adgang til kundens bøger afsluttet ved ophørsdatoen
- [ ] KYC-materiale og korrespondance opbevares i 5 år (§ 30)
