---
{
  "title": "Opdragsbrev – udvidet gennemgang (klasse B)",
  "description": "Opdragsbrev for udvidet gennemgang af årsregnskab efter Erhvervsstyrelsens erklæringsstandard for små virksomheder (årsregnskabslovens § 135, stk. 1, 2. pkt.). Kun regnskabsklasse B.",
  "kind": "brev",
  "references": ["Erklæringsstandard for udvidet gennemgang (Erhvervsstyrelsen)", "Årsregnskabsloven § 135, stk. 1, 2. pkt., og stk. 4", "Revisorloven § 18, stk. 1, 2. pkt.", "Revisorloven §§ 16, 22 og 24", "ISRE 2400 (principper)", "Hvidvaskloven"],
  "legal_forms": ["aps", "as", "ivs", "holding", "pmv", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "revisor_titel", "label": "Underskrivende revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "registreret revisor"},
    {"name": "valgt_dato", "label": "Dato for valg som revisor (generalforsamling)", "type": "text"},
    {"name": "materiale_dato", "label": "Seneste dato for aflevering af regnskabsmateriale", "type": "date"},
    {"name": "honorar", "label": "Honorar (kr. ekskl. moms)", "type": "number"},
    {"name": "honorar_type", "label": "Honorarform", "type": "select", "options": ["fast honorar", "overslag", "medgået tid"], "default": "overslag"},
    {"name": "timepris", "label": "Timepris for ekstraarbejde (kr. ekskl. moms)", "type": "number"},
    {"name": "fakturering", "label": "Fakturering", "type": "select", "options": ["løbende", "ved afslutning", "aconto månedligt", "aconto kvartalsvis"], "default": "ved afslutning"},
    {"name": "ansvarsbegraensning", "label": "Ansvarsbegrænsning", "type": "text", "default": "et beløb svarende til tre gange det honorar, der er faktureret for opgaven, dog højst 3.000.000 kr."},
    {"name": "opstilling_ogsaa", "label": "Vi opstiller også årsregnskabet", "type": "checkbox", "default": true}
  ]
}
---
**{{ kunde.navn }}**
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

CVR-nr. {{ kunde.cvr }}

{{ dato.idag }}

# Opdragsbrev – udvidet gennemgang af årsregnskabet for {{ regnskab.aar }}

{% if felt.valgt_dato %}På generalforsamlingen den {{ felt.valgt_dato }} blev {{ firma.navn }} valgt som revisor med henblik på udvidet gennemgang af årsregnskabet.{% else %}{{ firma.navn }} er valgt som revisor med henblik på udvidet gennemgang af årsregnskabet.{% endif %} Dette brev bekræfter vilkårene for opgaven og gælder også for de efterfølgende regnskabsår, indtil det ændres eller opsiges.

## 1. Baggrund – hvorfor udvidet gennemgang

Virksomheder i regnskabsklasse B, som er revisionspligtige, kan i stedet for revision vælge at lade årsregnskabet gennemgå efter Erhvervsstyrelsens erklæringsstandard for udvidet gennemgang, jf. årsregnskabslovens § 135, stk. 1, 2. pkt. Muligheden gælder ikke, hvis virksomheden i to på hinanden følgende regnskabsår sammen med de virksomheder, den har kapitalinteresser i og betydelig indflydelse over, overskrider to af størrelsesgrænserne for regnskabsklasse B i årsregnskabslovens § 7, stk. 2, nr. 1 (§ 135, stk. 4), eller hvis virksomheden overgår til regnskabsklasse C. Vi vurderer hvert år, om betingelserne fortsat er opfyldt, og giver jer besked, hvis selskabet bliver omfattet af krav om revision.

## 2. Opgavens formål og omfang

Vi udfører en udvidet gennemgang af årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }}. Formålet er at opnå begrænset sikkerhed for, at årsregnskabet giver et retvisende billede i overensstemmelse med årsregnskabsloven, og at afgive en erklæring med en konklusion i positiv form ("Baseret på det udførte arbejde er det vores opfattelse, at årsregnskabet giver et retvisende billede …"), jf. Erhvervsstyrelsens erklæringsstandard for udvidet gennemgang.

En udvidet gennemgang består af:

- **Gennemgang:** forespørgsler til ledelsen og, hvor det er hensigtsmæssigt, andre i virksomheden, samt analytiske handlinger og vurdering af det opnåede bevis.
- **Supplerende handlinger:** de supplerende handlinger, som erklæringsstandarden foreskriver, og yderligere handlinger, hvis vi bliver opmærksomme på forhold, der giver os grund til at tro, at årsregnskabet kan indeholde væsentlig fejlinformation.

Arbejdet er væsentligt mindre omfattende end en revision efter ISA. Vi udtrykker derfor ikke en revisionskonklusion, og der er en større risiko for, at væsentlig fejlinformation ikke opdages. Gennemgangen er ikke tilrettelagt med henblik på at afdække besvigelser eller andre uregelmæssigheder, men vi vil oplyse jer om væsentlige forhold, som vi bliver opmærksomme på.

