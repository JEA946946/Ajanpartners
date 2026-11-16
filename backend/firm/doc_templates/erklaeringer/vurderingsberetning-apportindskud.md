---
{
  "title": "Vurderingsberetning ved apportindskud (SL §§ 36-37 og 160)",
  "description": "Vurderingsberetning med høj grad af sikkerhed (ISAE 3000) ved stiftelse eller kapitalforhøjelse med indskud af andre værdier end kontanter (fx aktiver, kapitalandele). Indeholder de fire lovpligtige elementer i SL § 36, stk. 1, og Erhvervsstyrelsens krævede konklusionsformulering. Ved indskud af en bestående virksomhed bruges skabelonen om åbningsbalance.",
  "kind": "erklaering",
  "references": ["Selskabsloven §§ 35-38 og 160 (LBK nr. 331 af 20/03/2025)", "Erhvervsstyrelsens vejledning om anvendelse af vurderingsberetninger ved registreringer", "ISAE 3000 (Revideret)", "ISQM 1", "Erklæringsbekendtgørelsen (BEK nr. 518 af 24/05/2024) §§ 18-21"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "situation", "label": "Situation", "type": "select", "options": ["Stiftelse", "Kapitalforhøjelse"], "default": "Kapitalforhøjelse"},
    {"name": "modtager", "label": "Til (fx stifterne / det centrale ledelsesorgan og kapitalejerne)", "type": "text", "default": "{{ kunde.ledelsesorgan }} og {{ kunde.kapitalejere }}"},
    {"name": "indskyder", "label": "Indskyder (navn, CVR/fødselsdato udelades i offentlig version)", "type": "text"},
    {"name": "indskud_beskrivelse", "label": "Beskrivelse af hvert indskud (SL § 36, stk. 1, nr. 1)", "type": "textarea"},
    {"name": "vurderingsmetode", "label": "Anvendt vurderingsmetode (nr. 2)", "type": "textarea", "default": "Indskuddet er værdiansat til dagsværdi. For materielle aktiver er dagsværdien fastsat ud fra handelspriser for tilsvarende aktiver under hensyn til alder og stand. For kapitalandele er værdien fastsat ud fra selskabets indre værdi pr. vurderingsdagen korrigeret for merværdier, der kan dokumenteres."},
    {"name": "vurderingsdato", "label": "Vurderingsdato", "type": "text"},
    {"name": "ansat_vaerdi", "label": "Ansat økonomisk værdi (kr.)", "type": "number"},
    {"name": "nominel_kapital", "label": "Nominel værdi af nye kapitalandele (kr.)", "type": "number"},
    {"name": "overkurs", "label": "Overkurs (kr., tom = kurs pari)", "type": "number"},
    {"name": "vederlag_i_alt", "label": "Vederlag i alt (kr., nominel + overkurs + evt. andet vederlag)", "type": "number"},
    {"name": "andet_vederlag", "label": "Andet vederlag end kapitalandele (fx gældsbrev), hvis relevant", "type": "text"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato (højst 4 uger før stiftelsesdokument/beslutning)", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Vurderingsberetning ved {% if felt.situation == "Stiftelse" %}stiftelse af{% else %}kapitalforhøjelse i{% endif %} {{ kunde.navn }} ved indskud af andre værdier end kontanter

Til {{ felt.modtager }}

Som uvildig og sagkyndig vurderingsmand, jf. selskabslovens § 37, stk. 1, afgiver vi hermed vurderingsberetning efter selskabslovens § 36{% if felt.situation == "Kapitalforhøjelse" %}, jf. § 160{% endif %}, i forbindelse med {% if felt.situation == "Stiftelse" %}stiftelsen af {{ kunde.navn }}{% else %}forhøjelsen af selskabskapitalen i {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }},{% endif %} med indskud af andre værdier end kontanter fra {{ felt.indskyder }}.

## Konklusion

Det er vores opfattelse, at den ansatte økonomiske værdi af indskuddet pr. {{ felt.vurderingsdato }} på {{ felt.ansat_vaerdi }} kr. mindst svarer til det aftalte vederlag, herunder den nominelle værdi af de kapitalandele, der skal udstedes, på {{ felt.nominel_kapital }} kr.{% if felt.overkurs %} med tillæg af overkurs på {{ felt.overkurs }} kr.{% endif %}{% if felt.andet_vederlag %} og andet vederlag i form af {{ felt.andet_vederlag }}{% endif %}, i alt {{ felt.vederlag_i_alt }} kr.

## Beskrivelse af indskuddet

{{ felt.indskud_beskrivelse }}

## Anvendte vurderingsmetoder

{{ felt.vurderingsmetode }}

Efter vores vurdering er de anvendte metoder passende under hensyn til indskuddets art.

## Vederlag

Som vederlag for indskuddet udstedes kapitalandele i {{ kunde.navn }} med en nominel værdi på {{ felt.nominel_kapital }} kr. til kurs {% if felt.overkurs %}over pari med en overkurs på {{ felt.overkurs }} kr{% else %}pari{% endif %}{% if felt.andet_vederlag %} samt {{ felt.andet_vederlag }}{% endif %}. Vederlaget udgør i alt {{ felt.vederlag_i_alt }} kr.

## Grundlag for konklusion

Vi har udført vores arbejde i overensstemmelse med ISAE 3000 (Revideret), Andre erklæringsopgaver med sikkerhed end revision eller review af historiske finansielle oplysninger, og de yderligere krav, der er gældende i Danmark, med henblik på at opnå høj grad af sikkerhed for vores konklusion. Vores ansvar ifølge denne standard og disse krav er nærmere beskrevet i afsnittet „Vurderingsmandens ansvar“.

Vi er uafhængige af {{ kunde.navn }} og af indskyderen i overensstemmelse med International Ethics Standards Board for Accountants' internationale retningslinjer for revisorers etiske adfærd (IESBA Code) og de yderligere etiske krav, der er gældende i Danmark, ligesom vi har opfyldt vores øvrige etiske forpligtelser i henhold til disse krav og IESBA Code. Revisionsvirksomheden anvender ISQM 1 og opretholder et kvalitetsstyringssystem i overensstemmelse hermed.

Det er vores opfattelse, at det opnåede bevis er tilstrækkeligt og egnet som grundlag for vores konklusion.

## Ledelsens ansvar

{% if felt.situation == "Stiftelse" %}Stifterne{% else %}Ledelsen{% endif %} har ansvaret for at fastsætte vederlaget og for at tilvejebringe de oplysninger og den dokumentation for indskuddets eksistens, ejerskab, tilstand og værdi, der er nødvendig for vurderingen. Ledelsen har endvidere ansvaret for, at indskuddet overdrages til selskabet frit af rettigheder, der ikke er oplyst over for os.

## Vurderingsmandens ansvar

Vores ansvar er på grundlag af vores handlinger at udtrykke en konklusion om, hvorvidt den ansatte økonomiske værdi af indskuddet mindst svarer til det aftalte vederlag. Vi har planlagt og udført vores handlinger med henblik på at opnå høj grad af sikkerhed herfor. Vores handlinger har omfattet:

- kontrol af indskuddets eksistens og indskyderens adkomst og råderet, herunder gennemgang af aftaler, registreringer (fx tingbog, bilregister, ejerbog) og eventuelle pantsætninger;
- vurdering af de anvendte vurderingsmetoder og af forudsætningerne for den ansatte værdi, herunder indhentelse af sammenlignelige priser, regnskaber eller eksterne vurderinger;
- vurdering af, om der efter vurderingsdatoen og frem til datoen for denne beretning er indtruffet forhold, som forringer værdien;
- indhentelse af skriftlige bekræftelser fra ledelsen og indskyderen.

## Begrænsning i anvendelse

Vurderingsberetningen er udarbejdet til opfyldelse af selskabslovens § 36{% if felt.situation == "Kapitalforhøjelse" %}, jf. § 160{% endif %}{% if felt.situation == "Stiftelse" %} og skal vedhæftes stiftelsesdokumentet{% endif %}. Vurderingen må ikke være foretaget mere end 4 uger før {% if felt.situation == "Stiftelse" %}underskrivelsen af stiftelsesdokumentet{% else %}beslutningen om kapitalforhøjelsen{% endif %}, jf. selskabslovens § 36, stk. 2{% if felt.situation == "Kapitalforhøjelse" %}, jf. § 160{% endif %}. Beretningen er ikke egnet til andre formål.

{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
