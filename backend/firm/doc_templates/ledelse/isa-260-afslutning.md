---
{
  "title": "Kommunikation med den øverste ledelse – afslutning (ISA 260)",
  "description": "Afsluttende rapportering til den øverste ledelse om betydelige revisionsmæssige observationer: kvalitative aspekter af regnskabspraksis og skøn, vanskeligheder, ikke-korrigerede fejl, ledelseserklæring, påtegningens udformning og uafhængighed. Til selskaber med bestyrelse bruges normalt revisionsprotokollatet.",
  "kind": "brev",
  "references": ["ISA 260, afsnit 16-17 og Bilag 2", "ISA 450, afsnit 12-13", "ISA 580", "ISA 705/706", "Revisorloven § 24"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "har_bestyrelse", "label": "Selskabet har en bestyrelse (ApS)", "type": "checkbox", "default": false},
    {"name": "paategning", "label": "Påtegningens udformning", "type": "select", "options": ["uden modifikation", "uden modifikation, men med fremhævelse af forhold", "uden modifikation, men med supplerende oplysninger", "med forbehold", "med afkræftende konklusion", "med manglende konklusion"], "default": "uden modifikation"},
    {"name": "paategning_forklaring", "label": "Forklaring til påtegningen", "type": "textarea"},
    {"name": "regnskabspraksis", "label": "Bemærkninger om regnskabspraksis og skøn", "type": "textarea", "default": "Den anvendte regnskabspraksis er passende og uændret i forhold til sidste år. De væsentlige regnskabsmæssige skøn er efter vores vurdering rimelige og tilstrækkeligt oplyst."},
    {"name": "vanskeligheder", "label": "Betydelige vanskeligheder under revisionen (tom = ingen)", "type": "textarea"},
    {"name": "ukorrigerede_fejl", "label": "Ikke-korrigerede fejl (tom = ingen)", "type": "textarea"},
    {"name": "oevrige", "label": "Øvrige betydelige forhold (fx nærtstående parter, lovovertrædelser)", "type": "textarea"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"}
  ]
}
---
**{{ kunde.navn }}**
Att.: {% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %}bestyrelsen{% else %}{{ kunde.ledelsesorgan }}{% endif %}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Betydelige observationer fra revisionen for {{ regnskab.aar }}

Vi har afsluttet vores revision af årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} og rapporterer hermed vores betydelige observationer, jf. ISA 260.

## Påtegningen

Vi forventer at afgive en revisionspåtegning {{ felt.paategning }}.{% if felt.paategning_forklaring %} {{ felt.paategning_forklaring }}{% endif %}

## Kvalitative aspekter af regnskabspraksis og skøn

{{ felt.regnskabspraksis }}

{% if branche.lager %}- Varelageret er målt efter FIFO/vejede gennemsnitspriser med nedskrivning for ukurans. Vi har vurderet nedskrivningen som rimelig.
{% endif %}{% if branche.igangvaerende_arbejder %}- Igangværende arbejder er indregnet efter produktionsmetoden. Skønnet over færdiggørelsesgrad og restomkostninger er behæftet med usikkerhed, men er efter vores vurdering rimeligt.
{% endif %}{% if branche.investeringsejendomme %}- Investeringsejendomme er målt til dagsværdi. Dagsværdien er følsom over for afkastkravet, og vi anbefaler, at følsomheden oplyses i noterne.
{% endif %}{% if branche.landbrug %}- Biologiske aktiver er målt efter den oplyste regnskabspraksis, og forudsætningerne er efter vores vurdering rimelige.
{% endif %}
## Betydelige vanskeligheder

{% if felt.vanskeligheder %}{{ felt.vanskeligheder }}{% else %}Vi har ikke mødt betydelige vanskeligheder under revisionen og har modtaget de oplysninger, vi har bedt om.{% endif %}

## Fejl og korrektioner

{% if felt.ukorrigerede_fejl %}Følgende fejl er ikke korrigeret: {{ felt.ukorrigerede_fejl }} Ledelsen har i ledelseserklæringen bekræftet, at virkningen er uvæsentlig. Vi anbefaler, at fejlene korrigeres, da de ellers kan påvirke næste års regnskab.{% else %}Alle de korrektioner, vi har foreslået, er indarbejdet. Der er ingen ikke-korrigerede fejl ud over åbenlyst ubetydelige forhold.{% endif %}

{% if felt.oevrige %}## Øvrige forhold

{{ felt.oevrige }}

{% endif %}## Skriftlige erklæringer

Vi har anmodet ledelsen om en skriftlig ledelseserklæring, som underskrives samtidig med årsrapporten.

## Uafhængighed

Vi bekræfter, at vi i hele perioden har været uafhængige af selskabet i overensstemmelse med revisorlovens § 24 og IESBA Code.

Med venlig hilsen

**{{ firma.navn }}**

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
