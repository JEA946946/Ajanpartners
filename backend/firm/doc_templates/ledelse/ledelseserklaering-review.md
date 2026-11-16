---
{
  "title": "Ledelseserklæring – review (ISRE 2400)",
  "description": "Skriftlig ledelseserklæring ved review af årsregnskab efter ISRE 2400 (Revideret), afsnit 61-65. Kortere end ved revision, men med de erklæringer standarden kræver og branchespecifikke punkter.",
  "kind": "brev",
  "references": ["ISRE 2400 (Revideret), afsnit 61-65", "Årsregnskabsloven", "Bogføringsloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "erklaeringsdato", "label": "Dato (samme som reviewerklæringen)", "type": "text", "default": "{{ dato.idag }}"},
    {"name": "har_bestyrelse", "label": "Selskabet har en bestyrelse (ApS)", "type": "checkbox", "default": false},
    {"name": "yderligere", "label": "Yderligere specifikke erklæringer (valgfrit)", "type": "textarea"}
  ]
}
---
**{{ firma.navn }}**
{{ firma.adresse }}
Att.: {{ medarbejder.navn }}

{{ felt.erklaeringsdato }}

# Ledelseserklæring

Denne erklæring afgives i forbindelse med jeres review af årsregnskabet for {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}, for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}, med henblik på, at I kan udtrykke en konklusion om, hvorvidt I er blevet opmærksomme på forhold, der giver jer grund til at mene, at årsregnskabet ikke giver et retvisende billede i overensstemmelse med årsregnskabsloven.

Vi bekræfter efter bedste overbevisning:

1. Vi har opfyldt vores ansvar for udarbejdelsen af årsregnskabet i overensstemmelse med årsregnskabsloven, som aftalt i opdragsbrevet.
2. Vi har givet jer alle relevante oplysninger og adgang som aftalt, og alle transaktioner er registreret i bogføringen og afspejlet i årsregnskabet.
3. Vores svar på jeres forespørgsler er fyldestgørende og korrekte.
4. Nærtstående parter og alle forbindelser og transaktioner med dem er oplyst til jer og behandlet korrekt i årsregnskabet.
5. Alle begivenheder efter balancedagen, der kræver regulering eller oplysning, er reguleret eller oplyst.
6. Væsentlige forpligtelser, kontraktlige forpligtelser, eventualforpligtelser og sikkerhedsstillelser er indregnet eller oplyst.
7. Vi er ikke bekendt med besvigelser, mistanke om besvigelser eller overtrædelser af love og øvrig regulering, som kan påvirke årsregnskabet, herunder skatte-, moms- og afgiftslovgivningen.
8. Vi har vurderet {% if kunde.er_kapitalselskab %}selskabets{% else %}virksomhedens{% endif %} evne til at fortsætte driften og er ikke bekendt med væsentlige usikkerheder ud over hvad der er oplyst i årsregnskabet.
9. De væsentlige forudsætninger for regnskabsmæssige skøn er rimelige.
{% if kunde.er_kapitalselskab %}10. Lån og sikkerhedsstillelser, som selskabet har ydet til kapitalejere, ledelsesmedlemmer eller disses nærtstående, er ydet i selskabets interesse og på forsvarlige vilkår, jf. selskabslovens §§ 115-118 og 127, og eventuelle lån ydet før 1. januar 2025 i strid med de dagældende regler i selskabslovens § 210 er tilbagebetalt med renter efter § 215, og udlodninger er sket i overensstemmelse med selskabsloven.
{% endif %}
{% if branche.lager or branche.igangvaerende_arbejder or branche.investeringsejendomme or branche.kontantintensiv or branche.momsfritaget %}## Branchespecifikke forhold

{% if branche.lager %}- Varebeholdningerne er optalt pr. {{ regnskab.slut }} og målt til kostpris, dog højst nettorealisationsværdi.
{% endif %}{% if branche.igangvaerende_arbejder %}- Igangværende arbejder er medtaget med salgsværdien af det udførte arbejde, og forventede tab er indregnet.
{% endif %}{% if branche.investeringsejendomme %}- Investeringsejendomme er målt til dagsværdi med markedsbaserede forudsætninger.
{% endif %}{% if branche.kontantintensiv %}- Alt kontantsalg er registreret fuldstændigt i kasseapparat/salgssystem.
{% endif %}{% if branche.momsfritaget %}- Delvis fradragsret for moms og lønsumsafgift er opgjort korrekt.
{% endif %}
{% endif %}{% if felt.yderligere %}## Øvrige forhold

{{ felt.yderligere }}

{% endif %}Med venlig hilsen

**{{ kunde.navn }}**

{% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %}**Direktion**

______________________________

**Bestyrelse**

______________________________
{% else %}**{% if kunde.er_kapitalselskab %}Direktion{% else %}Indehaver/ledelse{% endif %}**

______________________________
{% endif %}
