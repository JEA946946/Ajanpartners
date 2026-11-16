---
{
  "title": "Rådgivningsbrev om lån til kapitalejer/ledelse (kapitalejerlån)",
  "description": "Brev til kapitalselskab om lån/debetsaldo til kapitalejer eller ledelse: selskabsretlige regler efter ophævelsen af SL §§ 210-212 pr. 1. januar 2025, beskatning efter ligningsloven § 16 E, konsekvenser og anbefalede handlinger.",
  "kind": "brev",
  "references": ["Ligningsloven § 16 E", "Selskabsloven §§ 115, 127, 206", "Lov nr. 1668 af 30. december 2024 (ophævelse af SL §§ 210-212)", "Lov nr. 749 af 20. juni 2025 (ændring af ligningsloven § 16 E)", "Kildeskatteloven § 65", "Årsregnskabsloven § 73", "Erklæringsbekendtgørelsen (omtale af ledelsesansvar)"],
  "legal_forms": ["aps", "as", "ivs", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "laantager", "label": "Låntager (navn og relation)", "type": "text"},
    {"name": "beloeb", "label": "Lånets/debetsaldoens størrelse (kr.)", "type": "number"},
    {"name": "opstaaet", "label": "Opstået (dato/periode)", "type": "text"},
    {"name": "hovedaktionaer", "label": "Låntager er personlig kapitalejer med bestemmende indflydelse eller nærtstående", "type": "checkbox", "default": true},
    {"name": "foer_2025", "label": "Lånet er helt eller delvist ydet før 1. januar 2025", "type": "checkbox"},
    {"name": "beskatning_som", "label": "Forventet skattemæssig behandling", "type": "select", "options": ["Udbytte", "Løn"], "default": "Udbytte"},
    {"name": "svar_frist", "label": "Vi beder om jeres tilbagemelding senest", "type": "date"}
  ]
}
---
{{ kunde.navn }}
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Lån fra selskabet til {{ felt.laantager }}

Kære {{ kunde.ledelsesorgan }}

Under vores arbejde med {% if regnskab.aar %}regnskabet for {{ regnskab.aar }}{% else %}bogføringen{% endif %} har vi konstateret, at selskabet har et tilgodehavende hos **{{ felt.laantager }}** på **{{ felt.beloeb }} kr.**, opstået {{ felt.opstaaet }}. Tilgodehavendet er opstået ved {{ felt.laantager }}s private hævninger/udlæg eller ved et lån. Vi vil med dette brev orientere jer om reglerne og anbefale, hvordan forholdet bringes i orden.

## Selskabsretten
Selskabslovens særlige regler om kapitalejerlån (§§ 210-212) er ophævet med virkning fra 1. januar 2025. Det betyder, at et selskab i dag kan yde lån til kapitalejere og ledelse uden at opfylde de tidligere særlige betingelser. Ledelsen skal dog stadig sikre, at:
- selskabets **kapitalberedskab** til enhver tid er forsvarligt, herunder at der er tilstrækkelig likviditet til at opfylde selskabets forpligtelser (SL § 115, nr. 5),
- dispositionen ikke er åbenbart egnet til at skaffe låntager en **utilbørlig fordel** på andre kapitalejeres eller selskabets bekostning (SL § 127), og
- lånet dokumenteres og ydes på **forretningsmæssige vilkår** (markedsrente, sikkerhed, tilbagebetalingsplan), hvilket understøtter vurderingen efter de to første punkter.

Selvfinansieringsreglerne (SL §§ 206-215) gælder fortsat: selskabet må ikke låne penge ud til køb af kapitalandele i selskabet selv, medmindre betingelserne herfor er opfyldt.
{% if felt.foer_2025 %}
Lånet er helt eller delvist ydet før 1. januar 2025, hvor de dagældende regler i SL §§ 210-212 gjaldt. Vi vurderer den del af lånet konkret efter de dagældende regler og anbefaler, at forholdet afklares med os, før årsrapporten underskrives.
{% endif %}
{% if felt.hovedaktionaer %}## Skat – det vigtigste punkt
Lån fra et selskab til en **personlig kapitalejer med bestemmende indflydelse** (eller dennes nærtstående) beskattes efter **ligningsloven § 16 E** som om, beløbet var udbetalt som **{{ felt.beskatning_som|lower }}**. Det gælder, uanset om lånet er selskabsretligt lovligt, og uanset om det senere tilbagebetales. Undtaget er bl.a. lån, der er led i en sædvanlig forretningsmæssig disposition.

Konsekvenser:
- Beløbet beskattes hos {{ felt.laantager }} som {{ felt.beskatning_som|lower }}.
{% if felt.beskatning_som == "Udbytte" %}- Selskabet skal indeholde og indbetale **udbytteskat** (som hovedregel 27 %, kildeskatteloven § 65) og indberette udbyttet. Er der ikke indeholdt udbytteskat, kan selskabet blive mødt med krav om betaling af den manglende skat.
{% else %}- Selskabet skal indeholde **A-skat og AM-bidrag** og indberette beløbet til eIndkomst.
{% endif %}- En senere tilbagebetaling ændrer ikke beskatningen. For lån ydet 1. januar 2026 eller senere anses tilbagebetalingen skattemæssigt som et rentefrit lån på anfordringsvilkår til selskabet, og selskabet skal føre en skattemæssig mellemregningskonto (ligningsloven § 16 E, stk. 2-4, jf. lov nr. 749 af 20. juni 2025). For lån ydet før 1. januar 2026 gælder disse regler først, når lånene er ophørt.
- Manglende indeholdelse af skat kan være en overtrædelse af skattelovgivningen. Som revisor skal vi efter erklæringsbekendtgørelsen vurdere, om forholdet skal omtales i vores erklæring på årsrapporten.
{% endif %}
## Regnskabet
Tilgodehavender hos medlemmer af ledelsen skal oplyses i noterne med summen pr. ledelseskategori, de væsentligste vilkår inkl. rentefod og de beløb, der er tilbagebetalt i året (ÅRL § 73).

## Vores anbefaling
1. Stop yderligere private hævninger/udlæg fra selskabets konti. Private udgifter bør betales fra private konti.
2. Beslut, om beløbet skal {% if felt.hovedaktionaer %}behandles som {{ felt.beskatning_som|lower }} (med indeholdelse af skat){% else %}tilbagebetales eller omlægges til et lån på skriftlige forretningsmæssige vilkår{% endif %}, og dokumentér beslutningen i et referat fra {{ kunde.ledelsesorgan }}{% if felt.beskatning_som == "Udbytte" %} og generalforsamlingen{% endif %}.
3. Hvis I ønsker et egentligt lån: udarbejd et skriftligt gældsbrev med markedsrente, afdragsprofil og evt. sikkerhed, og dokumentér ledelsens vurdering af forsvarligheden.
4. Kontakt os, før nye lån ydes – så sikrer vi den rigtige skattemæssige behandling.

Vi beder om jeres tilbagemelding senest **{{ felt.svar_frist }}**. Vi hjælper gerne med beregning af skatten, indberetning og nødvendige beslutningsdokumenter.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}
