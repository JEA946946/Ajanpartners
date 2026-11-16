---
{
  "title": "Opdragsbrev – personlig skat og selvangivelse",
  "description": "Aftale om udarbejdelse af selvangivelse (oplysningsskema) for personer med selvstændig virksomhed, interessentskaber og hovedaktionærer, herunder virksomhedsordningen og fuldmagt til TastSelv.",
  "kind": "brev",
  "references": ["Skattekontrolloven §§ 2-5 og 11", "Personskatteloven", "Virksomhedsskatteloven", "Ejendomsavancebeskatningsloven", "Aktieavancebeskatningsloven", "Skatteforvaltningsloven § 26", "Hvidvaskloven"],
  "legal_forms": ["enk", "is", "pmv", "holding", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "skatteyder", "label": "Skatteyder(e) – navn", "type": "text"},
    {"name": "aegtefaelle", "label": "Ægtefælle omfattet af aftalen (navn)", "type": "text"},
    {"name": "indkomstaar", "label": "Indkomstår", "type": "text", "default": "{{ regnskab.aar }}"},
    {"name": "beskatningsform", "label": "Beskatning af virksomhed", "type": "select", "options": ["virksomhedsordningen", "kapitalafkastordningen", "personskattelovens almindelige regler", "ingen selvstændig virksomhed (hovedaktionær/lønmodtager)", "vurderes af os"], "default": "vurderes af os"},
    {"name": "hovedaktionaer", "label": "Skatteyder er hovedaktionær", "type": "checkbox", "default": false},
    {"name": "udlejning", "label": "Udlejning af fast ejendom/ferielejlighed", "type": "checkbox", "default": false},
    {"name": "udland", "label": "Udenlandsk indkomst eller formue", "type": "checkbox", "default": false},
    {"name": "forskud", "label": "Tilpasning af forskudsopgørelse", "type": "checkbox", "default": true},
    {"name": "honorar", "label": "Honorar (kr. ekskl. moms)", "type": "number"},
    {"name": "timepris", "label": "Timepris for rådgivning (kr. ekskl. moms)", "type": "number"},
    {"name": "ansvarsbegraensning", "label": "Ansvarsbegrænsning", "type": "text", "default": "et beløb svarende til tre gange honoraret for den pågældende ydelse, dog højst 1.000.000 kr."}
  ]
}
---
**{{ felt.skatteyder }}**{% if felt.aegtefaelle %} og **{{ felt.aegtefaelle }}**{% endif %}
{% if kunde.er_personlig %}{{ kunde.navn }}
{% endif %}{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Opdragsbrev – personlig skat for indkomståret {{ felt.indkomstaar }}

Tak for jeres henvendelse. Med dette brev bekræfter vi vilkårene for vores bistand med jeres personlige skatteforhold. Brevet gælder også for de følgende indkomstår, indtil det ændres eller opsiges.

## 1. Ydelser

1. Udarbejdelse og indberetning af oplysningsskemaet (selvangivelsen) for {{ felt.skatteyder }}{% if felt.aegtefaelle %} og {{ felt.aegtefaelle }}{% endif %} på grundlag af årsopgørelsen, de forudfyldte oplysninger hos Skattestyrelsen og de oplysninger, I giver os.
{% if kunde.er_personlig %}2. Skattemæssig opgørelse af overskud af virksomheden {{ kunde.navn }} på grundlag af regnskabet, herunder afskrivninger, privat andel af bil, telefon, internet og bolig, samt beskatning efter {{ felt.beskatningsform }}.
{% endif %}{% if felt.beskatningsform == "virksomhedsordningen" %}3. Opgørelse efter virksomhedsskatteloven: indskudskonto, hævninger efter hæverækkefølgen, kapitalafkast, opsparet overskud og virksomhedsskat, konto for opsparet overskud samt kontrol af, at der ikke sker sammenblanding af privat og erhvervsmæssig økonomi.
{% endif %}{% if kunde.selskabsform_kode == "is" %}4. Fordeling af interessentskabets resultat mellem interessenterne efter interessentskabskontrakten.
{% endif %}{% if felt.hovedaktionaer %}5. Opgørelse af udbytte, aktieavance og lønindkomst fra hovedaktionærselskabet, herunder vurdering af personalegoder (fri bil, fri bolig, fri telefon), mellemregning og eventuelle lån fra selskabet (ligningslovens § 16 E).
{% endif %}{% if felt.udlejning %}6. Opgørelse af lejeindtægter efter den regnskabsmæssige eller skematiske metode og eventuel ejendomsavance ved salg.
{% endif %}{% if felt.udland %}7. Udenlandsk indkomst og formue, herunder lempelse efter dobbeltbeskatningsoverenskomst eller ligningslovens § 33.
{% endif %}{% if felt.forskud %}8. Tilpasning af forskudsopgørelsen for det kommende år.
{% endif %}

Fristen for oplysningsskemaet er **1. juli** året efter indkomståret for personer med selvstændig virksomhed og personer, der har indkomst, som ikke er forudfyldt. Overskrides fristen, kan Skattestyrelsen pålægge skattetillæg og foretage skønsmæssig ansættelse.

{% if branche.landbrug %}Landbrugsejendomme kræver særlig opgørelse af blandt andet stuehusets lejeværdi, besætninger og produktionstilskud.{% endif %}
{% if branche.ejendom %}Ved erhvervsmæssig udlejning af fast ejendom opgør vi også genvundne afskrivninger og ejendomsavance, og vi vurderer momsforhold ved frivillig registrering.{% endif %}
{% if branche.kontantintensiv %}I kontantintensive brancher lægger Skattestyrelsen vægt på privatforbrugsberegningen. Vi beregner privatforbruget og drøfter det med jer, så det er sandsynligt i forhold til husstandens forbrug.{% endif %}

## 2. Fuldmagt og jeres ansvar

For at kunne indberette skal vi have fuldmagt (rådgiverfuldmagt) til jeres skattemappe på TastSelv. Fuldmagten giver adgang til at se og ændre oplysninger og kan til enhver tid tilbagekaldes af jer.

I har selv ansvaret for, at selvangivelsen er rigtig og fuldstændig, jf. skattekontrolloven. I skal derfor give os alle relevante oplysninger rettidigt, herunder om indkomst fra udlandet, aktier og kryptoaktiver, salg af fast ejendom, gaver og arv, og I skal gennemgå årsopgørelsen, når den foreligger. Kontakt os, hvis I modtager breve fra Skattestyrelsen, da frister ofte er korte.

## 3. Vores rådgivning

Vores rådgivning bygger på gældende lovgivning og praksis og de forhold, I har oplyst. Vi kontrollerer ikke rigtigheden af oplysningerne. Vi opdaterer ikke tidligere rådgivning, medmindre det aftales. Klager, kontrolsager og bindende svar aftales særskilt.

## 4. Hvidvask og databeskyttelse

Vi er omfattet af hvidvaskloven og skal derfor se gyldig legitimation og indhente oplysninger om jeres økonomiske forhold. Vi behandler jeres personoplysninger, herunder CPR-nummer, for at levere ydelsen og opfylde vores lovpligtige forpligtelser. Læs mere i vores privatlivspolitik.

## 5. Honorar og ansvar

Honoraret udgør {{ felt.honorar }} kr. ekskl. moms. Øvrig rådgivning afregnes med {{ felt.timepris }} kr. pr. time ekskl. moms.

Vores ansvar er begrænset til {{ felt.ansvarsbegraensning }}. Vi hæfter ikke for skatter, som I under alle omstændigheder skulle have betalt, eller for tab som følge af ufuldstændige eller forkerte oplysninger. Begrænsningen gælder ikke ved forsæt eller grov uagtsomhed. Opgaven udføres i øvrigt efter vores almindelige forretningsbetingelser.

Vi beder jer bekræfte aftalen ved at underskrive og returnere en kopi.

Med venlig hilsen

{{ firma.navn }}

&nbsp;

______________________________
{{ medarbejder.navn }}
{{ medarbejder.titel }}

&nbsp;

**Accepteret**

Dato: ________________

______________________________ {% if felt.aegtefaelle %}______________________________{% endif %}
{{ felt.skatteyder }} {% if felt.aegtefaelle %}{{ felt.aegtefaelle }}{% endif %}
