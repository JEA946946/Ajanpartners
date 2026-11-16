---
{
  "title": "Selskabsskatteberegning (arbejdspapir)",
  "description": "Opgørelse af skattepligtig indkomst fra regnskabsmæssigt resultat: ikke-fradragsberettigede poster, repræsentation, afskrivningsforskelle, skattefri udbytter/avancer, rentefradragsbegrænsning, underskudsfremførsel, sambeskatning og acontoskat.",
  "kind": "arbejdspapir",
  "references": ["Selskabsskatteloven §§ 11, 11 B, 11 C, 12, 12 D, 13, 17 og 31", "Ligningsloven § 8, stk. 4 (repræsentation)", "Afskrivningsloven", "Aktieavancebeskatningsloven § 8", "Statsskatteloven § 6, stk. 1, litra a", "Skattekontrolloven § 2"],
  "legal_forms": ["aps", "as", "holding", "ivs", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "resultat_foer_skat", "label": "Resultat før skat iflg. årsregnskab (kr.)", "type": "number"},
    {"name": "skattesats", "label": "Selskabsskattesats (%)", "type": "text", "default": "22"},
    {"name": "repraesentation", "label": "Repræsentation bogført (kr.)", "type": "number"},
    {"name": "regn_afskr", "label": "Regnskabsmæssige af- og nedskrivninger (kr.)", "type": "number"},
    {"name": "skat_afskr", "label": "Skattemæssige afskrivninger (kr.)", "type": "number"},
    {"name": "nettofinans", "label": "Nettofinansieringsudgifter (kr.)", "type": "number"},
    {"name": "fremfoert_underskud", "label": "Fremførbart underskud primo (kr.)", "type": "number", "default": "0"},
    {"name": "grundbeloeb_underskud", "label": "Grundbeløb for fuld underskudsfremførsel (SEL § 12, stk. 2) for indkomståret (kr.)", "type": "text", "default": "21.830.700 (2026 – kontrollér; 2025: 20.829.000)"},
    {"name": "acontoskat", "label": "Betalt acontoskat (kr.)", "type": "number", "default": "0"},
    {"name": "sambeskattet", "label": "Selskabet indgår i sambeskatning", "type": "checkbox"},
    {"name": "administrationsselskab", "label": "Administrationsselskab (navn/CVR)", "type": "text"}
  ]
}
---
# Selskabsskatteberegning {{ regnskab.aar }}

**Kunde:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }} · **Indkomstår:** {{ regnskab.start }} – {{ regnskab.slut }}
**Udarbejdet af:** {{ medarbejder.navn }}, {{ dato.idag }} · **Gennemgået af:** \_\_\_\_\_\_

Selskabsskattesats: **{{ felt.skattesats }} %** (SEL § 17, stk. 1).{% if branche.finans %} **OBS:** Finansielle selskaber (pengeinstitutter, realkredit, forsikring m.fl.) beskattes med en forhøjet sats efter SEL § 17 (26 % fra indkomståret 2024 – kontrollér, om selskabet er omfattet; almindelige holding- og investeringsselskaber er ikke omfattet).{% endif %} Den varslede nedsættelse af selskabsskatten (22 % → 19 %) er ikke vedtaget pr. {{ dato.idag }} og påvirker ikke indkomståret {{ regnskab.aar }}.

## 1. Fra regnskabsmæssigt resultat til skattepligtig indkomst

