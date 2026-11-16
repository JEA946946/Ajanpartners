---
{
  "title": "Beslutning om kapitalforhøjelse",
  "description": "Generalforsamlingsbeslutning om kontant forhøjelse, apportindskud, gældskonvertering eller fondsforhøjelse med de obligatoriske angivelser i SL § 158, fortegningsret og anmeldelse.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 154-167", "Selskabsloven §§ 33, 35-38 (indskud og vurderingsberetning)", "Selskabsloven § 158", "Selskabsloven § 162", "Selskabsloven § 165 (fondsandele)", "Aktieavancebeskatningsloven"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "gf_dato", "label": "Dato for generalforsamlingen", "type": "date"},
    {"name": "dirigent", "label": "Dirigent", "type": "text"},
    {"name": "indskudsform", "label": "Indskudsform", "type": "select", "options": ["Kontant", "Apport (andre værdier end kontanter)", "Gældskonvertering", "Fondsforhøjelse"], "default": "Kontant"},
    {"name": "nuvaerende_kapital", "label": "Nuværende selskabskapital (kr.)", "type": "number"},
    {"name": "min_beloeb", "label": "Mindste forhøjelsesbeløb (nominelt kr.)", "type": "number"},
    {"name": "max_beloeb", "label": "Højeste forhøjelsesbeløb (nominelt kr.)", "type": "number"},
    {"name": "kurs", "label": "Tegningskurs", "type": "text", "default": "100"},
    {"name": "stykstoerrelse", "label": "Kapitalandelenes størrelse (kr.)", "type": "text", "default": "1"},
    {"name": "tegner", "label": "Tegner(e) og fordeling", "type": "textarea"},
    {"name": "fortegningsret", "label": "Fortegningsret", "type": "select", "options": ["Eksisterende kapitalejere tegner forholdsmæssigt", "Fortegningsretten fraviges til fordel for de navngivne tegnere", "Alle kapitalejere har givet afkald"], "default": "Eksisterende kapitalejere tegner forholdsmæssigt"},
    {"name": "tegningsfrist", "label": "Tegningsfrist", "type": "date"},
    {"name": "indbetalingsfrist", "label": "Indbetalingsfrist", "type": "date"},
    {"name": "omkostninger", "label": "Anslåede omkostninger (kr.)", "type": "number"},
    {"name": "apport_beskrivelse", "label": "Beskrivelse af apportindskud/fordring", "type": "textarea"},
    {"name": "vurderingsberetning_dato", "label": "Dato for vurderingsberetning (apport/gæld)", "type": "date"},
    {"name": "vedtaegtsbestemmelse", "label": "Ny ordlyd af vedtægternes kapitalbestemmelse", "type": "textarea"}
  ]
}
---
# Beslutning om kapitalforhøjelse

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}

På generalforsamling den {{ felt.gf_dato }} under ledelse af dirigent {{ felt.dirigent }} blev det med det flertal, der kræves til vedtægtsændring (mindst 2/3 af de afgivne stemmer og den repræsenterede kapital, jf. selskabslovens §§ 106 og 154, stk. 2), besluttet at forhøje selskabskapitalen på følgende vilkår:

