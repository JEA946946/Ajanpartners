---
{
  "title": "Beslutning om frivillig likvidation",
  "description": "Generalforsamlingsbeslutning om solvent likvidation med valg af likvidator, proklama (3 måneder), likvidationsregnskab og tjekliste – samt sammenligning med opløsning ved betalingserklæring (SL § 216).",
  "kind": "beslutning",
  "references": ["Selskabsloven §§ 216-224", "Selskabsloven § 106", "Aktieavancebeskatningsloven", "Ligningsloven § 16 A, stk. 3, nr. 2", "Skatteforvaltningsloven"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": true,
  "fields": [
    {"name": "metode", "label": "Metode", "type": "select", "options": ["Likvidation ved likvidator", "Opløsning ved betalingserklæring (SL § 216)"], "default": "Likvidation ved likvidator"},
    {"name": "gf_dato", "label": "Dato for generalforsamlingen", "type": "date"},
    {"name": "dirigent", "label": "Dirigent", "type": "text"},
    {"name": "likvidator", "label": "Likvidator (navn, adresse)", "type": "text"},
    {"name": "likvidationsdato", "label": "Likvidationsbalancedag/skæringsdato", "type": "date"},
    {"name": "revisor_valgt", "label": "Revisor vælges i likvidationsperioden", "type": "checkbox"},
    {"name": "forventet_provenu", "label": "Forventet likvidationsprovenu (kr.)", "type": "number"},
    {"name": "kapitalejere_liste", "label": "Kapitalejere (navn, adresse, ejerandel) – ved betalingserklæring", "type": "textarea"}
  ]
}
---
# Beslutning om frivillig likvidation

**{{ kunde.navn }}**, CVR-nr. {{ kunde.cvr }}

{% if felt.metode == "Likvidation ved likvidator" %}
## Generalforsamlingens beslutning
På generalforsamling den {{ felt.gf_dato }} under ledelse af dirigent {{ felt.dirigent }} blev det med det flertal, der kræves til vedtægtsændring (mindst 2/3 af de afgivne stemmer og den repræsenterede kapital, jf. selskabslovens §§ 106 og 217, stk. 2), besluttet:

1. at selskabet træder i frivillig likvidation,
2. at vælge **{{ felt.likvidator }}** som likvidator (selskabslovens § 218). Likvidator træder i ledelsens sted (§ 219, stk. 1), og den hidtidige ledelse fratræder,
3. at selskabets navn fremover har tilføjelsen »i likvidation« (§ 220, stk. 2),
{% if felt.revisor_valgt %}4. at selskabets revisor fortsætter i likvidationsperioden og reviderer likvidationsregnskabet,
{% else %}4. at likvidationsregnskabet ikke revideres, idet selskabet ikke er revisionspligtigt (§ 224, stk. 2),
{% endif %}5. at likvidator bemyndiges til at anmelde beslutningen til Erhvervsstyrelsen.

Kapitalejere, der ejer mindst 25 % af kapitalen, har ret til at vælge en likvidator ved siden af de øvrige (§ 218, stk. 2).

## Forløb
| Trin | Frist/indhold | Ansvarlig |
|---|---|---|
| Anmeldelse af beslutningen | Skal være modtaget i Erhvervsstyrelsen senest 2 uger efter beslutningen (§ 220, stk. 1) | Likvidator |
| Kreditorproklama | Offentliggøres ved registreringen; kreditorer anmelder krav til likvidator senest 3 måneder fra offentliggørelsen. Alle kendte kreditorer underrettes samtidig (§ 221, stk. 1) | Likvidator |
| Åbningsbalance | Likvidationsbalance pr. {{ felt.likvidationsdato }} | Likvidator/{{ firma.navn }} |
| Realisation | Aktiver realiseres, kontrakter, lejemål, ansættelser og abonnementer opsiges; gæld betales | Likvidator |
| Skat og afgifter | Afmelding af moms, A-skat/løn, lønsumsafgift m.v.; slutopgørelse af selskabsskat (indkomståret afsluttes ved likvidationens afslutning) | {{ firma.navn }} |
| A conto-udlodning | Tidligst efter proklamafristens udløb og når kendte kreditorer er betalt, eller der er stillet betryggende sikkerhed (§ 223) | Likvidator |
| Likvidationsregnskab | Godkendes af kapitalejerne; anmeldelse skal være modtaget senest 2 uger efter godkendelsen; revideres ved revisionspligt (§ 224, stk. 2) | Likvidator |
| Slettelse | Erhvervsstyrelsen sletter selskabet | – |

Selskabets bøger og bilag skal opbevares i 5 år efter likvidationens afslutning, og ansvarlig for opbevaringen angives ved anmeldelsen.
{% else %}
## Erklæring om opløsning (selskabslovens § 216)
Undertegnede, der udgør samtlige kapitalejere i selskabet, erklærer:

1. at al gæld, forfalden som uforfalden, er betalt, og
2. at det er besluttet at opløse selskabet.

**Kapitalejere:**
{{ felt.kapitalejere_liste }}

Erklæringen skal være modtaget i Erhvervsstyrelsen senest 2 uger efter underskrivelsen og skal vedlægges en erklæring fra Skattestyrelsen om, at der ikke foreligger skatte- og afgiftskrav (§ 216, stk. 2).

**Vigtigt:** Kapitalejerne hæfter personligt, solidarisk og ubegrænset for al gæld – forfalden, uforfalden og omtvistet – som bestod, da erklæringen blev afgivet (§ 216, stk. 4). Metoden bør kun anvendes, når selskabet er "tømt", alle kontrakter er afviklet, og der ikke er usikre forpligtelser (fx garantier, reklamationer, skattesager).
{% endif %}

## Rådgivers tjekliste
- [ ] Selskabet er solvent (ellers rekonstruktion/konkurs – likvidation forudsætter fuld dækning af kreditorerne).
- [ ] Eventuelle offentlige tilskud, leasing, lejekontrakter, ansættelser og forsikringer opsagt/afviklet.
{% if branche.byggeri or branche.igangvaerende_arbejder %}- [ ] Mangelsansvar, garantistillelser og sikkerhedsstillelse over for bygherrer afklaret (forpligtelser kan række ud over proklamafristen).
{% endif %}{% if branche.ejendom %}- [ ] Ejendomme afhændet eller udloddet; genvundne afskrivninger og ejendomsavance opgjort; tinglysning af ejerskifte.
{% endif %}{% if branche.lager %}- [ ] Varelager realiseret eller udloddet til handelsværdi.
{% endif %}- [ ] Udlodning i andre værdier end kontanter: handelsværdi dokumenteret.
- [ ] **Skat for kapitalejerne:** Likvidationsprovenu udloddet i det kalenderår, hvor selskabet endeligt opløses, beskattes som afståelse efter aktieavancebeskatningsloven (ligningslovens § 16 A, stk. 3, nr. 2); udlodninger i tidligere år er udbytte. Personer: aktieindkomst (27/42 %). Selskaber: skattefrit ved datterselskabs-/koncernselskabsaktier.
- [ ] Forventet provenu: {{ felt.forventet_provenu }} kr.; skatteberegning udarbejdet for hver kapitalejer.
- [ ] Ejer- og ledelsesregistre og reelle ejere ajourført frem til slettelsen.
- [ ] Afmelding af digitalt bogføringssystem først efter opbevaringspligtens tilrettelæggelse (bogføringsloven, 5 år).

{{ kunde.by }}, {{ felt.gf_dato }}

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
{% if felt.metode == "Likvidation ved likvidator" %}{{ felt.dirigent }}, dirigent{% else %}Samtlige kapitalejere{% endif %}
