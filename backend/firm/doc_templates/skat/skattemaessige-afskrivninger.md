---
{
  "title": "Skattemæssige afskrivninger (arbejdspapir)",
  "description": "Opgørelse af saldoafskrivning på driftsmidler (25 %), småaktiver (36.000 kr. i 2026), småsaldo (16.900 kr.), bygninger og installationer (3 % / 4 % for erhvervet før 2023), straksfradrag for forbedringer (5 %), goodwill og rettigheder (1/7), særsaldi og genvundne afskrivninger.",
  "kind": "arbejdspapir",
  "references": ["Afskrivningsloven (LBK nr. 1222 af 13. oktober 2025 med senere ændringer) §§ 5, 5 B, 5 C, 5 D, 6, 11, 14-21 og 40", "Ligningsloven § 8 B", "Ejendomsavancebeskatningsloven"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "saldo_primo", "label": "Saldo driftsmidler primo (kr.)", "type": "number"},
    {"name": "tilgang", "label": "Anskaffelser i året (kr.)", "type": "number", "default": "0"},
    {"name": "afgang", "label": "Salgssummer i året (kr.)", "type": "number", "default": "0"},
    {"name": "sats", "label": "Valgt saldoafskrivning (%), max 25", "type": "number", "default": "25"},
    {"name": "smaaaktiv_graense", "label": "Småaktivgrænse for indkomståret (kr.)", "type": "text", "default": "36.000 (2026); 34.400 (2025)"},
    {"name": "smaasaldo_graense", "label": "Småsaldogrænse for indkomståret (kr.)", "type": "text", "default": "16.900 (2026); 16.200 (2025)"},
    {"name": "privat_andel", "label": "Driftsmidler med blandet benyttelse (særskilt afskrivning, AL § 11)", "type": "checkbox"}
  ]
}
---
# Skattemæssige afskrivninger {{ regnskab.aar }}

