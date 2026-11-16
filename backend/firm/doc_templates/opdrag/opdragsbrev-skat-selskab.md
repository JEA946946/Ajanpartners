---
{
  "title": "Opdragsbrev – selskabsskat og skatterådgivning (selskab)",
  "description": "Aftale om udarbejdelse af skattemæssig indkomstopgørelse og selvangivelse for kapitalselskaber, herunder sambeskatning, transfer pricing-oplysninger og løbende skatterådgivning.",
  "kind": "brev",
  "references": ["Selskabsskatteloven", "Skattekontrolloven (LBK nr. 12 af 08/01/2024) §§ 2, 12 og 37-39", "Skatteforvaltningsloven §§ 26-27", "Ligningsloven §§ 2, 3 og 16 E", "Aktieavancebeskatningsloven §§ 4 A og 4 B", "Selskabsskatteloven §§ 12, 12 D og 29 A", "Selskabsskatteloven § 31 (sambeskatning)", "Revisorloven § 24", "Hvidvaskloven"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "indkomstaar", "label": "Indkomstår", "type": "text", "default": "{{ regnskab.aar }}"},
    {"name": "selvangivelsesfrist", "label": "Frist for selvangivelse", "type": "text", "default": "6 måneder efter indkomstårets udløb (udløber indkomståret i perioden 1.-31. marts: senest 1. september samme år), jf. skattekontrollovens § 12"},
    {"name": "sambeskatning", "label": "Selskabet indgår i national sambeskatning", "type": "checkbox", "default": false},
    {"name": "administrationsselskab", "label": "Administrationsselskab i sambeskatningen", "type": "text"},
    {"name": "kontrollerede_transaktioner", "label": "Selskabet har kontrollerede transaktioner (koncern/hovedaktionær)", "type": "checkbox", "default": false},
    {"name": "aconto", "label": "Rådgivning om acontoskat og frivillige indbetalinger", "type": "checkbox", "default": true},
    {"name": "raadgivning", "label": "Særskilt aftalt rådgivning (fx omstrukturering, udbytte, generationsskifte)", "type": "textarea"},
    {"name": "honorar", "label": "Honorar for indkomstopgørelse og selvangivelse (kr. ekskl. moms)", "type": "number"},
    {"name": "timepris", "label": "Timepris for rådgivning (kr. ekskl. moms)", "type": "number"},
    {"name": "ansvarsbegraensning", "label": "Ansvarsbegrænsning – beløb/formulering (udfyldes af revisor)", "type": "text"}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

CVR-nr. {{ kunde.cvr }}

{{ dato.idag }}

# Opdragsbrev – selskabsskat for indkomståret {{ felt.indkomstaar }}

Med dette brev bekræfter vi vilkårene for vores bistand med selskabets skatteforhold. Brevet gælder også for de følgende indkomstår, indtil det ændres eller opsiges.

## 1. Ydelser

Vi udfører følgende:

1. Opgørelse af selskabets skattepligtige indkomst på grundlag af det godkendte årsregnskab og de oplysninger, ledelsen giver os, herunder skattemæssige afskrivninger, fradrag, underskudsfremførsel (selskabsskattelovens § 12) og renteloft/rentebegrænsning, hvor det er relevant.
2. Indberetning af selvangivelse/oplysningsskema for selskabet på TastSelv Erhverv. Fristen er {{ felt.selvangivelsesfrist }}.
3. Beregning af selskabsskat, udskudt skat til brug for årsregnskabet og afstemning af skattekontoen for selskabsskat.
{% if felt.aconto %}4. Rådgivning om acontoskat (ordinær acontoskat i 2 rater; frivillig acontoskat senest 20. marts, 20. november og 1. februar, selskabsskattelovens § 29 A) for at begrænse restskattetillæg.
{% endif %}{% if felt.sambeskatning %}5. Indkomstopgørelse som led i national sambeskatning (selskabsskattelovens § 31) med {{ felt.administrationsselskab }} som administrationsselskab, herunder fordeling af skat og underskud mellem de sambeskattede selskaber.
{% endif %}{% if felt.kontrollerede_transaktioner %}6. Udfyldelse af oplysninger om kontrollerede transaktioner (skattekontrollovens § 38, jf. definitionerne i § 37) i selvangivelsen. Udarbejdelse af transfer pricing-dokumentation (skattekontrollovens § 39) er ikke omfattet, medmindre det aftales særskilt. Selskabet er ansvarligt for, at transaktioner med nærtstående parter sker på armslængdevilkår (ligningslovens § 2).
{% endif %}

{% if branche.holding %}**Holdingselskab:** Vi vurderer den skattemæssige behandling af udbytter og avancer på datterselskabsaktier og koncernselskabsaktier (aktieavancebeskatningslovens §§ 4 A og 4 B), skattefrie/skattepligtige porteføljeaktier og eventuelle lån til hovedaktionærer (ligningslovens § 16 E).
{% endif %}{% if branche.investeringsejendomme %}**Ejendomme:** Vi opgør skattemæssige afskrivninger på bygninger og installationer, genvundne afskrivninger og ejendomsavance ved salg samt ejendomsværdiskatte- og grundskyldsforhold, hvor det er relevant.
{% endif %}{% if branche.byggeri or branche.igangvaerende_arbejder %}**Igangværende arbejder:** Den skattemæssige behandling af igangværende arbejder følger som udgangspunkt den regnskabsmæssige. Vi kontrollerer, at der ikke er forskel, som skal korrigeres.
{% endif %}{% if branche.landbrug %}**Landbrug:** Særlige regler om afskrivninger, besætninger og eventuelle tilskud (fx landdistrikts- og arealstøtte) indgår i opgørelsen.
{% endif %}
{% if felt.raadgivning %}**Særskilt rådgivning:** {{ felt.raadgivning }}
{% endif %}

Skatterådgivning ud over ovenstående, dialog med Skattestyrelsen om kontrolsager, klager til Skatteankestyrelsen og bindende svar aftales og afregnes særskilt.

## 2. Ledelsens ansvar

{{ kunde.ledelsesorgan }} har ansvaret for, at selskabets selvangivelse er rigtig og fuldstændig, og for at give os alle relevante oplysninger rettidigt, herunder om transaktioner med kapitalejere, ledelse og koncernselskaber, udenlandske forhold, personalegoder, tilskud og ændringer i ejerforhold (ejerskifte kan begrænse fremførsel af underskud, jf. selskabsskattelovens § 12 D). Ledelsen skal gennemgå og godkende selvangivelsen, før vi indberetter den.

Vi bygger vores arbejde på de oplysninger, vi modtager, og vi kontrollerer ikke rigtigheden ud over det, der følger af en eventuel revision eller anden erklæringsopgave.

## 3. Vores rådgivning

Vores rådgivning bygger på gældende lovgivning, praksis og de faktiske forhold, I har oplyst ved rådgivningstidspunktet. Ændres lovgivning eller praksis, eller er de oplyste forhold ufuldstændige, kan rådgivningen ikke lægges til grund. Vi opdaterer ikke tidligere rådgivning, medmindre det aftales. Hvor der er tvivl om den skattemæssige behandling, oplyser vi om tvivlen og om muligheden for bindende svar.

Hvis vi også er selskabets revisor, vurderer vi, at skattebistanden kan leveres uden at true vores uafhængighed, fordi ledelsen træffer alle beslutninger, og fordi skatteberegningerne ikke er af væsentlig betydning for regnskabet eller bygger på skøn, som vi selv ville skulle revidere, jf. revisorlovens § 24.

## 4. Hvidvask og skattemæssige pligter

Vi er omfattet af hvidvaskloven og gennemfører kundekendskabsprocedurer. Vi medvirker ikke til skatteunddragelse eller arrangementer, hvis hovedformål er at opnå en skattefordel i strid med lovens formål (ligningslovens § 3). Hvis vi bliver opmærksomme på fejl i tidligere selvangivelser, orienterer vi ledelsen og anbefaler, at fejlen rettes over for Skattestyrelsen.

## 5. Honorar og ansvar

Honoraret for indkomstopgørelse og selvangivelse udgør {{ felt.honorar }} kr. ekskl. moms. Øvrig rådgivning afregnes efter medgået tid med {{ felt.timepris }} kr. pr. time ekskl. moms.

Vores ansvar er begrænset til {{ felt.ansvarsbegraensning }}. Vi hæfter ikke for skatter, renter og tillæg, som selskabet under alle omstændigheder skulle have betalt, eller for tab, der skyldes ufuldstændige eller urigtige oplysninger fra selskabet. Begrænsningen gælder ikke ved forsæt eller grov uagtsomhed. Opgaven udføres i øvrigt efter vores almindelige forretningsbetingelser.

Vi beder jer bekræfte opdragsbrevet ved at underskrive og returnere en kopi.

Med venlig hilsen

{{ firma.navn }}

&nbsp;

______________________________
{{ medarbejder.navn }}
{{ medarbejder.titel }}

&nbsp;

**Accepteret på vegne af {{ kunde.navn }}**

Dato: ________________

______________________________
{{ kunde.ledelsesorgan }}
