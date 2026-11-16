---
{
  "title": "Opsigelse af kundeforhold / ophør af samarbejde",
  "description": "Brev om ophør af samarbejdet (opsagt af kunden eller af os): ophørsdato, afslutning af igangværende opgaver, udlevering af materiale og dataeksport, adgange, fratræden som valgt revisor og hvidvaskdokumentation.",
  "kind": "brev",
  "references": ["Revisorloven § 18 (revisors fratræden)", "Selskabsloven §§ 144, 146 (valg og fratræden af revisor)", "Bogføringsloven § 12 (opbevaring i 5 år)", "Hvidvaskloven § 30 (opbevaring af kundekendskabsoplysninger)", "Selskabsloven § 88, stk. 1, nr. 3 (fravalg af revision)", "Databeskyttelsesforordningen (databehandleraftalen)"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "opsagt_af", "label": "Opsagt af", "type": "select", "options": ["Kunden", "Os"], "default": "Kunden"},
    {"name": "opsigelse_modtaget", "label": "Opsigelse modtaget/afgivet den", "type": "date"},
    {"name": "ophoersdato", "label": "Ophørsdato", "type": "date"},
    {"name": "begrundelse", "label": "Begrundelse (når vi opsiger)", "type": "textarea"},
    {"name": "valgt_revisor", "label": "Vi er valgt som revisor for selskabet", "type": "checkbox"},
    {"name": "igangvaerende", "label": "Opgaver vi afslutter inden ophør", "type": "textarea"},
    {"name": "ikke_afsluttet", "label": "Opgaver vi IKKE udfører (kunden skal selv sørge for)", "type": "textarea"},
    {"name": "slutfaktura", "label": "Slutafregning", "type": "text", "default": "Medgået tid frem til ophørsdatoen faktureres efter aftalen."},
    {"name": "eksport_dato", "label": "Adgang til bogføringsprogram lukkes den", "type": "date"}
  ]
}
---
{{ kunde.navn }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Ophør af samarbejdet

Kære {{ kunde.navn }}

{% if felt.opsagt_af == "Kunden" %}Vi bekræfter at have modtaget jeres opsigelse af samarbejdet den {{ felt.opsigelse_modtaget }}. Samarbejdet ophører den **{{ felt.ophoersdato }}**. Tak for samarbejdet indtil nu.{% else %}Vi skal hermed meddele, at vi opsiger samarbejdet med virkning fra den **{{ felt.ophoersdato }}**, jf. vores aftale{% if kunde.aftalereference %} ({{ kunde.aftalereference }}){% endif %}.

{{ felt.begrundelse }}{% endif %}

## Igangværende opgaver
Vi afslutter følgende opgaver inden ophør:
{{ felt.igangvaerende }}

Følgende opgaver udfører vi ikke, og I skal derfor selv sørge for dem eller aftale dem med jeres nye rådgiver:
{{ felt.ikke_afsluttet }}

Vær særligt opmærksom på kommende frister for moms (jeres momsperiode: {{ kunde.momsperiode }}){% if kunde.er_kapitalselskab %}, A-skat, acontoskat og indsendelse af årsrapport (næste frist: {{ regnskab.frist_aarsrapport }}){% else %}, A-skat, B-skat og selvangivelse{% endif %}.

{% if felt.valgt_revisor %}## Fratræden som valgt revisor
Vi er valgt som revisor for selskabet. Vores hverv består, indtil en ny revisor er tiltrådt, medmindre andet følger af lovgivningen, vedtægterne eller aftalen (revisorloven § 18, stk. 1). {% if felt.opsagt_af == "Os" %}Fratræder vi før hvervets udløb, giver vi hurtigst muligt Erhvervsstyrelsen meddelelse herom med en fyldestgørende forklaring på årsagen (selskabsloven § 146, stk. 2).{% else %}Selskabet skal snarest foranledige valg af ny revisor (selskabsloven § 146, stk. 3). Ophører vores hverv før udløbet, giver vi hurtigst muligt Erhvervsstyrelsen meddelelse herom med en forklaring på årsagen (selskabsloven § 146, stk. 2).{% endif %} Hvis selskabet ikke har pligt til revision og ønsker at fravælge revision, træffes beslutningen på generalforsamlingen (selskabsloven § 88, stk. 1, nr. 3).

Den tiltrædende revisor skal rette henvendelse til os, og vi har pligt til at oplyse grundene til vores fratræden og give adgang til alle relevante oplysninger om virksomheden (revisorloven § 18, stk. 2).
{% endif %}
## Jeres materiale og data
- Bilag og regnskabsmateriale, I har givet os, udleveres eller er allerede tilgængeligt i bogføringsprogrammet.
- I kan hente **alle jeres data** fra bogføringsprogrammet med funktionen "Eksportér alt" (SAF-T-fil pr. regnskabsår, saldobalancer, bilag og log). Vi anbefaler, at I gør det inden **{{ felt.eksport_dato }}**, hvor vores adgang ophører. Jeres egne brugere bevarer adgang efter aftalen.
- Husk, at regnskabsmaterialet skal opbevares i 5 år fra udgangen af det regnskabsår, det vedrører (bogføringsloven § 12), også når I skifter system.
- Vores arbejdspapirer tilhører os. Vi opbevarer dem samt kundekendskabsoplysninger efter hvidvaskloven i mindst 5 år efter forretningsforbindelsens ophør; personoplysninger slettes herefter, medmindre andet følger af anden lovgivning (hvidvaskloven § 30, stk. 2).

## Adgange og fuldmagter
Vi beder jer fjerne vores adgang til TastSelv Erhverv, Virk og netbank pr. {{ felt.ophoersdato }}. Vi fjerner selv vores rådgiveradgange, hvor vi kan. Jeres accept af databehandleraftalen ophører samtidig for de opgaver, vi ikke længere udfører.

## Slutafregning
{{ felt.slutfaktura }}

Har I spørgsmål til overdragelsen, er I velkomne til at kontakte {{ kunde.ansvarlig }}.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