**Kunde:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}
**Udarbejdet af:** {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Driftsmidler – fælles saldo (AL § 5)
| | Kr. |
|---|---|
| Saldo primo | {{ felt.saldo_primo }} |
| + Anskaffelser i året | {{ felt.tilgang }} |
| ÷ Salgssummer for solgte driftsmidler | -{{ felt.afgang }} |
| = Afskrivningsgrundlag | |
| ÷ Afskrivning {{ felt.sats }} % (højst 25 %) | |
| **Saldo ultimo** | |

- Er saldoen (før afskrivning) negativ, indtægtsføres det negative beløb (genvundne afskrivninger).
- **Småsaldo:** Er afskrivningsgrundlaget højst {{ felt.smaasaldo_graense }} kr. (grundbeløb 12.300 kr. i 2010-niveau), kan hele saldoen fradrages.
- Driftsmidler i samme indkomstår, der er anskaffet og solgt, behandles efter saldometoden.
{% if felt.privat_andel %}- **Blandet benyttelse (AL § 11):** Driftsmidler, der også benyttes privat (fx bil i personligt drevet virksomhed), afskrives særskilt for hvert driftsmiddel med indtil 25 % af den uafskrevne saldo; kun den erhvervsmæssige andel fradrages, og fortjeneste/tab ved salg opgøres særskilt.
{% endif %}

## 2. Straksafskrivning (AL § 6)
| Type | Grænse/regel | Beløb |
|---|---|---|
| Småaktiver | Anskaffelsessum højst {{ felt.smaaaktiv_graense }} kr. ekskl. moms for momsregistrerede (grundbeløb 26.200 kr. i 2010-niveau). Samlesæt og aktiver, der skal fungere sammen, anses for ét. | |
| Kort levetid | Fysisk levealder højst 3 år | |
| Forsøg og forskning | Driftsmidler til FoU (ikke råstofefterforskning); fradrag med 114 % af anskaffelsessummen i 2026 og 116 % i 2027 (AL § 6, stk. 1, nr. 3) | |
| Software | Afskrives efter driftsmiddelreglerne (AL § 2); straksafskrivning kun som småaktiv eller kort levetid | |

## 3. Særlige saldi
- [ ] Driftsmidler med lang levetid (AL § 5 C – fx skibe ≥ 20 BT, fly, store energianlæg): højst 15 %; infrastrukturanlæg højst 7 %.
- [ ] Skibe (AL § 5 B): særskilt saldo, højst 12 %.
- [ ] Personbiler i virksomhed med privat anvendelse: særskilt afskrivning (§ 11).
{% if branche.transport %}- [ ] **Transport:** Lastbiler, busser og varebiler afskrives på den fælles saldo; taxi og vognmandskøretøjer med blandet brug vurderes særskilt.
{% endif %}{% if branche.landbrug %}- [ ] **Landbrug:** Landbrugsmaskiner på fælles saldo; driftsbygninger efter § 14; jordforbedringer og læhegn efter særregler.
{% endif %}

## 4. Bygninger og installationer (AL §§ 14-21)
Afskrivningsberettiget er bygninger anvendt til fremstilling, transport, hotel, butik, værksted, lager m.v. **Ikke** afskrivningsberettiget er bl.a. bygninger til beboelse og kontor/finansiel virksomhed (AL § 14, stk. 2) – bortset fra kontorbygninger, der er tilknyttet afskrivningsberettiget virksomhed.

| Bygning | Anskaffet | Afskrivningsgrundlag | Sats | Afskrivning | Nedskreven værdi |
|---|---|---|---|---|---|
| | Før 1.1.2023 | | 4 % | | |
| | Fra 1.1.2023 | | 3 % | | |

- Afskrivning sker lineært af anskaffelsessummen (AL § 17, stk. 1). Bygninger og installationer erhvervet fra og med 1. januar 2023 afskrives med højst **3 %**; erhvervet før med højst **4 %**.
- Forhøjet sats, hvis bygningen trods normal vedligeholdelse må antages at miste sin værdi inden 33 år (§ 17, stk. 2).
- **Straksfradrag for forbedringer (AL § 18, stk. 2):** Forbedringer kan fradrages straks, i det omfang årets vedligeholdelse + forbedring ikke overstiger 5 % af bygningens afskrivningsgrundlag (vedligeholdelse medregnes først). Øvrige forbedringer afskrives særskilt.
- **Genvundne afskrivninger (AL § 21):** Ved salg beskattes forskellen mellem salgssum og nedskreven værdi op til foretagne afskrivninger; resterende fortjeneste efter ejendomsavancebeskatningsloven.
{% if branche.ejendom or branche.investeringsejendomme %}- [ ] **Ejendomsselskab:** Boligudlejning er ikke afskrivningsberettiget. Erhvervsudlejning til afskrivningsberettiget brug kan afskrives; blandede ejendomme fordeles efter areal. Installationer (fx elevatorer, varmeanlæg) i ikke-afskrivningsberettigede bygninger kan afskrives efter § 15.
{% endif %}{% if branche.hotel or branche.restauration %}- [ ] **Hotel/restauration:** Hotelbygninger er afskrivningsberettigede; restaurationsinventar på fælles saldo.
{% endif %}

## 5. Immaterielle aktiver (AL § 40)
- Goodwill og andre erhvervede immaterielle rettigheder (§ 40): højst 1/7 årligt fra aftaleåret. Ikke goodwill erhvervet fra skattefri selskaber m.v.
- Erhvervet knowhow, patentret, varemærker, mønsterret m.v. (§ 40, stk. 2): højst 1/7 årligt; rettigheder med kortere beskyttelsesperiode over den resterende periode. (Den tidligere straksafskrivning efter § 41 er ophævet.)
- Konkurrenceklausuler og afløsning af agentur (§ 40, stk. 3): afskrives med 1/7 årligt hos yderen, dog fuldt fradrag hvis under 5 % af lønudgiften.
- Forsknings- og udviklingsomkostninger: fradrag efter LL § 8 B (evt. forhøjet fradrag – kontrollér årets procent).

## 6. Kontrol og afstemning
- [ ] Tilgang og afgang afstemt til anlægskartotek og bogføring; fakturaer for anskaffelser > småaktivgrænsen gennemgået.
- [ ] Driftsmidler anskaffet til erstatning af solgte afskrives i anskaffelsesåret (ingen periodisering).
- [ ] Aktiver taget i brug efter udlejning/leasing vurderet (AL § 5 D for udlejningsdriftsmidler).
- [ ] Regnskabsmæssige og skattemæssige værdier overført til opgørelsen af udskudt skat.
