---
{
  "title": "Vurderingsberetning ved konvertering af gæld (SL §§ 160-161)",
  "description": "Vurderingsberetning med høj grad af sikkerhed (ISAE 3000) ved kapitalforhøjelse, hvor indskuddet sker ved konvertering af gæld (fordring på selskabet). Fordringen værdiansættes under hensyn til selskabets betalingsevne – ikke automatisk til pålydende. Henviser til ledelsens redegørelse efter § 161, stk. 2. Bemærk: Selskabsloven § 161 kræver en redegørelse fra det centrale ledelsesorgan; om der tillige kræves vurderingsberetning efter § 160, jf. §§ 36-37, skal revisor afklare i den konkrete sag (feltet Retsgrundlag).",
  "kind": "erklaering",
  "references": ["Selskabsloven §§ 36-37, 160 og 161 (LBK nr. 331 af 20/03/2025)", "Erhvervsstyrelsens vejledning om anvendelse af vurderingsberetninger ved registreringer", "ISAE 3000 (Revideret)", "ISQM 1", "Erklæringsbekendtgørelsen (BEK nr. 518 af 24/05/2024) §§ 18-21"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "retsgrundlag", "label": "Retsgrundlag for beretningen (udfyldes af revisor – afklar, om selskabslovens § 160, jf. §§ 36-37, finder anvendelse, eller om beretningen afgives efter aftale)", "type": "text"},
    {"name": "kreditor", "label": "Kreditor/indskyder", "type": "text"},
    {"name": "fordring_beskrivelse", "label": "Beskrivelse af fordringen (grundlag, stiftelsestidspunkt, rente, forfald, evt. efterstillelse)", "type": "textarea"},
    {"name": "fordring_paalydende", "label": "Fordringens pålydende inkl. påløbne renter (kr.)", "type": "number"},
    {"name": "vurderingsdato", "label": "Vurderingsdato", "type": "text"},
    {"name": "solvens", "label": "Selskabets betalingsevne på vurderingsdagen", "type": "select", "options": ["Selskabet var på vurderingsdagen solvent og i stand til at indfri fordringen ved forfald – fordringen er ansat til pålydende.", "Selskabet var på vurderingsdagen ikke i stand til fuldt ud at indfri fordringen – fordringen er ansat til en dagsværdi under pålydende."], "default": "Selskabet var på vurderingsdagen solvent og i stand til at indfri fordringen ved forfald – fordringen er ansat til pålydende."},
    {"name": "vurderingsgrundlag", "label": "Grundlag for vurderingen af betalingsevnen (fx mellembalance pr. dato, likviditetsbudget)", "type": "textarea", "default": "en af ledelsen udarbejdet balance pr. vurderingsdagen og et likviditetsbudget for de kommende 12 måneder"},
    {"name": "ansat_vaerdi", "label": "Ansat økonomisk værdi af fordringen (kr.)", "type": "number"},
    {"name": "nominel_kapital", "label": "Nominel værdi af nye kapitalandele (kr.)", "type": "number"},
    {"name": "overkurs", "label": "Overkurs (kr., tom = kurs pari)", "type": "number"},
    {"name": "vederlag_i_alt", "label": "Vederlag i alt (kr.)", "type": "number"},
    {"name": "redegoerelse_161", "label": "Ledelsens redegørelse efter § 161, stk. 2, foreligger (ellers: kapitalejerne har i enighed fravalgt den, § 161, stk. 4)", "type": "checkbox", "default": true},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "mne_nr", "label": "Revisors MNE-nr.", "type": "text"},
    {"name": "sted", "label": "Sted for underskrift (by)", "type": "text"},
    {"name": "erklaeringsdato", "label": "Erklæringens dato (højst 4 uger før beslutningen)", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
# Vurderingsberetning ved kapitalforhøjelse i {{ kunde.navn }} ved konvertering af gæld

Til {{ kunde.ledelsesorgan }} og {{ kunde.kapitalejere }} i {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}

Som uvildig og sagkyndig vurderingsmand, jf. selskabslovens § 37, stk. 1, afgiver vi vurderingsberetning efter {{ felt.retsgrundlag }} i forbindelse med forhøjelse af selskabskapitalen ved konvertering af en fordring på selskabet tilhørende {{ felt.kreditor }}.

## Konklusion

Det er vores opfattelse, at den ansatte økonomiske værdi af fordringen pr. {{ felt.vurderingsdato }} på {{ felt.ansat_vaerdi }} kr. mindst svarer til det aftalte vederlag, herunder den nominelle værdi af de kapitalandele, der skal udstedes, på {{ felt.nominel_kapital }} kr.{% if felt.overkurs %} med tillæg af overkurs på {{ felt.overkurs }} kr.{% endif %}, i alt {{ felt.vederlag_i_alt }} kr.

## Beskrivelse af indskuddet

Indskuddet består af en fordring på {{ kunde.navn }} med en pålydende værdi inkl. påløbne renter på {{ felt.fordring_paalydende }} kr.

{{ felt.fordring_beskrivelse }}

Fordringen bortfalder ved konverteringen, og selskabets gæld nedbringes tilsvarende.

## Anvendt vurderingsmetode

Fordringen er værdiansat under hensyn til selskabets evne til at indfri den. Vi har vurderet betalingsevnen på grundlag af {{ felt.vurderingsgrundlag }}.

{{ felt.solvens }}

## Vederlag

Som vederlag udstedes kapitalandele med en nominel værdi på {{ felt.nominel_kapital }} kr. til kurs {% if felt.overkurs %}over pari med en overkurs på {{ felt.overkurs }} kr{% else %}pari{% endif %}, i alt {{ felt.vederlag_i_alt }} kr.

{% if felt.redegoerelse_161 %}Det centrale ledelsesorgan har i en redegørelse efter selskabslovens § 161, stk. 2, redegjort for årsagen til og tidspunktet for gældens stiftelse og for begrundelsen for forslaget om konvertering. Vi har gennemgået redegørelsen, og den er i overensstemmelse med de oplysninger, vi har modtaget.{% else %}Kapitalejerne har i enighed besluttet, at der ikke skal udarbejdes en redegørelse efter selskabslovens § 161, stk. 2, jf. stk. 4.{% endif %}

## Grundlag for konklusion

Vi har udført vores arbejde i overensstemmelse med ISAE 3000 (Revideret), Andre erklæringsopgaver med sikkerhed end revision eller review af historiske finansielle oplysninger, og de yderligere krav, der er gældende i Danmark, med henblik på at opnå høj grad af sikkerhed for vores konklusion. Vi er uafhængige af selskabet og af kreditor i overensstemmelse med IESBA Code og de yderligere etiske krav, der er gældende i Danmark, ligesom vi har opfyldt vores øvrige etiske forpligtelser i henhold til disse krav. Revisionsvirksomheden anvender ISQM 1. Det er vores opfattelse, at det opnåede bevis er tilstrækkeligt og egnet som grundlag for vores konklusion.

## Ledelsens ansvar

Ledelsen har ansvaret for at fastsætte konverteringsvilkårene og for at tilvejebringe dokumentation for fordringens eksistens, størrelse og retsgrundlag samt for selskabets økonomiske stilling og betalingsevne.

## Vurderingsmandens ansvar

Vores ansvar er at udtrykke en konklusion om, hvorvidt den ansatte økonomiske værdi af fordringen mindst svarer til vederlaget. Vores handlinger har omfattet afstemning af fordringen til selskabets bogføring og underliggende aftaler, bekræftelse fra kreditor, vurdering af selskabets balance, likviditet og budgetter pr. vurderingsdagen, vurdering af efterfølgende begivenheder frem til datoen for beretningen og indhentelse af ledelseserklæring.

## Begrænsning i anvendelse

Beretningen er udarbejdet til brug for kapitalforhøjelsen og er ikke egnet til andre formål. Afgives den efter selskabslovens § 160, jf. §§ 36 og 37, må vurderingen ikke være foretaget mere end 4 uger før beslutningen om kapitalforhøjelsen, jf. § 36, stk. 2.

{{ felt.sted }}, den {{ felt.erklaeringsdato }}

**{{ firma.navn }}**
CVR-nr. {{ firma.cvr }}

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}
MNE-nr. {{ felt.mne_nr }}
