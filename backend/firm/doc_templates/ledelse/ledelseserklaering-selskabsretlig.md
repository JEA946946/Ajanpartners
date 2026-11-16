---
{
  "title": "Ledelseserklæring – selskabsretlige erklæringer (vurderingsberetning, mellembalance, fusion)",
  "description": "Ledelsens skriftlige erklæring til vurderingsmanden/revisor ved vurderingsberetning (apport, gældskonvertering, virksomhedsomdannelse), mellembalance til udlodning og vurderingsmandserklæringer ved fusion/spaltning. Dateres samme dag som erklæringen.",
  "kind": "brev",
  "references": ["ISAE 3000 (Revideret), afsnit 56", "ISA 580", "Selskabsloven §§ 36-38, 115, 160-161, 179-183 og 240-242"],
  "legal_forms": ["aps", "as", "holding", "ivs", "enk", "pmv"],
  "industry_aware": true,
  "fields": [
    {"name": "erklaeringstype", "label": "Erklæring", "type": "select", "options": ["vurderingsberetning ved apportindskud", "vurderingsberetning ved konvertering af gæld", "vurderingsberetning med åbningsbalance ved virksomhedsomdannelse", "reviewerklæring om mellembalance til brug for udlodning", "vurderingsmandens erklæringer ved fusion/spaltning"], "default": "vurderingsberetning ved apportindskud"},
    {"name": "underskriver_rolle", "label": "Underskriver", "type": "select", "options": ["direktionen", "bestyrelsen og direktionen", "stifteren/indskyderen"], "default": "direktionen"},
    {"name": "opgoerelsesdato", "label": "Vurderings-/balancedato", "type": "text"},
    {"name": "erklaeringsdato", "label": "Dato", "type": "text", "default": "{{ dato.idag }}"}
  ]
}
---
**{{ firma.navn }}**
{{ firma.adresse }}
Att.: {{ medarbejder.navn }}

{{ felt.erklaeringsdato }}

# Ledelseserklæring – {{ felt.erklaeringstype }}

Denne erklæring afgives i forbindelse med jeres {{ felt.erklaeringstype }} vedrørende {{ kunde.navn }} med opgørelses-/vurderingsdato {{ felt.opgoerelsesdato }}. Vi bekræfter efter bedste overbevisning:

1. Vi har givet jer alle oplysninger og al dokumentation, der er relevant for opgaven, herunder aftaler, værdiansættelser, regnskaber, budgetter og referater, og vores svar på jeres forespørgsler er fyldestgørende og korrekte.
2. De aktiver og forpligtelser, der indgår i opgørelsen, eksisterer, tilhører {% if felt.erklaeringstype == "vurderingsberetning ved apportindskud" or felt.erklaeringstype == "vurderingsberetning med åbningsbalance ved virksomhedsomdannelse" %}indskyderen og overdrages til selskabet{% else %}selskabet{% endif %} fri for pant, ejendomsforbehold og andre rettigheder for tredjemand, bortset fra det, der er oplyst til jer.
3. Alle forpligtelser, herunder eventualforpligtelser, garantier, skatter og afgifter, er medtaget eller oplyst.
4. Vi er ikke bekendt med begivenheder efter {{ felt.opgoerelsesdato }} og frem til i dag, som har forringet værdien eller påvirker opgørelsen væsentligt.
{% if felt.erklaeringstype == "vurderingsberetning ved konvertering af gæld" %}5. Fordringen, der konverteres, er opstået som oplyst til jer, er ikke tidligere overdraget eller pantsat, og kreditor har accepteret konverteringen. Selskabets oplyste balance og likviditetsbudget er udarbejdet på et realistisk grundlag.
{% elif felt.erklaeringstype == "reviewerklæring om mellembalance til brug for udlodning" %}5. Mellembalancen er udarbejdet efter samme regnskabspraksis som seneste årsrapport. Vi har vurderet, at den foreslåede udlodning er forsvarlig under hensyn til selskabets økonomiske stilling, jf. selskabslovens § 179, stk. 2, og at der efter udlodningen er dækning for selskabskapitalen og bundne reserver.
{% elif felt.erklaeringstype == "vurderingsberetning med åbningsbalance ved virksomhedsomdannelse" %}5. Samtlige aktiver og forpligtelser i den personligt ejede virksomhed overdrages til selskabet, og private hævninger efter omdannelsestidspunktet er oplyst til jer. Betingelserne i virksomhedsomdannelsesloven er os bekendt opfyldt.
{% elif felt.erklaeringstype == "vurderingsmandens erklæringer ved fusion/spaltning" %}5. Fusions-/spaltningsplanen og redegørelsen giver et fyldestgørende billede af transaktionen, og vi har oplyst jer om alle kreditorforhold, sikkerhedsstillelser og låneaftaler med ejerskiftebestemmelser, der kan påvirke kreditorernes stilling.
{% else %}5. Vederlaget er fastsat på armslængdevilkår, og vi er ikke bekendt med forhold, der gør, at indskuddets værdi er lavere end vederlaget.
{% endif %}{% if branche.lager %}6. Varebeholdninger, der indgår, er optalt og målt til kostpris, dog højst nettorealisationsværdi.
{% endif %}{% if branche.investeringsejendomme %}7. Forudsætningerne for dagsværdien af ejendommene afspejler markedsforholdene på opgørelsesdatoen.
{% endif %}
Med venlig hilsen

**{{ kunde.navn }}** – {{ felt.underskriver_rolle }}

______________________________

______________________________
