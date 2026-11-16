---
{
  "title": "Fuldmagt til rådgiver – Skattestyrelsen",
  "description": "Fuldmagt fra kunde (person eller virksomhed) til revisionsfirmaet til at repræsentere kunden over for Skattestyrelsen, med vejledning til at give rådgiveradgang i TastSelv Borger/Erhverv via MitID/MitID Erhverv.",
  "kind": "brev",
  "references": ["Skatteforvaltningsloven", "Forvaltningsloven § 8 (partsrepræsentation)", "Databeskyttelsesforordningen art. 6", "Revisorloven § 10 (tavshedspligt)"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "fuldmagtsgiver", "label": "Fuldmagtsgiver (navn)", "type": "text", "default": "{{ kunde.navn }}"},
    {"name": "id_nr", "label": "CPR-nr. (person) eller CVR/SE-nr.", "type": "text", "default": "{{ kunde.cvr }}"},
    {"name": "type", "label": "Fuldmagtsgiver er", "type": "select", "options": ["Virksomhed", "Person"], "default": "Virksomhed"},
    {"name": "omfang", "label": "Omfang", "type": "select", "options": ["Alle skatte- og afgiftsforhold", "Kun selvangivelse/årsopgørelse og forskudsopgørelse", "Kun moms, A-skat og afgifter", "Konkret sag"], "default": "Alle skatte- og afgiftsforhold"},
    {"name": "sag", "label": "Konkret sag (hvis relevant)", "type": "text"},
    {"name": "gyldig_til", "label": "Gyldig til (tom = indtil tilbagekaldelse)", "type": "date"},
    {"name": "post", "label": "Rådgiveren må modtage post fra Skattestyrelsen (Digital Post) på kundens vegne", "type": "checkbox", "default": true}
  ]
}
---
# Fuldmagt

Undertegnede

**{{ felt.fuldmagtsgiver }}**
{% if felt.type == "Person" %}CPR-nr.{% else %}CVR/SE-nr.{% endif %} {{ felt.id_nr }}

giver hermed

**{{ firma.navn }}**, CVR-nr. {{ firma.cvr }}, {{ firma.adresse }}

og firmaets medarbejdere fuldmagt til at repræsentere mig/virksomheden over for Skattestyrelsen, Motorstyrelsen, Gældsstyrelsen og Skatteankestyrelsen vedrørende: **{{ felt.omfang }}**{% if felt.sag %} – {{ felt.sag }}{% endif %}.

Fuldmagten omfatter at:
- se og hente oplysninger i TastSelv/skat.dk, herunder årsopgørelser, forskudsopgørelser, indberetninger og skattekontoen,
- indberette og ændre selvangivelse/oplysningsskema, forskudsopgørelse, moms, A-skat, AM-bidrag og andre angivelser,
- føre korrespondance, give møde og afgive udtalelser i sager, herunder anmode om aktindsigt, bindende svar, henstand og genoptagelse, samt klage,
{% if felt.post %}- modtage breve og afgørelser fra myndighederne på mine/virksomhedens vegne.
{% endif %}

Fuldmagten giver ikke ret til at disponere over penge på skattekontoen til andre end fuldmagtsgiver.

Fuldmagten gælder {% if felt.gyldig_til %}til og med {{ felt.gyldig_til }}{% else %}indtil den tilbagekaldes skriftligt{% endif %}. Tilbagekaldelse har virkning, når den er modtaget af {{ firma.navn }} og myndigheden.

{{ firma.navn }} behandler personoplysninger i henhold til databehandler-/forretningsbetingelserne og har tavshedspligt.

Sted og dato: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.fuldmagtsgiver }}{% if felt.type == "Virksomhed" %} (underskrives efter tegningsreglen){% endif %}

---

## Vejledning: Sådan giver du os adgang digitalt
Ud over denne fuldmagt beder vi dig give os rådgiveradgang i TastSelv. Det tager få minutter (menunavnene kan ændre sig – søg efter "rådgiver" på skat.dk):

{% if felt.type == "Person" %}1. Log på **TastSelv Borger** på skat.dk med MitID.
2. Vælg **Profil** → **Rådgiver/fuldmagt** (giv adgang til rådgiver).
3. Indtast vores CVR-nr. **{{ firma.cvr }}**, vælg de områder, vi skal have adgang til, og evt. en udløbsdato.
4. Bekræft. Du kan til enhver tid se og fjerne adgangen samme sted.
{% else %}1. Log på **TastSelv Erhverv** på skat.dk med **MitID Erhverv** (som administrator eller bruger med rettighed til at give rådgiveradgang).
2. Vælg **Profil** → **Rettigheder/adgange** → **Giv rådgiver adgang**.
3. Indtast vores CVR-nr. **{{ firma.cvr }}**, og vælg de områder, vi skal have adgang til (fx moms, A-skat, selskabsskat, oplysningsskema, skattekonto).
4. Bekræft. Adgangen kan til enhver tid ændres eller fjernes.

*Har virksomheden ikke MitID Erhverv, kan den oprettes på mitid-erhverv.dk af en tegningsberettiget.*
{% endif %}

Har du spørgsmål, kan du kontakte {{ medarbejder.navn }} på {{ firma.telefon }} eller {{ firma.email }}.
