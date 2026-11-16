---
{
  "title": "Erklæring om opgørelse af omsætning (ISA 805 / ISAE 3000)",
  "description": "Revisors erklæring med høj eller begrænset grad af sikkerhed om en særskilt opgørelse af omsætning, fx til udlejer ved omsætningsbaseret leje, franchisegiver, licensgiver eller långiver. Indeholder afsnit om regnskabsgrundlag og begrænsning i distribution. Ved kontantintensive virksomheder fremhæves ledelsens ansvar for fuldstændig registrering af kontantsalg.",
  "kind": "erklaering",
  "references": ["ISA 805 (DK) – revision af særskilte regnskabsopgørelser", "ISA 800 (DK) – regnskaber med særligt formål", "ISAE 3000 (Revideret)", "ISRE 2400 (ved begrænset sikkerhed)", "Erklæringsbekendtgørelsen §§ 1-5"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "modtager", "label": "Modtager (fx udlejer, franchisegiver, bank)", "type": "text"},
    {"name": "periode", "label": "Periode", "type": "text", "default": "{{ regnskab.start }} – {{ regnskab.slut }}"},
    {"name": "kriterier", "label": "Kriterier/grundlag for opgørelsen", "type": "text", "default": "lejekontraktens bestemmelser om opgørelse af omsætning"},
    {"name": "lokation", "label": "Afgrænsning (fx butik/lejemål, adresse)", "type": "text"},
    {"name": "beloeb", "label": "Opgjort omsætning (kr. ekskl. moms)", "type": "number"},
    {"name": "sikkerhed", "label": "Sikkerhedsgrad", "type": "select", "options": ["Høj grad af sikkerhed (revision)", "Begrænset grad af sikkerhed (review)"], "default": "Høj grad af sikkerhed (revision)"},
    {"name": "standard", "label": "Standard", "type": "select", "options": ["ISA 805", "ISAE 3000"], "default": "ISA 805"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Den uafhængige revisors erklæring om opgørelse af omsætning

Til {{ felt.modtager }} og ledelsen i {{ kunde.navn }}

## Konklusion

Vi har {% if felt.sikkerhed == "Høj grad af sikkerhed (revision)" %}revideret{% else %}udført review af{% endif %} den medfølgende opgørelse af omsætning for {{ kunde.navn }}{% if felt.lokation %} vedrørende {{ felt.lokation }}{% endif %} for perioden {{ felt.periode }}, som udviser en omsætning på {{ felt.beloeb }} kr. ekskl. moms (herefter „opgørelsen“). Opgørelsen er udarbejdet på grundlag af {{ felt.kriterier }}.

{% if felt.sikkerhed == "Høj grad af sikkerhed (revision)" %}Det er vores opfattelse, at opgørelsen i alle væsentlige henseender er udarbejdet i overensstemmelse med {{ felt.kriterier }}.{% else %}Ved vores review er vi ikke blevet opmærksomme på forhold, der giver os grund til at mene, at opgørelsen ikke i alle væsentlige henseender er udarbejdet i overensstemmelse med {{ felt.kriterier }}.{% endif %}

## Grundlag for konklusion

{% if felt.standard == "ISA 805" %}Vi har udført vores {% if felt.sikkerhed == "Høj grad af sikkerhed (revision)" %}revision i overensstemmelse med internationale standarder om revision, herunder ISA 805 om revision af særskilte regnskabsopgørelser{% else %}review i overensstemmelse med ISRE 2400 (Revideret){% endif %}, og de yderligere krav, der er gældende i Danmark.{% else %}Vi har udført vores arbejde i overensstemmelse med ISAE 3000 (Revideret), Andre erklæringsopgaver med sikkerhed end revision eller review af historiske finansielle oplysninger, og de yderligere krav, der er gældende i Danmark, med henblik på at opnå {% if felt.sikkerhed == "Høj grad af sikkerhed (revision)" %}høj{% else %}begrænset{% endif %} grad af sikkerhed for vores konklusion.{% endif %} Vores ansvar ifølge disse standarder og krav er nærmere beskrevet i afsnittet „Revisors ansvar“. Vi er uafhængige af selskabet i overensstemmelse med International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code) og de yderligere etiske krav, der er gældende i Danmark, ligesom vi har opfyldt vores øvrige etiske forpligtelser i henhold til disse krav og IESBA Code. Revisionsvirksomheden anvender ISQM 1. Det er vores opfattelse, at det opnåede bevis er tilstrækkeligt og egnet som grundlag for vores konklusion.

## Fremhævelse af forhold – regnskabsgrundlag og begrænsning i distribution og anvendelse

Vi henleder opmærksomheden på, at opgørelsen er udarbejdet på grundlag af {{ felt.kriterier }} med det formål at opfylde selskabets forpligtelse over for {{ felt.modtager }}. Opgørelsen er derfor muligvis ikke egnet til andre formål. Vores erklæring er udelukkende udarbejdet til brug for {{ kunde.navn }} og {{ felt.modtager }} og bør ikke udleveres til eller anvendes af andre parter. Vores konklusion er ikke modificeret som følge af dette forhold.

## Ledelsens ansvar

Ledelsen har ansvaret for udarbejdelsen af opgørelsen i overensstemmelse med {{ felt.kriterier }} og for den interne kontrol, som ledelsen anser for nødvendig for at udarbejde en opgørelse uden væsentlig fejlinformation, uanset om denne skyldes besvigelser eller fejl.{% if branche.kontantintensiv %} Ledelsen er herunder ansvarlig for, at alt salg, også kontantsalg, registreres løbende og fuldstændigt i kasseapparat/salgssystem, og at dagsopgørelser, kasseafstemninger og bankindsætninger opbevares som regnskabsmateriale efter bogføringsloven.{% endif %}

## Revisors ansvar

Vores mål er at opnå {% if felt.sikkerhed == "Høj grad af sikkerhed (revision)" %}høj{% else %}begrænset{% endif %} grad af sikkerhed for, om opgørelsen som helhed er uden væsentlig fejlinformation, uanset om denne skyldes besvigelser eller fejl, og at afgive en erklæring med en konklusion. {% if felt.sikkerhed == "Høj grad af sikkerhed (revision)" %}Høj grad af sikkerhed er et højt niveau af sikkerhed, men er ikke en garanti for, at en revision altid vil afdække væsentlig fejlinformation, når sådan findes. Vores handlinger har omfattet vurdering af risici for væsentlig fejlinformation, forståelse af processer og kontroller for registrering af salg, afstemning af opgørelsen til bogføring og momsangivelser, analytiske handlinger samt stikprøvevis kontrol af salgstransaktioner og periodeafgrænsning.{% else %}Et review omfatter primært forespørgsler til ledelsen, analytiske handlinger og afstemning af opgørelsen til bogføring og momsangivelser. Handlingerne er væsentligt mindre omfattende end ved en revision, og vi udtrykker derfor ikke en revisionskonklusion.{% endif %}{% if branche.kontantintensiv %} Vores handlinger har særligt omfattet fuldstændigheden af kontantsalg, herunder kasseafstemninger, z-rapporter, bankindsætninger og analyse af bruttoavance og vareforbrug.{% endif %}

{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