| Nr. | Post | Kr. | Ref./bilag |
|---|---|---|---|
| 1 | Resultat før skat iflg. årsregnskab | {{ felt.resultat_foer_skat }} | |
| | **Tillæg – ikke-fradragsberettigede omkostninger** | | |
| 2 | Regnskabsmæssige af- og nedskrivninger | {{ felt.regn_afskr }} | |
| 3 | 75 % af repræsentation ({{ felt.repraesentation }} kr. bogført; kun 25 % fradrag, LL § 8, stk. 4) | | |
| 4 | Bøder, afgifter til det offentlige med strafkarakter, parkeringsafgifter | | |
| 5 | Renter og tillæg vedr. selskabsskat (restskattetillæg, rentetillæg) | | |
| 6 | Ikke-fradragsberettigede gaver, sponsorater uden reklameværdi, kontingenter til politiske formål | | |
| 7 | Etablerings-/udvidelsesudgifter og ikke-afskrivningsberettigede anskaffelser (fx kunst, grunde) | | |
| 8 | Regnskabsmæssigt tab på kapitalandele/datterselskaber | | |
| 9 | Private udgifter afholdt af selskabet (vurdér LL § 16 E/løn/udbytte) | | |
| 10 | Hensatte forpligtelser uden skattemæssig fradrag (garantier, omstrukturering) – regulering | | |
| 11 | Ikke-realiserede værdireguleringer (investeringsejendomme, dagsværdi) | | |
| | **Fradrag – skattefri indtægter og ekstra fradrag** | | |
| 12 | Skattemæssige afskrivninger (jf. afskrivningsark) | -{{ felt.skat_afskr }} | |
| 13 | Skattefrit udbytte af datterselskabs-/koncernselskabsaktier (SEL § 13, stk. 1, nr. 2) | | |
| 14 | Skattefri avance på datterselskabs-/koncernselskabsaktier og skattefri porteføljeaktier (ABL § 8) | | |
| 15 | Resultat af kapitalandele i tilknyttede/associerede virksomheder (indre værdi) | | |
| 16 | Regulering af skattemæssig avance på driftsmidler/ejendomme (genvundne afskrivninger, ejendomsavance) | | |
| 17 | Forhøjet fradrag for forsknings- og udviklingsomkostninger (LL § 8 B – kontrollér årets procent) | | |
| 18 | Skattekredit for FoU-underskud (LL § 8 X) – noteres særskilt | | |
| | **Rentefradragsbegrænsning** (afsnit 3) | | |
| 19 | Tillæg efter SEL § 11 / § 11 B / § 11 C | | |
| | **Skattepligtig indkomst før underskudsfremførsel** | | |
| 20 | Fremført underskud (afsnit 4) | | |
| | **Skattepligtig indkomst** | | |
| | Selskabsskat {{ felt.skattesats }} % | | |
| | Acontoskat betalt | -{{ felt.acontoskat }} | |
| | **Restskat / overskydende skat** (ekskl. tillæg/godtgørelse) | | |

{% if branche.restauration or branche.hotel or branche.liberalt_erhverv %}*Branchebemærkning:* Repræsentation og personaleforplejning skal adskilles. Personalearrangementer og fortæring under rejser er fuldt fradragsberettigede; forretningsmæssig repræsentation over for kunder er kun 25 % fradragsberettiget (moms: 25 % fradrag for hotel- og restaurationsydelser, 0 % for øvrig repræsentation).
{% endif %}{% if branche.ejendom or branche.investeringsejendomme %}*Branchebemærkning:* Værdiregulering af investeringsejendomme indgår ikke i skattepligtig indkomst; boligudlejningsejendomme og grunde er ikke afskrivningsberettigede (AL § 14, stk. 2). Ejendomsavance opgøres efter ejendomsavancebeskatningsloven ved salg.
{% endif %}{% if branche.holding %}*Branchebemærkning:* Holdingselskab – kontrollér ejerandel (≥ 10 % for datterselskabsaktier) og koncernforbindelse for skattefrihed af udbytte og avance; vurdér værdipapirer efter lagerprincippet (porteføljeaktier, investeringsforeninger) og CFC-reglerne (SEL § 32).
{% endif %}{% if branche.byggeri or branche.igangvaerende_arbejder %}*Branchebemærkning:* Igangværende arbejder for fremmed regning beskattes efter produktionsprincippet; kontrollér at skattemæssig og regnskabsmæssig indregning er ens, og at hensættelser til tab på kontrakter er skattemæssigt korrekte.
{% endif %}{% if branche.lager %}*Branchebemærkning:* Varelager opgøres skattemæssigt efter varelagerloven (kostpris/FIFO, ukurans nedskrivning kun ved dokumenteret lavere dagsværdi).
{% endif %}

## 2. Afskrivningsforskelle
| | Regnskab | Skat | Forskel |
|---|---|---|---|
| Driftsmidler (saldo) | | | |
| Bygninger og installationer | | | |
| Goodwill og immaterielle aktiver | | | |
| Småaktiver / straksafskrivninger | | | |
| **I alt** | {{ felt.regn_afskr }} | {{ felt.skat_afskr }} | |

