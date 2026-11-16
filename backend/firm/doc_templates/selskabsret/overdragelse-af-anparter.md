---
{
  "title": "Overdragelse af kapitalandele (transport til ejerbog)",
  "description": "Overdragelseserklæring for anparter/aktier med notering i ejerbogen, kontrol af vedtægternes omsættelighedsbegrænsninger, ejerregister, reelle ejere og skattemæssig opfølgning.",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 50-58 a", "Selskabsloven § 67 (forkøbsret m.v. i vedtægterne)", "Aktieavancebeskatningsloven", "Ligningsloven § 2", "Hvidvaskloven"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "saelger", "label": "Overdrager (navn, adresse, CPR/CVR)", "type": "text"},
    {"name": "koeber", "label": "Erhverver (navn, adresse, CPR/CVR)", "type": "text"},
    {"name": "nominelt", "label": "Nominelt beløb der overdrages (kr.)", "type": "number"},
    {"name": "kapital_i_alt", "label": "Samlet selskabskapital (kr.)", "type": "number"},
    {"name": "andele_nr", "label": "Kapitalandelenes nr./klasse", "type": "text"},
    {"name": "kobesum", "label": "Købesum (kr.)", "type": "number"},
    {"name": "overtagelsesdag", "label": "Overtagelsesdag", "type": "date"},
    {"name": "udbytte_ret", "label": "Ret til udbytte for indeværende år tilfalder", "type": "select", "options": ["Erhverver", "Overdrager"], "default": "Erhverver"},
    {"name": "forkoebsret", "label": "Vedtægterne indeholder forkøbsret/samtykkekrav", "type": "checkbox"},
    {"name": "afkald", "label": "Forkøbsberettigede har givet afkald/samtykke er givet", "type": "checkbox"},
    {"name": "naerstaaende", "label": "Overdragelse mellem nærtstående/interesseforbundne parter", "type": "checkbox"}
  ]
}
---
# Overdragelseserklæring

**Selskab:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}

Undertegnede overdrager

**{{ felt.saelger }}**

hermed til

**{{ felt.koeber }}**

kapitalandele i selskabet nominelt **{{ felt.nominelt }} kr.** (nr./klasse {{ felt.andele_nr }}) af en samlet selskabskapital på nominelt {{ felt.kapital_i_alt }} kr., med alle tilhørende rettigheder og forpligtelser fra overtagelsesdagen {{ felt.overtagelsesdag }}.

Købesummen udgør {{ felt.kobesum }} kr. og er afregnet i henhold til særskilt aftale. Udbytte, der deklareres efter overtagelsesdagen, tilfalder {{ felt.udbytte_ret|default:"erhverver" }}.

Overdrager indestår for, at kapitalandelene er fuldt indbetalt og fri for pant, udlæg og andre rettigheder.

Sted og dato: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

| Overdrager | Erhverver |
|---|---|
| \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ | \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ |
| {{ felt.saelger }} | {{ felt.koeber }} |

---

## Selskabets påtegning – notering i ejerbogen
Overdragelsen er noteret i selskabets ejerbog den \_\_\_\_\_\_\_\_\_\_.
{% if felt.forkoebsret %}{% if felt.afkald %}De forkøbsberettigede har givet skriftligt afkald, og/eller selskabets samtykke efter vedtægterne foreligger.{% else %}**OBS:** Vedtægterne indeholder forkøbsret eller samtykkekrav. Overdragelsen kan ikke noteres, før vedtægternes procedure er gennemført.{% endif %}{% endif %}

For {{ kunde.ledelsesorgan }}: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

## Tjekliste (rådgiver)
- [ ] Vedtægter og eventuel ejeraftale gennemgået for forkøbsret, samtykke, medsalgsret/-pligt og værdiansættelsesregler.
- [ ] Erhververens identitet kontrolleret (hvidvaskloven – kundekendskab hos rådgiver/bank).
- [ ] Ejerbog ajourført (selskabslovens § 50); erhverver kan ikke udøve rettigheder, før erhvervelsen er noteret eller anmeldt og dokumenteret.
- [ ] Ejerregister i CVR: meddelelse og registrering, hvis grænserne 5, 10, 15, 20, 25, 50, 90 eller 100 % eller 1/3 og 2/3 nås eller ikke længere nås (§§ 55-58).
- [ ] Reelle ejere ajourført i CVR hurtigst muligt (§ 58 a, stk. 3).
- [ ] Ledelsesændringer og tegningsregel ved ejerskifte vurderet.
- [ ] **Skat for overdrager:** Aktieavance opgjort efter aktieavancebeskatningsloven (gennemsnitsmetoden). Personer: aktieindkomst. Selskaber: skattefri ved datterselskabs-/koncernselskabsaktier (ABL § 8), skattepligtig ved porteføljeaktier.
{% if felt.naerstaaende %}- [ ] **Nærtstående:** Overdragelsen skal ske til handelsværdi (LL § 2 / statsskattelovens § 4 og praksis). Værdiansættelse dokumenteret (fx Skattestyrelsens værdiansættelsescirkulære eller særskilt vurdering); overvej bindende svar. Ved generationsskifte vurderes succession (ABL § 34) og gaveafgift.
{% endif %}- [ ] Selskabets skattemæssige underskud: ejerskifte på mere end 50 % kan begrænse fremførsel, hvis selskabet ved ejerskiftet havde passive aktiver (SEL § 12 D).
- [ ] Sambeskatning: ophør eller indtræden i sambeskatning ved ændring i koncernforbindelse (SEL § 31).
