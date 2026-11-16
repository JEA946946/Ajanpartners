---
{
  "title": "Opdragsbrev – opstilling af årsregnskab (ISRS 4410)",
  "description": "Opdragsbrev for opstilling af årsregnskab efter ISRS 4410 (revideret) uden sikkerhed. Dækker også risikobranchekravet i årsregnskabslovens § 135, stk. 5.",
  "kind": "brev",
  "references": ["ISRS 4410 (revideret)", "Erklæringsbekendtgørelsen", "Årsregnskabsloven § 135, stk. 5", "Bekendtgørelse nr. 1488 af 27/11/2025 om risikobrancher", "Revisorloven § 16", "Hvidvaskloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "revisor_titel", "label": "Underskrivende revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "registreret revisor"},
    {"name": "regnskabsgrundlag", "label": "Regnskabsgrundlag", "type": "select", "options": ["årsregnskabsloven (regnskabsklasse B)", "årsregnskabsloven (regnskabsklasse A)", "skattemæssige principper (skattemæssigt regnskab)", "særligt formål (beskrives i felt nedenfor)"], "default": "årsregnskabsloven (regnskabsklasse B)"},
    {"name": "saerligt_formaal", "label": "Formål og brugere hvis regnskab til særligt formål", "type": "textarea"},
    {"name": "bogfoering_hos_os", "label": "Vi fører også bogføringen", "type": "checkbox", "default": false},
    {"name": "materiale_dato", "label": "Seneste dato for materiale", "type": "date"},
    {"name": "honorar", "label": "Honorar (kr. ekskl. moms)", "type": "number"},
    {"name": "timepris", "label": "Timepris for ekstraarbejde (kr. ekskl. moms)", "type": "number"},
    {"name": "fakturering", "label": "Fakturering", "type": "select", "options": ["løbende", "ved afslutning", "aconto månedligt"], "default": "ved afslutning"},
    {"name": "ansvarsbegraensning", "label": "Ansvarsbegrænsning", "type": "text", "default": "et beløb svarende til honoraret for opgaven, dog højst 1.000.000 kr."}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Opdragsbrev – opstilling af årsregnskabet for {{ regnskab.aar }}

Tak fordi I har valgt {{ firma.navn }}. Med dette brev bekræfter vi vilkårene for vores bistand med opstilling af årsregnskabet. Brevet gælder også for de følgende regnskabsår, indtil det ændres eller opsiges.

## 1. Opgavens formål og omfang

Vi opstiller årsregnskabet for {{ kunde.navn }} for perioden {{ regnskab.start }} – {{ regnskab.slut }} på grundlag af bogføringen og de øvrige oplysninger, som I giver os. Årsregnskabet udarbejdes efter {{ felt.regnskabsgrundlag }}.
{% if felt.saerligt_formaal %}

Regnskabet udarbejdes til følgende særlige formål og brugere: {{ felt.saerligt_formaal }}. Regnskabet er ikke egnet til andre formål.{% endif %}

Opgaven udføres efter ISRS 4410 (revideret), Opgaver om opstilling af finansielle oplysninger, og de yderligere krav i dansk revisorlovgivning. Vi anvender vores faglige ekspertise inden for regnskabsaflæggelse til at bistå jer med at klassificere, sammenfatte og præsentere de finansielle oplysninger. Vi overholder de relevante etiske krav, herunder krav om integritet, objektivitet, professionel kompetence og fornøden omhu.

En opstilling er **ikke** en revision eller et review. Vi skal ikke verificere nøjagtigheden eller fuldstændigheden af de oplysninger, I giver os, og vi skal ikke indhente bevis for at kunne udtrykke en konklusion. Vi giver derfor ingen sikkerhed for, at årsregnskabet er udarbejdet i overensstemmelse med regnskabsgrundlaget. Opgaven kan ikke forventes at afdække fejl, besvigelser eller ulovligheder.

Hvis vi bliver opmærksomme på, at oplysningerne er ufuldstændige, unøjagtige eller på anden måde utilfredsstillende, beder vi jer om yderligere oplysninger eller rettelser. Hvis I ikke giver os disse, kan vi blive nødt til at trække os fra opgaven.

{% if felt.bogfoering_hos_os %}Vi fører også jeres bogføring efter særskilt aftale. Det ændrer ikke ved, at ledelsen har ansvaret for bogføringen, for de oplysninger, den bygger på, og for årsregnskabet.{% endif %}

{% if branche.restauration or branche.rengoering or branche.transport or branche.it or branche.personlig_service or branche.bilhandel %}
### Risikobranche – årsregnskabslovens § 135, stk. 5

Selskabets branche ({{ kunde.branchetekst }}, {{ kunde.branchekode }}) kan være klassificeret som risikobranche efter bekendtgørelse nr. 1488 af 27. november 2025 (gældende for regnskabsår, der begynder 1. januar 2025 eller senere). Er hovedbranchekoden på balancedagen omfattet, og har nettoomsætningen oversteget 5 mio. kr. i to på hinanden følgende regnskabsår, skal årsregnskabet ledsages af enten en erklæring om assistance med opstilling eller en erklæring med sikkerhed fra en uafhængig revisor. Denne opstillingserklæring opfylder kravet. Vi kontrollerer hvert år koden og omsætningen og giver jer besked, hvis kravet gælder.
{% endif %}

## 2. Ledelsens ansvar

Opgaven udføres på det grundlag, at {{ kunde.ledelsesorgan }} anerkender at have ansvaret for:

1. årsregnskabet og de oplysninger, det bygger på, herunder valg af regnskabsgrundlag og regnskabsmæssige skøn;
2. at bogføringen er fuldstændig og korrekt og opfylder bogføringslovens krav, herunder opbevaring af bilag i 5 år;
3. den interne kontrol, ledelsen finder nødvendig;
4. at give os fuldstændige og korrekte oplysninger rettidigt, herunder om lager, igangværende arbejder, tilgodehavender, gæld, eventualforpligtelser og begivenheder efter balancedagen;
5. at godkende det endelige årsregnskab, før det offentliggøres eller anvendes.

Ledelsen skal underskrive en ledelsespåtegning og afgive en skriftlig bekræftelse af de oplysninger, der er givet os.

## 3. Rapportering

Vi afgiver en erklæring om opstilling, som vedlægges årsregnskabet. Erklæringen beskriver, at vi har assisteret med opstillingen, og at vi ikke har udført revision eller review. Bruges årsregnskabet eller vores navn i forbindelse med regnskabet, skal erklæringen følge med.

## 4. Hvidvask

Vi er omfattet af hvidvaskloven og skal derfor indhente legitimation og oplysninger om ejere, reelle ejere og ledelse samt løbende overvåge kundeforholdet. Ved mistanke om hvidvask eller terrorfinansiering har vi pligt til at underrette Hvidvasksekretariatet.

## 5. Tidsplan, honorar og øvrige vilkår

Vi forventer at modtage materialet senest {{ felt.materiale_dato }}{% if kunde.er_kapitalselskab %}, så årsrapporten kan indsendes til Erhvervsstyrelsen senest {{ regnskab.frist_aarsrapport }}{% endif %}.

Honoraret udgør {{ felt.honorar }} kr. ekskl. moms. Ekstraarbejde afregnes med {{ felt.timepris }} kr. pr. time ekskl. moms efter forudgående orientering. Fakturering sker {{ felt.fakturering }}.

Vores ansvar er begrænset til {{ felt.ansvarsbegraensning }}. Begrænsningen gælder ikke ved forsæt eller grov uagtsomhed. Vi hæfter ikke for indirekte tab eller for tab, der skyldes fejl i de oplysninger, I har givet os. Vi behandler personoplysninger som selvstændig dataansvarlig. Klager kan indgives til Revisornævnet. Opgaven udføres i øvrigt efter vores almindelige forretningsbetingelser.

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
