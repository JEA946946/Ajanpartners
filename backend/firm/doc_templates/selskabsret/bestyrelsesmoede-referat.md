---
{
  "title": "Referat af bestyrelsesmøde",
  "description": "Protokol for bestyrelsesmøde i A/S eller ApS med bestyrelse: beslutningsdygtighed, inhabilitet, økonomi og kapitalberedskab, årsrapport, reelle ejere, revisionsprotokollat.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 111, 115, 117, 124, 127, 128 og 131", "Selskabsloven § 58 a, stk. 4"],
  "legal_forms": ["as", "aps", "holding"],
  "industry_aware": true,
  "fields": [
    {"name": "moede_dato", "label": "Mødedato", "type": "date"},
    {"name": "moede_sted", "label": "Sted/form (fysisk, video, skriftligt)", "type": "text", "default": "selskabets adresse"},
    {"name": "moede_type", "label": "Mødetype", "type": "select", "options": ["Ordinært møde", "Årsregnskabsmøde", "Budgetmøde", "Konstituerende møde", "Ekstraordinært møde"], "default": "Ordinært møde"},
    {"name": "formand", "label": "Formand / mødeleder", "type": "text"},
    {"name": "deltagere", "label": "Deltagende bestyrelsesmedlemmer", "type": "textarea"},
    {"name": "afbud", "label": "Afbud", "type": "text"},
    {"name": "oevrige", "label": "Øvrige deltagere (direktion, revisor, sekretær)", "type": "textarea"},
    {"name": "referent", "label": "Referent", "type": "text"},
    {"name": "inhabilitet", "label": "Erklæret inhabilitet (navn og punkt)", "type": "text"},
    {"name": "oekonomi", "label": "Økonomi: resultat ift. budget, likviditet, prognose", "type": "textarea"},
    {"name": "nye_punkter", "label": "Øvrige dagsordenspunkter og beslutninger", "type": "textarea"},
    {"name": "naeste_moede", "label": "Næste møde", "type": "date"}
  ]
}
---
# Referat af bestyrelsesmøde

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}
{{ felt.moede_type }} den {{ felt.moede_dato }} – {{ felt.moede_sted }}

**Deltagere:** {{ felt.deltagere }}
**Afbud:** {{ felt.afbud }}
**Desuden deltog:** {{ felt.oevrige }}
**Referent:** {{ felt.referent }}

## 1. Mødets lovlighed og inhabilitet
Formanden, {{ felt.formand }}, konstaterede, at mødet var indkaldt i overensstemmelse med forretningsordenen, og at bestyrelsen var beslutningsdygtig, idet over halvdelen af samtlige medlemmer var repræsenteret (selskabslovens § 124, stk. 1). Beslutninger træffes ved simpelt flertal, medmindre vedtægterne eller forretningsordenen bestemmer andet.

Inhabilitet efter selskabslovens § 131: {{ felt.inhabilitet|default:"Ingen medlemmer erklærede sig inhabile." }}

## 2. Godkendelse af dagsorden og referat fra forrige møde
Dagsordenen blev godkendt. Referatet fra forrige møde blev godkendt og underskrevet.

{% if felt.moede_type == "Konstituerende møde" %}
## 3. Konstituering
Bestyrelsen konstituerede sig med {{ felt.formand }} som formand.{% if kunde.selskabsform_kode == "as" %} Formanden og næstformanden er ikke direktører i selskabet, og flertallet af bestyrelsens medlemmer er ikke direktører (selskabslovens § 111, stk. 1, nr. 1).{% endif %} Forretningsordenen blev gennemgået og underskrevet af alle medlemmer, og direktionsinstruksen blev bekræftet. Tegningsregel og eventuelle prokuraer blev gennemgået.
{% endif %}
## Direktionens orientering og økonomi
{{ felt.oekonomi }}

Bestyrelsen drøftede selskabets kapitalberedskab og likviditet, herunder om der er tilstrækkelig likviditet til at opfylde nuværende og fremtidige forpligtelser, efterhånden som de forfalder (selskabslovens § 115, nr. 5). Bestyrelsen vurderede, at kapitalberedskabet er forsvarligt.{% if branche.byggeri or branche.igangvaerende_arbejder %} Status på igangværende arbejder, tabsgivende kontrakter, sikkerhedsstillelser og garantier blev gennemgået.{% endif %}{% if branche.lager %} Varelagerets størrelse, omsætningshastighed og ukurans blev gennemgået.{% endif %}{% if branche.kontantintensiv %} Kontantbeholdning, kasseafstemninger og kontrol med kasseapparater blev gennemgået.{% endif %}{% if branche.ejendom %} Udlejningsgrad, vedligeholdelsesplan og værdiansættelse af ejendomme blev gennemgået.{% endif %}

{% if felt.moede_type == "Årsregnskabsmøde" %}
## Årsrapport {{ regnskab.aar }}
- Revisor gennemgik revisionen og revisionsprotokollatet. Bestyrelsen gennemgik protokollatet, og hvert medlem bekræfter ved sin underskrift at have gjort sig bekendt med det.
- Ledelsens regnskabserklæring til revisor blev godkendt og underskrevet.
- Årsrapporten med resultat {{ regnskab.resultat }} kr. og egenkapital {{ regnskab.egenkapital }} kr. blev godkendt og underskrevet af bestyrelse og direktion med henblik på fremlæggelse på den ordinære generalforsamling.
- Forslag til resultatdisponering og eventuelt udbytte blev vedtaget, efter at bestyrelsen havde vurderet forsvarligheden efter selskabslovens § 179.
- **Reelle ejere:** Resultatet af den årlige undersøgelse af selskabets reelle ejere blev fremlagt (selskabslovens § 58 a, stk. 4). Registreringen i CVR er korrekt / skal ændres som følger: \_\_\_\_\_\_.
- Tidspunkt for ordinær generalforsamling blev fastlagt, således at årsrapporten kan indsendes inden {{ regnskab.frist_aarsrapport }}.
{% endif %}
{% if felt.moede_type == "Budgetmøde" %}
## Budget
Direktionen fremlagde budget og likviditetsbudget for det kommende regnskabsår. Budgettet blev drøftet og godkendt med de bemærkninger, der fremgår nedenfor.
{% endif %}
## Øvrige punkter
{{ felt.nye_punkter }}

## Eventuelt og næste møde
Næste møde afholdes {{ felt.naeste_moede }}.

Referatet underskrives af samtlige tilstedeværende medlemmer (selskabslovens § 128). Et medlem, der ikke er enig i en beslutning, har ret til at få sin opfattelse ført til protokols.

{{ kunde.by }}, {{ felt.moede_dato }}

| Navn | Underskrift |
|---|---|
| {{ felt.formand }} (formand) | |
| | |
| | |
