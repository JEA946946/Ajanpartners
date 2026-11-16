---
{
  "title": "Ledelseserklæring – opstilling (ISRS 4410)",
  "description": "Ledelsens bekræftelse ved opstilling af årsregnskab efter ISRS 4410. Ikke krævet af standarden, men god praksis: dokumenterer, at oplysningerne er fuldstændige og at ledelsen har godkendt regnskabet og væsentlige skøn. Også til personligt ejede virksomheder.",
  "kind": "brev",
  "references": ["ISRS 4410 (Revideret), afsnit 24-25 og 37", "Bogføringsloven", "Årsregnskabsloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "erklaeringsdato", "label": "Dato", "type": "text", "default": "{{ dato.idag }}"},
    {"name": "har_bestyrelse", "label": "Selskabet har en bestyrelse (ApS)", "type": "checkbox", "default": false},
    {"name": "privat_andel", "label": "Privat andel af bil, telefon, bolig m.v. (personlig virksomhed)", "type": "textarea"},
    {"name": "yderligere", "label": "Yderligere bekræftelser (valgfrit)", "type": "textarea"}
  ]
}
---
**{{ firma.navn }}**
{{ firma.adresse }}
Att.: {{ medarbejder.navn }}

{{ felt.erklaeringsdato }}

# Ledelsens bekræftelse ved opstilling af årsregnskab

I forbindelse med jeres opstilling af årsregnskabet for {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}, for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} bekræfter vi:

1. Vi har ansvaret for årsregnskabet og for nøjagtigheden og fuldstændigheden af de bogføringsdata og øvrige oplysninger, vi har givet jer til brug for opstillingen.
2. Alle indtægter og udgifter, aktiver og forpligtelser er registreret i bogføringen, og bogføringen og opbevaringen af regnskabsmateriale opfylder bogføringslovens krav.
3. Vi har gennemgået og godkendt årsregnskabet, herunder de væsentlige regnskabsmæssige skøn og den anvendte regnskabspraksis.
4. Vi har oplyst jer om alle forpligtelser, garantier, kautioner, sikkerhedsstillelser, verserende tvister og begivenheder efter balancedagen, som kan påvirke årsregnskabet.
5. Moms, A-skat, arbejdsmarkedsbidrag og øvrige skatter og afgifter er angivet og afregnet, og vi er ikke bekendt med uafklarede forhold over for Skattestyrelsen.
6. Vi er ikke bekendt med usikkerhed om {% if kunde.er_kapitalselskab %}selskabets{% else %}virksomhedens{% endif %} evne til at fortsætte driften ud over det, der er oplyst i årsregnskabet.
{% if kunde.er_kapitalselskab %}7. Vi har oplyst jer om alle lån, mellemregninger og sikkerhedsstillelser til kapitalejere, ledelsesmedlemmer og disses nærtstående.
{% else %}7. Private udgifter er ikke medtaget i regnskabet, og den private andel af blandede udgifter er udskilt.{% if felt.privat_andel %} Den private andel er opgjort således: {{ felt.privat_andel }}{% endif %}
{% endif %}
{% if branche.lager or branche.igangvaerende_arbejder or branche.kontantintensiv or branche.momsfritaget or branche.investeringsejendomme or branche.landbrug %}Vi bekræfter endvidere:

{% endif %}{% if branche.lager %}- Varelageret er optalt pr. {{ regnskab.slut }}, og optællingslisten er udleveret til jer.
{% endif %}{% if branche.igangvaerende_arbejder %}- Igangværende arbejder er opgjort pr. projekt og udleveret til jer.
{% endif %}{% if branche.kontantintensiv %}- Alt kontantsalg er registreret i kasseapparat/salgssystem, og kasseopgørelser er afstemt.
{% endif %}{% if branche.momsfritaget %}- Fordelingen mellem momspligtig og momsfritaget aktivitet er opgjort korrekt, og lønsumsafgift er afregnet.
{% endif %}{% if branche.investeringsejendomme %}- Grundlaget for værdiansættelsen af ejendommene er udleveret til jer.
{% endif %}{% if branche.landbrug %}- Optælling af besætninger og beholdninger samt oversigt over modtaget landbrugsstøtte er udleveret til jer.
{% endif %}
{% if felt.yderligere %}{{ felt.yderligere }}

{% endif %}Med venlig hilsen

**{{ kunde.navn }}**

{% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %}**Direktion**

______________________________

**Bestyrelse**

______________________________
{% else %}**{% if kunde.er_kapitalselskab %}Direktion{% else %}Indehaver/ledelse{% endif %}**

______________________________
{% endif %}
