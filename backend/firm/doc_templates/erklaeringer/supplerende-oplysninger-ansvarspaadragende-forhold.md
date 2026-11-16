---
{
  "title": "Supplerende oplysninger – ansvarspådragende forhold (afsnit til påtegning)",
  "description": "Afsnit til indsættelse i revisionspåtegning eller erklæring om udvidet gennemgang, når der er begrundet formodning om, at ledelsen kan ifalde erstatnings- eller strafansvar: lån til kapitalejere/ledelse (ulovlige lån ydet før 2025 efter de ophævede SL §§ 210 og 215; nyere lån vurderes efter SL §§ 115-118 og 127), moms/A-skat ikke rettidigt afregnet, kapitaltab (SL § 119), bogføringsloven, ulovlig udlodning m.v. Kopiér det flettede afsnit ind i feltet Supplerende oplysninger i påtegningsskabelonen.",
  "kind": "erklaering",
  "references": ["Erklæringsbekendtgørelsen § 7, stk. 2 og 4", "Erhvervsstyrelsens vejledning om erklæringsbekendtgørelsen (opdateret 26/03/2026)", "Revisorloven § 16 og § 22 (LBK nr. 206 af 20/02/2025)", "Selskabsloven §§ 115-119, 127 og 179-182", "Selskabsloven §§ 210-215 (ophævet pr. 1/1 2025 ved lov nr. 1668 af 30/12/2024; gælder fortsat for ældre lån)", "Opkrævningsloven og momsloven (rettidig angivelse/betaling)", "Bogføringsloven (lov nr. 700 af 24/05/2022)"],
  "legal_forms": ["aps", "as", "ivs", "holding", "andet"],
  "industry_aware": false,
  "fields": [
    {"name": "kapitalejerlaan", "label": "Ansvarspådragende lån/sikkerhedsstillelse til kapitalejer eller ledelse", "type": "checkbox", "default": false},
    {"name": "kapitalejerlaan_regel", "label": "Regelgrundlag (SL §§ 210-212 er ophævet pr. 1/1 2025, lov nr. 1668 af 30/12/2024)", "type": "select", "options": ["Lån ydet før 1. januar 2025 i strid med de dagældende regler", "Lån ydet efter 1. januar 2025, der ikke er i selskabets interesse eller er uforsvarligt"], "default": "Lån ydet før 1. januar 2025 i strid med de dagældende regler"},
    {"name": "kapitalejerlaan_art", "label": "Art", "type": "select", "options": ["ydet lån til", "stillet sikkerhed for", "ydet lån til og stillet sikkerhed for"], "default": "ydet lån til"},
    {"name": "kapitalejerlaan_modtager", "label": "Modtagerens rolle (uden navn)", "type": "select", "options": ["en kapitalejer", "et medlem af ledelsen", "en kapitalejer, der tillige er medlem af ledelsen", "en nærtstående til en kapitalejer"], "default": "en kapitalejer, der tillige er medlem af ledelsen"},
    {"name": "kapitalejerlaan_status", "label": "Status pr. påtegningsdatoen", "type": "select", "options": ["Lånet er ikke tilbagebetalt pr. datoen for denne erklæring.", "Lånet er tilbagebetalt med tillæg af renter efter balancedagen.", "Lånet er tilbagebetalt i regnskabsåret."], "default": "Lånet er ikke tilbagebetalt pr. datoen for denne erklæring."},
    {"name": "skatter_afgifter", "label": "Moms/A-skat/AM-bidrag ikke rettidigt angivet eller afregnet", "type": "checkbox", "default": false},
    {"name": "skatter_afgifter_hvilke", "label": "Hvilke skatter og afgifter", "type": "text", "default": "moms, A-skat og arbejdsmarkedsbidrag"},
    {"name": "kapitaltab", "label": "Kapitaltab – ledelsen har ikke handlet efter SL § 119", "type": "checkbox", "default": false},
    {"name": "bogfoeringsloven", "label": "Overtrædelse af bogføringsloven", "type": "checkbox", "default": false},
    {"name": "bogfoeringsloven_forhold", "label": "Hvilke krav (fx rettidig registrering, opbevaring, digitalt bogføringssystem)", "type": "text", "default": "rettidig registrering af transaktioner og opbevaring af regnskabsmateriale"},
    {"name": "ulovlig_udlodning", "label": "Udlodning i strid med SL §§ 179-182", "type": "checkbox", "default": false},
    {"name": "andet_overskrift", "label": "Andet forhold – overskrift", "type": "text"},
    {"name": "andet_tekst", "label": "Andet forhold – beskrivelse (kun de ansvarspådragende forhold, ingen navne, ingen sanktioner)", "type": "textarea"}
  ]
}
---
## Erklæring i henhold til anden lovgivning og øvrig regulering

{% if felt.kapitalejerlaan %}{% if felt.kapitalejerlaan_regel == "Lån ydet før 1. januar 2025 i strid med de dagældende regler" %}### Ulovligt kapitalejerlån ydet før 1. januar 2025

Selskabet har før 1. januar 2025 {{ felt.kapitalejerlaan_art }} {{ felt.kapitalejerlaan_modtager }}, i strid med de dagældende regler i selskabslovens § 210. Et sådant lån skal tilbagebetales med renter, jf. selskabslovens § 215, stk. 1. {{ felt.kapitalejerlaan_status }} Ledelsen kan derved have ifaldt ansvar.{% else %}### Lån til kapitalejer eller ledelse, der ikke er i selskabets interesse

Selskabet har i regnskabsåret {{ felt.kapitalejerlaan_art }} {{ felt.kapitalejerlaan_modtager }}, på vilkår, som efter vores vurdering ikke er i selskabets interesse eller ikke er forsvarlige under hensyn til selskabets økonomiske stilling, jf. selskabslovens §§ 115-118 og 127. {{ felt.kapitalejerlaan_status }} Ledelsen kan derved have ifaldt ansvar.{% endif %}

{% endif %}{% if felt.skatter_afgifter %}### Manglende rettidig angivelse og afregning af skatter og afgifter

Selskabet har i regnskabsåret ikke rettidigt angivet og afregnet {{ felt.skatter_afgifter_hvilke }} i overensstemmelse med reglerne herom. Ledelsen kan derved have ifaldt ansvar.

{% endif %}{% if felt.kapitaltab %}### Kapitaltab

Selskabets egenkapital udgør mindre end halvdelen af selskabskapitalen. Ledelsen har ikke inden for den frist, der følger af selskabslovens § 119, sikret, at kapitalejerne på en generalforsamling er blevet orienteret om selskabets økonomiske stilling og om nødvendigt har fået en redegørelse for, hvilke foranstaltninger der bør træffes. Ledelsen kan derved have ifaldt ansvar.

{% endif %}{% if felt.bogfoeringsloven %}### Overtrædelse af bogføringsloven

Selskabet har i regnskabsåret ikke overholdt bogføringslovens krav om {{ felt.bogfoeringsloven_forhold }}. Ledelsen kan derved have ifaldt ansvar.

{% endif %}{% if felt.ulovlig_udlodning %}### Udlodning i strid med selskabsloven

Selskabet har i regnskabsåret foretaget udlodning til kapitalejerne, som ikke opfylder betingelserne i selskabslovens §§ 179-182, idet udlodningen oversteg de frie reserver eller ikke var forsvarlig under hensyn til selskabets økonomiske stilling. Ledelsen kan derved have ifaldt ansvar.

{% endif %}{% if felt.andet_tekst %}### {{ felt.andet_overskrift }}

{{ felt.andet_tekst }}

{% endif %}