Vi læser ledelsesberetningen og afgiver en udtalelse om, hvorvidt den er i overensstemmelse med årsregnskabet og årsregnskabslovens krav.

### Områder med særlig opmærksomhed

{% if branche.lager %}- **Varelager:** Dokumentation for optælling, kostpris og nedskrivning af ukurante varer. Vi kan efter en vurdering beslutte at overvære lageroptællingen.
{% endif %}{% if branche.igangvaerende_arbejder %}- **Igangværende arbejder:** Opgørelse pr. projekt, færdiggørelsesgrad og forventede tab.
{% endif %}{% if branche.kontantintensiv %}- **Omsætning og kasse:** Kasseafstemninger, z-rapporter, sammenhæng mellem vareforbrug og omsætning (bruttoavance).
{% endif %}{% if branche.investeringsejendomme %}- **Investeringsejendomme:** Grundlaget for målingen og afkastforudsætninger.
{% endif %}{% if branche.holding %}- **Kapitalandele:** Måling, nedskrivningsbehov, koncerninterne mellemværender og eventuelle lån til kapitalejere og ledelse (forsvarlighed, SL §§ 115 og 127; beskatning efter LL § 16 E).
{% endif %}{% if branche.momsfritaget %}- **Moms og lønsumsafgift:** Delvis fradragsret og opgørelse af lønsumsafgift.
{% endif %}- Bankafstemninger, tilgodehavender, gæld til offentlige myndigheder, periodeafgrænsninger og fortsat drift.

{% if felt.opstilling_ogsaa %}### Opstilling af årsregnskabet

Efter jeres ønske bistår vi også med opstilling af årsregnskabet. Bistanden ændrer ikke ved, at {{ kunde.ledelsesorgan }} har ansvaret for årsregnskabet, og at alle væsentlige beslutninger, herunder regnskabsmæssige skøn, træffes af ledelsen. Vi har vurderet, at vi kan yde bistanden uden at true vores uafhængighed, fordi ledelsen godkender alle posteringer og skøn, og fordi opgaven tilrettelægges, så den medarbejder, der opstiller regnskabet, ikke alene står for den udvidede gennemgang.{% endif %}

## 3. Ledelsens ansvar

Opgaven udføres på det grundlag, at {{ kunde.ledelsesorgan }} anerkender at have ansvaret for:

1. at udarbejde et årsregnskab, der giver et retvisende billede i overensstemmelse med årsregnskabsloven, og en ledelsesberetning, der opfylder lovens krav;
2. den interne kontrol, ledelsen anser for nødvendig for at udarbejde et årsregnskab uden væsentlig fejlinformation;
3. bogføring og opbevaring af regnskabsmateriale efter bogføringsloven, herunder brug af et digitalt bogføringssystem, når loven kræver det;
4. at give os adgang til alle relevante oplysninger og personer samt de yderligere oplysninger, vi anmoder om;
5. at afgive en skriftlig ledelseserklæring ved opgavens afslutning.

## 4. Rapportering

Vi afgiver en erklæring om udvidet gennemgang, som indgår i årsrapporten. Erklæringens indhold kan blive modificeret, hvis vi under arbejdet finder forhold, der giver anledning hertil. Væsentlige forhold meddeler vi skriftligt til {{ kunde.ledelsesorgan }}.

Vi er underlagt revisorlovens § 22 om underretning ved ledelsens økonomiske kriminalitet og hvidvasklovens krav om kundekendskab, overvågning og underretning til Hvidvasksekretariatet. Vi beder derfor om legitimation og oplysninger om ejere, reelle ejere og ledelse.

## 5. Revisors hverv

Ved udvidet gennemgang ophører vores hverv, når erklæringen på årsregnskabet er afgivet, jf. revisorlovens § 18, stk. 1, 2. pkt. Selskabet skal derfor vælge revisor på hver ordinær generalforsamling og anmelde valget til Erhvervsstyrelsen. Vi kan fratræde hvervet, hvis fratræden ikke strider mod god revisorskik (§ 18, stk. 2).

## 6. Tidsplan, honorar og øvrige vilkår

Vi forventer at modtage regnskabsmaterialet senest {{ felt.materiale_dato }}. Årsrapporten skal være modtaget i Erhvervsstyrelsen senest {{ regnskab.frist_aarsrapport }}.

Honoraret udgør {{ felt.honorar }} kr. ekskl. moms ({{ felt.honorar_type }}). Ekstraarbejde som følge af mangelfuldt materiale eller ændrede forhold afregnes med {{ felt.timepris }} kr. pr. time ekskl. moms efter forudgående orientering. Fakturering sker {{ felt.fakturering }}.

Vores ansvar er begrænset til {{ felt.ansvarsbegraensning }}. Begrænsningen gælder ikke ved forsæt eller grov uagtsomhed. Vi hæfter ikke for indirekte tab. Vores arbejdspapirer kan indgå i Erhvervsstyrelsens kvalitetskontrol. Vi behandler personoplysninger som selvstændig dataansvarlig. Klager kan indgives til Revisornævnet. Opgaven udføres i øvrigt efter vores almindelige forretningsbetingelser.

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
