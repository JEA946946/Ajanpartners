---
{
  "title": "Fratræden som revisor – brev til selskabet og meddelelse til Erhvervsstyrelsen",
  "description": "Revisors fratræden før valgperiodens udløb: brev til selskabets ledelse, meddelelse med begrundelse til Erhvervsstyrelsen (selskabslovens § 146, stk. 2) og intern tjekliste (god revisorskik, hvidvask, overdragelse).",
  "kind": "brev",
  "references": ["Revisorloven § 18, stk. 1-2", "Selskabsloven § 146, stk. 2-3", "ISA 210 og ISQM 1 (afslutning af kundeforhold)", "FSR – danske revisorers Etiske regler", "Revisorloven §§ 22, stk. 3, og 23", "Hvidvaskloven §§ 14, 26 og 38"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "andet"],
  "industry_aware": false,
  "fields": [
    {"name": "revisor_titel", "label": "Underskrivende revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "fratraedelsesdato", "label": "Fratrædelsesdato", "type": "date"},
    {"name": "begrundelse_type", "label": "Årsag", "type": "select", "options": ["Manglende betaling af honorar", "Manglende medvirken/adgang til oplysninger", "Tvivl om ledelsens integritet", "Uafhængighed kan ikke opretholdes", "Manglende kundekendskab efter hvidvaskloven", "Kapacitet/kompetence", "Selskabet har fravalgt revision", "Andet"], "default": "Manglende betaling af honorar"},
    {"name": "begrundelse", "label": "Fyldestgørende begrundelse (til Erhvervsstyrelsen og selskabet)", "type": "textarea"},
    {"name": "seneste_erklaering", "label": "Seneste afgivne erklæring (regnskabsår og type)", "type": "text"},
    {"name": "igangvaerende", "label": "Igangværende arbejde, der ikke afsluttes", "type": "textarea"}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Fratræden som revisor for {{ kunde.navn }}

Vi meddeler hermed, at {{ firma.navn }} fratræder som revisor for {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}, med virkning fra {{ felt.fratraedelsesdato }}, jf. revisorlovens § 18, stk. 2.

**Begrundelse:** {{ felt.begrundelse }}

{% if felt.begrundelse_type == "Manglende kundekendskab efter hvidvaskloven" %}Vi har ikke kunnet gennemføre de kundekendskabsprocedurer, som hvidvaskloven kræver, og vi er derfor forpligtet til at afslutte forretningsforbindelsen, jf. hvidvasklovens § 14, stk. 5.{% endif %}

{% if felt.igangvaerende %}Følgende igangværende arbejde afsluttes ikke af os: {{ felt.igangvaerende }}{% endif %}

Seneste erklæring afgivet af os: {{ felt.seneste_erklaering }}.

**Hvad selskabet skal gøre**

1. Vi giver Erhvervsstyrelsen meddelelse om vores fratræden med en fyldestgørende forklaring, jf. selskabslovens § 146, stk. 2.
2. Er selskabet fortsat revisionspligtigt – eller ønsker det en erklæring på årsregnskabet – skal der vælges en ny revisor på en generalforsamling, og valget skal anmeldes til Erhvervsstyrelsen. Er der ingen suppleant, skal det centrale ledelsesorgan snarest foranledige valg af ny revisor, og ekstraordinær generalforsamling skal indkaldes senest 2 uger efter, at fratrædelsen er meddelt selskabet (selskabslovens § 146, stk. 3).
3. Den nye revisor har pligt til at rette henvendelse til os, og vi har pligt til at oplyse grundene til vores fratræden og give adgang til relevante oplysninger, jf. revisorlovens § 18, stk. 2.
4. Årsrapporten skal fortsat indsendes rettidigt til Erhvervsstyrelsen (frist {{ regnskab.frist_aarsrapport }}). Manglende rettidig indsendelse kan medføre afgift til ledelsen (årsregnskabslovens § 151) og tvangsopløsning (selskabslovens § 225).

Selskabets regnskabsmateriale og øvrige dokumenter, som tilhører selskabet, udleveres efter aftale. Vores arbejdspapirer tilhører {{ firma.navn }}. Adgang til bogføringsprogrammet for selskabets egne brugere bevares, og selskabet kan eksportere alle data.

Ubetalte honorarer forfalder til betaling ved fratrædelsen.

Med venlig hilsen

{{ firma.navn }}

&nbsp;

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}

* * *

## Meddelelse til Erhvervsstyrelsen om revisors fratræden

*Meddelelsen skal gives til Erhvervsstyrelsen hurtigst muligt og vedlægges en fyldestgørende forklaring på årsagen (selskabslovens § 146, stk. 2). Kontrollér den aktuelle indsendelsesmåde på erhvervsstyrelsen.dk/virk.dk.*

Til Erhvervsstyrelsen

**Selskab:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}, {{ kunde.adresse }}, {{ kunde.postnr }} {{ kunde.by }}

**Revisor:** {{ firma.navn }}, CVR-nr. {{ firma.cvr }}, {{ firma.adresse }}

**Ansvarlig revisor:** {{ medarbejder.navn }}, {{ felt.revisor_titel }}

**Fratrædelsesdato:** {{ felt.fratraedelsesdato }}

{{ firma.navn }} meddeler hermed, jf. selskabslovens § 146, stk. 2, at vi er fratrådt som revisor for ovennævnte selskab før valgperiodens udløb.

**Begrundelse for fratrædelsen:** {{ felt.begrundelse }}

Seneste erklæring afgivet af os: {{ felt.seneste_erklaering }}.

Selskabet er orienteret skriftligt om fratrædelsen den {{ dato.idag }}.

{{ firma.navn }}, {{ dato.idag }}

______________________________
{{ medarbejder.navn }}, {{ felt.revisor_titel }}

* * *

## Intern tjekliste (arkiveres – sendes ikke)

- [ ] Fratræden strider ikke mod god revisorskik (fx ikke midt i en erklæringsopgave uden saglig grund, eller for at undgå at tage forbehold)
- [ ] Partner har godkendt fratrædelsen (ISQM 1 – afslutning af kundeforhold)
- [ ] Begrundelsen er saglig og fyldestgørende, og samme begrundelse gives til selskabet, Erhvervsstyrelsen og den tiltrædende revisor
- [ ] Er der forhold, der skal i revisionsprotokollen, før vi fratræder?
- [ ] Er der grundlag for underretning efter revisorlovens § 22 (ledelsens økonomiske kriminalitet)? Fratræder vi med en begrundet formodning om sådanne forhold, skal National Enhed for Særlig Kriminalitet straks underrettes om forholdet og grundene til fratrædelsen (§ 22, stk. 3)
- [ ] Er der mistanke om hvidvask/terrorfinansiering? I så fald underrettes Hvidvasksekretariatet (§ 26), og brevet til kunden må ikke afsløre underretningen (§ 38). Begrundelsen formuleres neutralt.
- [ ] Meddelelse til Erhvervsstyrelsen sendt – dato: ________
- [ ] Revisorregistrering i CVR ændret
- [ ] Revisorens adgang (AccessGrant) i bogføringsprogrammet afsluttet af partner
- [ ] Udlevering af kundens materiale, kvittering modtaget
- [ ] Opbevaring af arbejdspapirer i 5 år fra underskrivelse af erklæringen (revisorlovens § 23) og KYC i mindst 5 år efter forretningsforbindelsens ophør (hvidvasklovens § 30)
