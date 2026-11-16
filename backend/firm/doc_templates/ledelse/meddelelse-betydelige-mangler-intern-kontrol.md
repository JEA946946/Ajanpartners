---
{
  "title": "Meddelelse om betydelige mangler i intern kontrol (ISA 265)",
  "description": "Skriftlig meddelelse til den øverste ledelse og direktionen om betydelige mangler i den interne kontrol, som revisor har identificeret under revisionen. ISA 265 kræver skriftlig kommunikation rettidigt. Op til fire mangler med beskrivelse, mulig virkning og anbefaling; branchetypiske eksempler foreslås.",
  "kind": "brev",
  "references": ["ISA 265, afsnit 9-11", "ISA 315 (Revideret 2019)", "Selskabsloven §§ 115 og 118", "Bogføringsloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "har_bestyrelse", "label": "Selskabet har en bestyrelse (ApS)", "type": "checkbox", "default": false},
    {"name": "m1_titel", "label": "Mangel 1 – overskrift", "type": "text"},
    {"name": "m1_beskrivelse", "label": "Mangel 1 – beskrivelse", "type": "textarea"},
    {"name": "m1_virkning", "label": "Mangel 1 – mulig virkning", "type": "textarea"},
    {"name": "m1_anbefaling", "label": "Mangel 1 – anbefaling", "type": "textarea"},
    {"name": "m2_titel", "label": "Mangel 2 – overskrift", "type": "text"},
    {"name": "m2_beskrivelse", "label": "Mangel 2 – beskrivelse", "type": "textarea"},
    {"name": "m2_virkning", "label": "Mangel 2 – mulig virkning", "type": "textarea"},
    {"name": "m2_anbefaling", "label": "Mangel 2 – anbefaling", "type": "textarea"},
    {"name": "m3_titel", "label": "Mangel 3 – overskrift", "type": "text"},
    {"name": "m3_beskrivelse", "label": "Mangel 3 – beskrivelse", "type": "textarea"},
    {"name": "m3_virkning", "label": "Mangel 3 – mulig virkning", "type": "textarea"},
    {"name": "m3_anbefaling", "label": "Mangel 3 – anbefaling", "type": "textarea"},
    {"name": "m4_titel", "label": "Mangel 4 – overskrift", "type": "text"},
    {"name": "m4_beskrivelse", "label": "Mangel 4 – beskrivelse", "type": "textarea"},
    {"name": "m4_virkning", "label": "Mangel 4 – mulig virkning", "type": "textarea"},
    {"name": "m4_anbefaling", "label": "Mangel 4 – anbefaling", "type": "textarea"},
    {"name": "svarfrist", "label": "Frist for ledelsens tilbagemelding", "type": "text"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"}
  ]
}
---
**{{ kunde.navn }}**
Att.: {% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %}bestyrelsen og direktionen{% else %}{{ kunde.ledelsesorgan }}{% endif %}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Meddelelse om betydelige mangler i den interne kontrol

I forbindelse med vores revision af årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} har vi identificeret mangler i den interne kontrol, som vi efter en faglig vurdering anser for betydelige, og som vi derfor skal meddele jer skriftligt, jf. ISA 265.

Formålet med vores revision er at udtrykke en konklusion om årsregnskabet. Vi har i den forbindelse taget den interne kontrol i betragtning for at kunne tilrettelægge revisionshandlinger, der er passende efter omstændighederne, men ikke med henblik på at udtrykke en konklusion om den interne kontrols effektivitet. Meddelelsen omfatter derfor alene de mangler, vi er blevet opmærksomme på under revisionen, og er ikke en udtømmende liste over alle mangler, der måtte findes.

## Identificerede betydelige mangler

{% if felt.m1_beskrivelse %}### 1. {{ felt.m1_titel }}

**Observation:** {{ felt.m1_beskrivelse }}

**Mulig virkning:** {{ felt.m1_virkning }}

**Anbefaling:** {{ felt.m1_anbefaling }}

{% endif %}{% if felt.m2_beskrivelse %}### 2. {{ felt.m2_titel }}

**Observation:** {{ felt.m2_beskrivelse }}

**Mulig virkning:** {{ felt.m2_virkning }}

**Anbefaling:** {{ felt.m2_anbefaling }}

{% endif %}{% if felt.m3_beskrivelse %}### 3. {{ felt.m3_titel }}

**Observation:** {{ felt.m3_beskrivelse }}

**Mulig virkning:** {{ felt.m3_virkning }}

**Anbefaling:** {{ felt.m3_anbefaling }}

{% endif %}{% if felt.m4_beskrivelse %}### 4. {{ felt.m4_titel }}

**Observation:** {{ felt.m4_beskrivelse }}

**Mulig virkning:** {{ felt.m4_virkning }}

**Anbefaling:** {{ felt.m4_anbefaling }}

{% endif %}{% if not felt.m1_beskrivelse %}*Udfyld mindst én mangel. Typiske betydelige mangler i virksomheder af denne type:*

- Manglende funktionsadskillelse mellem bogføring, betalinger og afstemninger, uden kompenserende kontrol fra ledelsen.
- Manglende eller forsinkede månedlige afstemninger af bank, debitorer, kreditorer og skyldige skatter og afgifter.
- Utilstrækkelig styring af brugeradgange og godkendelse i netbank og bogføringssystem, herunder delte log-ins.
{% if branche.kontantintensiv %}- Kontantsalg registreres ikke fuldstændigt, eller daglige kasseafstemninger og z-rapporter mangler.
{% endif %}{% if branche.lager %}- Lagerregistrering og -optælling er ikke pålidelig, og der foretages ingen løbende vurdering af ukurans.
{% endif %}{% if branche.igangvaerende_arbejder %}- Der mangler projektstyring med efterkalkulation og løbende vurdering af færdiggørelsesgrad og tab.
{% endif %}{% if branche.momsfritaget %}- Opgørelsen af delvis momsfradrag og lønsumsafgift er ikke dokumenteret.
{% endif %}
{% endif %}## Ledelsens opfølgning

Vi anbefaler, at ledelsen tager stilling til manglerne og iværksætter de nødvendige tiltag. Vi beder om en skriftlig tilbagemelding om de planlagte tiltag senest {{ felt.svarfrist }}. Vi vil følge op på manglerne ved næste revision.{% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %} Forholdene er tillige omtalt i revisionsprotokollen.{% endif %}

Meddelelsen er udarbejdet til brug for ledelsen og bør ikke udleveres til tredjemand uden vores samtykke.

Med venlig hilsen

**{{ firma.navn }}**

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
