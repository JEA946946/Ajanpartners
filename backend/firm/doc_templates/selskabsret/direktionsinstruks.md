---
{
  "title": "Direktionsinstruks",
  "description": "Bestyrelsens skriftlige instruks til direktionen om daglig ledelse, beføjelser, beløbsgrænser, rapportering, bogføring og formueforvaltning (SL §§ 115, 117 og 118).",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 115, 117 og 118", "Bogføringsloven", "Selskabsloven § 119"],
  "legal_forms": ["as", "aps", "holding"],
  "industry_aware": true,
  "fields": [
    {"name": "direktoer", "label": "Direktør(er)", "type": "text"},
    {"name": "vedtaget_dato", "label": "Vedtaget dato", "type": "date"},
    {"name": "beloebsgraense", "label": "Beløbsgrænse for enkeltdispositioner uden for budget (kr.)", "type": "number", "default": "250000"},
    {"name": "investeringsgraense", "label": "Grænse for investeringer i alt pr. år uden for budget (kr.)", "type": "number", "default": "500000"},
    {"name": "rapportering", "label": "Rapportering", "type": "select", "options": ["Månedlig", "Kvartalsvis"], "default": "Månedlig"},
    {"name": "to_i_forening", "label": "Betalinger over (kr.) kræver godkendelse af to personer", "type": "number", "default": "50000"}
  ]
}
---
# Direktionsinstruks

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}
Til direktionen: {{ felt.direktoer }}

Bestyrelsen fastsætter hermed følgende retningslinjer for direktionens arbejde, jf. selskabslovens § 117, stk. 1.

## 1. Den daglige ledelse
1. Direktionen varetager den daglige ledelse og skal følge de retningslinjer og anvisninger, bestyrelsen giver.
2. Den daglige ledelse omfatter ikke dispositioner af usædvanlig art eller stor betydning. Disse kan kun foretages efter særlig bemyndigelse fra bestyrelsen, medmindre bestyrelsens beslutning ikke kan afventes uden væsentlig ulempe; bestyrelsen skal i så fald underrettes snarest muligt.
3. Uden bestyrelsens forudgående godkendelse må direktionen ikke:
   - indgå aftaler eller foretage investeringer over {{ felt.beloebsgraense }} kr. pr. disposition eller {{ felt.investeringsgraense }} kr. i alt pr. år ud over budget,
   - købe, sælge eller pantsætte fast ejendom, virksomheder eller kapitalandele,
   - optage lån, stille garanti, kaution eller anden sikkerhed uden for sædvanlig drift,
   - indgå aftaler med kapitalejere, ledelsesmedlemmer eller disses nærtstående, herunder yde lån eller stille sikkerhed (jf. også selskabslovens § 206 om selvfinansiering),
   - ansætte eller afskedige ledende medarbejdere eller indføre bonus- og pensionsordninger,
   - anlægge eller forlige retssager af væsentlig betydning.

## 2. Bogføring og formueforvaltning
Direktionen skal sikre, at bogføringen sker efter bogføringslovens regler, herunder brug af et registreret digitalt bogføringssystem, opbevaring af bilag i 5 år og løbende afstemning, og at formueforvaltningen foregår betryggende (selskabslovens § 118, stk. 1). Betalinger over {{ felt.to_i_forening }} kr. godkendes af to personer i forening.{% if branche.kontantintensiv %} Kontanthåndtering skal ske med daglig kasseopgørelse, registrering i kasseapparat og overholdelse af hvidvasklovens kontantforbud.{% endif %}{% if branche.byggeri %} Direktionen skal sikre korrekt håndtering af RUT-registrerede underentreprenører, kædeansvar og arbejdsmiljøregler.{% endif %}

## 3. Kapitalberedskab
Direktionen skal til enhver tid vurdere den økonomiske situation og sikre, at kapitalberedskabet er forsvarligt, herunder at der er tilstrækkelig likviditet (selskabslovens § 118, stk. 2). Direktionen skal straks underrette formanden, hvis
- likviditetsbudgettet viser, at selskabet ikke kan betale sine forpligtelser rettidigt,
- egenkapitalen kan forventes at udgøre mindre end halvdelen af selskabskapitalen (§ 119), eller
- der opstår væsentlige tab, tvister, myndighedskrav eller brud på lånebetingelser (covenants).

## 4. Rapportering
Direktionen rapporterer til bestyrelsen (frekvens: {{ felt.rapportering }}) med resultat og balance sammenholdt med budget, likviditetsprognose for mindst 3 måneder, væsentlige debitorer og tab samt status på risici.{% if branche.igangvaerende_arbejder %} Rapporteringen omfatter igangværende arbejder (forventet dækningsbidrag pr. projekt).{% endif %}{% if branche.lager %} Rapporteringen omfatter lagerværdi og ukurans.{% endif %}

## 5. Skatter, afgifter og myndigheder
Direktionen sikrer rettidig angivelse og betaling af moms, A-skat, AM-bidrag, udbytteskat og øvrige afgifter, indberetning til eIndkomst samt rettidig indsendelse af årsrapport og registreringer til Erhvervsstyrelsen.{% if branche.momsfritaget %} Direktionen sikrer korrekt opgørelse af delvis momsfradrag og lønsumsafgift.{% endif %}

## 6. Underretning og samarbejde
Direktionen forbereder bestyrelsesmøderne sammen med formanden og fremsender materiale i god tid. Direktionen er forpligtet til at give bestyrelsen og revisor alle oplysninger, de anmoder om.

## 7. Ikrafttræden
Instruksen træder i kraft ved underskrift og gennemgås årligt af bestyrelsen.

{{ kunde.by }}, {{ felt.vedtaget_dato }}

For bestyrelsen:

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ (formand)

Modtaget og accepteret af direktionen:

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{{ felt.direktoer }}