{% if felt.indskudsform == "Fondsforhøjelse" %}
1. Selskabskapitalen forhøjes fra nominelt {{ felt.nuvaerende_kapital }} kr. med nominelt {{ felt.max_beloeb }} kr. ved udstedelse af fondsandele.
2. Forhøjelsen sker ved overførsel fra overført overskud eller frie reserver opført i selskabets senest godkendte årsrapport (selskabslovens § 165). Er der sket begivenheder af væsentlig betydning efter balancedagen, er dette vurderet.
3. Fondsandelene tilfalder kapitalejerne i forhold til deres kapitalandele og giver ret til udbytte fra registreringen.
4. De anslåede omkostninger, som selskabet afholder, udgør {{ felt.omkostninger }} kr.
{% else %}
1. **Beløb:** Selskabskapitalen forhøjes fra nominelt {{ felt.nuvaerende_kapital }} kr. med mindst nominelt {{ felt.min_beloeb }} kr. og højst nominelt {{ felt.max_beloeb }} kr.
2. **Delvis indbetaling:** {% if felt.indskudsform == "Kontant" %}Kapitalen skal indbetales fuldt ud.{% elif felt.indskudsform == "Gældskonvertering" %}Kapitalen indbetales fuldt ud ved konvertering af fordringen.{% else %}Delvis indbetaling kan ikke ske, idet selskabskapitalen og en eventuel overkurs skal indbetales fuldt ud ved indskud af andre værdier end kontanter (selskabslovens § 33).{% endif %}
3. **Tegningskurs og størrelse:** Tegningskursen er {{ felt.kurs }}, og kapitalandelene udstedes i stykker á {{ felt.stykstoerrelse }} kr.
4. **Rettigheder:** De nye kapitalandele giver ret til udbytte og andre rettigheder fra registreringen i Erhvervsstyrelsen.
5. **Omkostninger:** De anslåede omkostninger, som selskabet afholder, udgør {{ felt.omkostninger }} kr.
6. **Klasse:** De nye kapitalandele har samme rettigheder som de eksisterende og hører til samme klasse.
7. **Fortegningsret:** {% if felt.fortegningsret == "Eksisterende kapitalejere tegner forholdsmæssigt" %}De eksisterende kapitalejere har fortegningsret i forhold til deres kapitalandele (selskabslovens § 162, stk. 1).{% elif felt.fortegningsret == "Fortegningsretten fraviges til fordel for de navngivne tegnere" %}Fortegningsretten fraviges til fordel for de nedenfor nævnte tegnere med det flertal, der kræves til vedtægtsændring (selskabslovens § 162, stk. 2). Sker tegningen til favørkurs til andre end kapitalejerne og medarbejderne, kræves tilslutning fra mindst 9/10 (§ 107, stk. 2, nr. 1).{% else %}Samtlige kapitalejere har givet afkald på fortegningsret.{% endif %} Der er ingen indskrænkning i de nye kapitalejeres fortegningsret ved fremtidige forhøjelser.
8. **Tegning:** Tegning sker skriftligt (selskabslovens § 163) senest {{ felt.tegningsfrist }}.{% if felt.fortegningsret == "Eksisterende kapitalejere tegner forholdsmæssigt" %} Kapitalejerne skal udnytte fortegningsretten inden for mindst 2 uger fra afsendelse af underretning.{% endif %}
9. **Indbetaling:** {% if felt.indskudsform == "Kontant" %}Kontant senest {{ felt.indbetalingsfrist }} til selskabets bankkonto.{% elif felt.indskudsform == "Gældskonvertering" %}Ved konvertering af fordring på selskabet: {{ felt.apport_beskrivelse }}{% else %}Ved indskud af andre værdier end kontanter: {{ felt.apport_beskrivelse }}{% endif %}
10. **Omsættelighed:** De nye kapitalandele er underlagt samme omsættelighedsbegrænsninger som efter vedtægterne. Kapitalandelene er ikke omsætningspapirer{% if kunde.selskabsform_kode == "as" %} og skal lyde på navn{% endif %}.
11. **Tegnere:** {{ felt.tegner }}
{% if felt.indskudsform == "Apport (andre værdier end kontanter)" %}
**Vurderingsberetning:** Der er udarbejdet vurderingsberetning dateret {{ felt.vurderingsberetning_dato }}, jf. selskabslovens §§ 36, 37 og 160 (medmindre ledelsen har afgivet erklæring efter § 38, stk. 2). Vurderingen må ikke være foretaget mere end 4 uger før beslutningen (§ 36, stk. 2, jf. § 160). Den vedlægges anmeldelsen.
{% elif felt.indskudsform == "Gældskonvertering" %}
**Gældskonvertering:** Det centrale ledelsesorgan har redegjort for årsagen til og tidspunktet for gældsstiftelsen og for grundene til forslaget om konvertering (selskabslovens § 161, stk. 2; kan i enighed fraviges, stk. 4). Om der tillige skal udarbejdes vurderingsberetning (dato: {{ felt.vurderingsberetning_dato }}), kontrolleres i det konkrete tilfælde.
{% endif %}
{% endif %}

**Vedtægtsændring:** Vedtægternes bestemmelse om selskabskapitalen affattes herefter således:

> {{ felt.vedtaegtsbestemmelse }}

{% if kunde.selskabsform_kode == "as" %}Forslaget og de dokumenter, der kræves efter selskabslovens § 156 (bl.a. seneste årsrapport og ledelsens beretning om væsentlige begivenheder efter balancedagen, hvis årsrapporten ikke behandles på samme generalforsamling), har været gjort tilgængelige for aktionærerne.{% endif %}

Hvis mindstebeløbet ikke er tegnet inden for tegningsfristen, bortfalder beslutningen, og indbetalte beløb tilbagebetales hurtigst muligt (selskabslovens § 164).

## Opfølgning
- [ ] Tegningslister/tegningsblanketter underskrevet.
- [ ] Indbetaling dokumenteret (kontoudtog) eller apportindskud overdraget.
- [ ] Kapitalforhøjelsen anmeldes/registreres i Erhvervsstyrelsen inden for fristen i selskabslovens § 9 (2 uger efter den retsstiftende beslutning), med opdaterede vedtægter{% if felt.indskudsform == "Apport (andre værdier end kontanter)" %} og vurderingsberetning{% endif %}.
- [ ] Ejerbog og ejerregister opdateres; ejerandele, der krydser grænserne på 5, 10, 15, 20, 25, 50, 90 eller 100 % eller 1/3 og 2/3, registreres (selskabslovens §§ 55-58).
- [ ] Reelle ejere vurderes på ny (§ 58 a).
- [ ] Skat: anskaffelsessum og -tidspunkt for de nye kapitalandele noteres til brug for aktieavanceopgørelsen. Ved gældskonvertering vurderes de skattemæssige konsekvenser for kreditor og debitor efter kursgevinstloven (gældskonvertering kan sidestilles med eftergivelse, hvis fordringens værdi er lavere end kursen på de udstedte kapitalandele), og om selskabets fremførte underskud påvirkes (SEL §§ 12 A-12 B).
- [ ] Regnskab: overkurs posteres som overkurs ved emission under egenkapitalen.

{{ kunde.by }}, {{ felt.gf_dato }}

Som dirigent:

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.dirigent }}
