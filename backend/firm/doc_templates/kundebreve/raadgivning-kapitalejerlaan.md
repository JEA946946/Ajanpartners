---
{
  "title": "Rådgivningsbrev om lån til kapitalejer/ledelse (kapitalejerlån)",
  "description": "Brev til kapitalselskab om lån/debetsaldo til kapitalejer eller ledelse: selskabsretlige regler efter ophævelsen af SL §§ 210-212 pr. 1. januar 2025, beskatning efter ligningsloven § 16 E, konsekvenser og anbefalede handlinger.",
  "kind": "brev",
  "references": ["Ligningsloven § 16 E", "Selskabsloven §§ 115, 127, 206", "Lov nr. 1668 af 30. december 2024 (ophævelse af SL §§ 210-212)", "Kildeskatteloven §§ 46, 65", "Årsregnskabsloven § 72", "Erklæringsbekendtgørelsen (omtale af ledelsesansvar)"],
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
- lånet er **forsvarligt** under hensyn til selskabets økonomiske stilling og kapitalberedskab (SL § 115),
- lånet er i **selskabets interesse** og ydes på **forretningsmæssige vilkår** (markedsrente, sikkerhed, tilbagebetalingsplan), og
- lånet ikke åbenbart giver låntager en **utilbørlig fordel** på andre kapitalejeres eller selskabets bekostning (SL § 127).

Selvfinansieringsreglerne (SL § 206) gælder fortsat: selskabet må ikke låne penge ud til køb af kapitalandele i selskabet selv, medmindre betingelserne herfor er opfyldt.
{% if felt.foer_2025 %}
Lånet er helt eller delvist ydet før 1. januar 2025. Ophævelsen har ikke gjort tidligere ulovlige kapitalejerlån lovlige med tilbagevirkende kraft. Vi anbefaler derfor, at den del af lånet, der er ydet før 2025, tilbagebetales, eller at forholdet afklares med os, før årsrapporten underskrives.
{% endif %}
{% if felt.hovedaktionaer %}## Skat – det vigtigste punkt
Lån fra et selskab til en **personlig kapitalejer med bestemmende indflydelse** (eller dennes nærtstående) beskattes efter **ligningsloven § 16 E** som om, beløbet var udbetalt som **{{ felt.beskatning_som|lower }}**. Det gælder, uanset om lånet er selskabsretligt lovligt, og uanset om det senere tilbagebetales. Undtaget er bl.a. lån, der er led i en sædvanlig forretningsmæssig disposition.

Konsekvenser:
- Beløbet beskattes hos {{ felt.laantager }} som {{ felt.beskatning_som|lower }} i det år, lånet blev ydet.
{% if felt.beskatning_som == "Udbytte" %}- Selskabet skal indeholde og indbetale **udbytteskat** (som udgangspunkt 27 %) og indberette udbyttet. Er det ikke sket rettidigt, hæfter selskabet for skatten.
{% else %}- Selskabet skal indeholde **A-skat og AM-bidrag** og indberette beløbet til eIndkomst. Beløbet er fradragsberettiget for selskabet som løn.
{% endif %}- En senere tilbagebetaling ændrer ikke beskatningen; tilbagebetalingen anses skattemæssigt som et indskud i selskabet.
- Manglende indeholdelse af skat er en overtrædelse af skattelovgivningen. Som revisor skal vi efter erklæringsbekendtgørelsen omtale væsentlige overtrædelser, der kan medføre ansvar for ledelsen, i vores erklæring på årsrapporten.
{% endif %}
## Regnskabet
Tilgodehavender hos kapitalejere og ledelse skal vises som en særskilt post i balancen, og lån til medlemmer af ledelsen skal oplyses i noterne med beløb, rente og væsentlige vilkår (ÅRL § 72).

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
