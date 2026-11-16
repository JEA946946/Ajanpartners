---
{
  "title": "Opdragsbrev – review af årsregnskab (ISRE 2400)",
  "description": "Opdragsbrev for review med begrænset sikkerhed efter ISRE 2400 (revideret), typisk for virksomheder der har fravalgt revision, men ønsker en erklæring med sikkerhed (fx til bank).",
  "kind": "brev",
  "references": ["ISRE 2400 (revideret)", "Erklæringsbekendtgørelsen", "Revisorloven §§ 16 og 24", "Årsregnskabsloven § 135, stk. 1 og 5", "Hvidvaskloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "revisor_titel", "label": "Underskrivende revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "registreret revisor"},
    {"name": "formaal", "label": "Erklæringens formål/brugere (fx bank, leverandører)", "type": "text", "default": "årsrapporten og selskabets pengeinstitut"},
    {"name": "regnskabsgrundlag", "label": "Regnskabsgrundlag", "type": "select", "options": ["årsregnskabsloven (regnskabsklasse B)", "årsregnskabsloven (regnskabsklasse A) og virksomhedens anvendte regnskabspraksis", "skattemæssige principper (skattemæssigt regnskab)"], "default": "årsregnskabsloven (regnskabsklasse B)"},
    {"name": "materiale_dato", "label": "Seneste dato for materiale", "type": "date"},
    {"name": "honorar", "label": "Honorar (kr. ekskl. moms)", "type": "number"},
    {"name": "timepris", "label": "Timepris for ekstraarbejde (kr. ekskl. moms)", "type": "number"},
    {"name": "fakturering", "label": "Fakturering", "type": "select", "options": ["løbende", "ved afslutning"], "default": "ved afslutning"},
    {"name": "ansvarsbegraensning", "label": "Ansvarsbegrænsning", "type": "text", "default": "et beløb svarende til tre gange honoraret for opgaven, dog højst 3.000.000 kr."}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Opdragsbrev – review af årsregnskabet for {{ regnskab.aar }}

I forlængelse af vores drøftelser bekræfter vi hermed vilkårene for vores review af årsregnskabet for {{ kunde.navn }}. Brevet gælder også for de efterfølgende regnskabsår, indtil det ændres eller opsiges.

## 1. Opgavens formål og omfang

Vi udfører et review af årsregnskabet for perioden {{ regnskab.start }} – {{ regnskab.slut }}, der udarbejdes efter {{ felt.regnskabsgrundlag }}. Erklæringen er bestemt til {{ felt.formaal }}.

{% if kunde.er_kapitalselskab %}Selskabet har fravalgt revision efter årsregnskabslovens § 135, stk. 1, 3. pkt. Et review er en frivillig erklæring med begrænset sikkerhed og træder ikke i stedet for en revision, hvis selskabet senere bliver revisionspligtigt.{% endif %}

Vi udfører reviewet i overensstemmelse med den internationale standard om review af historiske regnskaber ISRE 2400 (revideret) og yderligere krav ifølge dansk revisorlovgivning. ISRE 2400 kræver, at vi konkluderer, om noget er kommet til vores kendskab, der giver os grund til at mene, at årsregnskabet ikke i alle væsentlige henseender er udarbejdet i overensstemmelse med den relevante regnskabsmæssige begrebsramme. Standarden kræver også, at vi overholder etiske krav, herunder uafhængighed.

Et review er en opgave med begrænset sikkerhed. Vi udfører primært forespørgsler til ledelsen og andre i virksomheden samt analytiske handlinger og vurderer det opnåede bevis. Handlingerne er væsentligt mindre omfattende end ved en revision efter ISA. Vi udtrykker derfor ikke en revisionskonklusion. Et review er ikke tilrettelagt med henblik på at afdække besvigelser, fejl eller ulovligheder, men vi orienterer jer om væsentlige forhold, vi bliver opmærksomme på.

{% if branche.kontantintensiv %}Da virksomheden har en væsentlig kontantomsætning, vil vores forespørgsler og analyser have særligt fokus på omsætningens fuldstændighed, kasseafstemninger og bruttoavance. Hvis vi ikke kan opnå tilstrækkeligt bevis gennem forespørgsler og analyser, udfører vi yderligere handlinger efter ISRE 2400.{% endif %}
{% if branche.lager %}Varelageret er en væsentlig post. Vi forventer at modtage lageropgørelse med kostpriser og ledelsens vurdering af ukurante varer.{% endif %}
{% if branche.restauration or branche.rengoering or branche.transport or branche.it or branche.personlig_service or branche.bilhandel %}

**Risikobrancher:** Virksomheder i regnskabsklasse B med hovedbranchekode i en klassificeret risikobranche og en nettoomsætning over 5 mio. kr. i to på hinanden følgende år skal ledsage årsregnskabet af en erklæring med sikkerhed eller en erklæring om opstilling, jf. årsregnskabslovens § 135, stk. 5, og bekendtgørelse nr. 1488 af 27. november 2025. Et review opfylder kravet. Selskabets branchekode {{ kunde.branchekode }} skal kontrolleres mod bekendtgørelsens liste.{% endif %}

## 2. Ledelsens ansvar

Opgaven udføres på det grundlag, at {{ kunde.ledelsesorgan }} anerkender og forstår at have ansvaret for:

1. at udarbejde et årsregnskab i overensstemmelse med {{ felt.regnskabsgrundlag }};
2. den interne kontrol, ledelsen anser for nødvendig for at udarbejde et årsregnskab uden væsentlig fejlinformation;
3. bogføring og opbevaring af regnskabsmateriale efter bogføringsloven;
4. at give os adgang til alle oplysninger, som ledelsen er bekendt med og som er relevante for årsregnskabet, de yderligere oplysninger, vi anmoder om, og ubegrænset adgang til personer i virksomheden;
5. at afgive en skriftlig ledelseserklæring ved opgavens afslutning.

## 3. Rapportering

Vi afgiver en erklæring om review med en konklusion i negativ form. Hvis vi finder forhold, der giver anledning hertil, kan konklusionen blive modificeret, eller erklæringen kan indeholde supplerende oplysninger. Erklæringen må alene anvendes i sin helhed sammen med årsregnskabet.

## 4. Hvidvask og øvrige pligter

Vi er omfattet af hvidvaskloven og skal derfor indhente legitimation og oplysninger om ejere, reelle ejere og ledelse samt løbende overvåge kundeforholdet. Ved mistanke om hvidvask eller terrorfinansiering har vi pligt til at underrette Hvidvasksekretariatet. Vores arbejdspapirer kan indgå i Erhvervsstyrelsens kvalitetskontrol.

## 5. Tidsplan, honorar og øvrige vilkår

Vi forventer at modtage regnskabsmaterialet senest {{ felt.materiale_dato }}{% if kunde.er_kapitalselskab %}, så årsrapporten kan indsendes til Erhvervsstyrelsen senest {{ regnskab.frist_aarsrapport }}{% endif %}.

Honoraret udgør {{ felt.honorar }} kr. ekskl. moms. Ekstraarbejde afregnes med {{ felt.timepris }} kr. pr. time ekskl. moms efter forudgående orientering. Fakturering sker {{ felt.fakturering }}.

Vores ansvar er begrænset til {{ felt.ansvarsbegraensning }}. Begrænsningen gælder ikke ved forsæt eller grov uagtsomhed. Vi hæfter ikke for indirekte tab og ikke over for tredjemand, som erklæringen ikke er bestemt for. Vi behandler personoplysninger som selvstændig dataansvarlig. Klager kan indgives til Revisornævnet. Opgaven udføres i øvrigt efter vores almindelige forretningsbetingelser.

Vi beder jer bekræfte opdragsbrevet ved at underskrive og returnere en kopi.

Med venlig hilsen

{{ firma.navn }}

&nbsp;

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}

&nbsp;

**Accepteret på vegne af {{ kunde.navn }}**

Dato: ________________

______________________________
{{ kunde.ledelsesorgan }}