Forskellene overføres til opgørelsen af udskudt skat.

## 3. Rentefradragsbegrænsning
Nettofinansieringsudgifter: {{ felt.nettofinans }} kr.

| Regel | Test | Konklusion |
|---|---|---|
| Tynd kapitalisering (SEL § 11) | Kontrolleret gæld > 10 mio. kr. og gæld/egenkapital > 4:1 | |
| Renteloft / aktivtest (SEL § 11 B) | Nettofinansieringsudgifter > 21,3 mio. kr.; fradrag begrænses til standardrente (4,2 % for 2026) × skattemæssig værdi af visse aktiver | |
| EBITDA-regel (SEL § 11 C) | Nettofinansieringsudgifter > 22.313.400 kr. (bundgrænse); fradrag højst 30 % af skattemæssig EBITDA | |

For de fleste SMV'er er bundgrænserne ikke overskredet; dette dokumenteres ved at anføre nettofinansieringsudgifterne for selskabet{% if felt.sambeskattet %} og for sambeskatningskredsen samlet (grundbeløbene gælder for koncernen under ét){% endif %}.

## 4. Underskudsfremførsel (SEL § 12)
| | Kr. |
|---|---|
| Fremførbart underskud primo | {{ felt.fremfoert_underskud }} |
| Indkomst før underskud | |
| Fuld modregning op til grundbeløbet ({{ felt.grundbeloeb_underskud }}) | |
| Herudover modregning af højst 60 % af resterende indkomst | |
| Anvendt underskud | |
| **Fremførbart underskud ultimo** | |

- [ ] Kontrollér ejerskifte > 50 % (SEL § 12 D – passive aktiver) og gældseftergivelse/akkord (SEL § 12 A-12 B), der kan begrænse underskud.
- [ ] Underskud specificeret pr. indkomstår (ældste anvendes først). Bemærk det varslede forslag om en 17-årig grænse for underskudsfremførsel (ikke vedtaget pr. {{ dato.idag }}).

{% if felt.sambeskattet %}
## 5. Sambeskatning (SEL § 31)
- Administrationsselskab: {{ felt.administrationsselskab }}
- [ ] Alle danske koncernforbundne selskaber og faste driftssteder indgår (tvungen national sambeskatning).
- [ ] Selskabets skattepligtige indkomst indgår i den sambeskattede indkomst; underskud udnyttes inden for kredsen efter særunderskud/fællesunderskud-reglerne og ét fælles grundbeløb.
- [ ] Skattefordeling: selskaber med positiv indkomst betaler sambeskatningsbidrag til administrationsselskabet; selskaber med underskud modtager godtgørelse (fuld fordeling).
- [ ] Hæftelse: alle selskaber hæfter solidarisk for skat af sambeskattet indkomst, hvor ultimativt moderselskab hæfter fuldt, og øvrige hæfter subsidiært for egen andel (SEL § 31, stk. 6).
- [ ] Indkomstår, regnskabsår og ændringer i sambeskatningskredsen (indtræden/udtræden) kontrolleret.
{% endif %}

## 6. Acontoskat og frister
- [ ] Ordinær acontoskat forfalder 20. marts og 20. november i indkomståret (SEL § 29 A). Frivillig acontoskat kan indbetales til 20. november; supplerende frivillig indbetaling senest 1. februar efter indkomstårets udløb mod lavere tillæg.
- [ ] Restskat forfalder 20. november i året efter indkomståret med procenttillæg; overskydende skat udbetales med godtgørelse.
- [ ] Selvangivelse (oplysningsskema) for selskaber skal indgives senest 6 måneder efter indkomstårets udløb (for indkomstår, der slutter 1. februar-31. marts: senest 1. august) – skattekontrolloven § 2.
- [ ] Transfer pricing-dokumentation og oplysningsskema for kontrollerede transaktioner (SKL § 37 og § 38), hvis relevant.

## 7. Afstemning
| | Kr. |
|---|---|
| Aktuel skat iflg. beregning | |
| Regulering af skat for tidligere år | |
| Ændring i udskudt skat | |
| **Skat af årets resultat iflg. resultatopgørelsen** | |
| Effektiv skatteprocent | |

Konklusion: \_\_\_\_\_\_
