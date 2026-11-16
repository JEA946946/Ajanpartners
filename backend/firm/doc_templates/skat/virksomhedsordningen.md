---
{
  "title": "Virksomhedsordningen (VSO) – opgørelse og tjekliste",
  "description": "Arbejdspapir for virksomhedsskatteordningen: indskudskonto, kapitalafkastgrundlag, kapitalafkast (2 % i 2026), mellemregningskonto, hæverækkefølgen, opsparet overskud og virksomhedsskat (22 %), rentekorrektion og kontrolpunkter.",
  "kind": "arbejdspapir",
  "references": ["Virksomhedsskatteloven §§ 1-22 b", "VSL § 3 (indskudskonto)", "VSL § 4 a (mellemregningskonto)", "VSL § 5 (hæverækkefølge)", "VSL §§ 7-9 (kapitalafkast, -grundlag og -sats)", "VSL § 10 (opsparet overskud og virksomhedsskat)", "VSL § 11 (rentekorrektion)", "SKM2026.414.SKTST (kapitalafkastsats 2026)", "Den juridiske vejledning C.C.5.2"],
  "legal_forms": ["enk", "is", "pmv"],
  "industry_aware": true,
  "fields": [
    {"name": "ejer", "label": "Virksomhedsejer (navn)", "type": "text"},
    {"name": "kapitalafkastsats", "label": "Kapitalafkastsats (%)", "type": "text", "default": "2"},
    {"name": "virksomhedsskat", "label": "Virksomhedsskat (%)", "type": "text", "default": "22"},
    {"name": "indskud_primo", "label": "Indskudskonto primo (kr.)", "type": "number"},
    {"name": "kag_primo", "label": "Kapitalafkastgrundlag primo (kr.)", "type": "number"},
    {"name": "kag_ultimo", "label": "Kapitalafkastgrundlag ultimo (kr.)", "type": "number"},
    {"name": "resultat", "label": "Skattemæssigt resultat af virksomheden (kr.)", "type": "text", "default": "{{ regnskab.resultat }}"},
    {"name": "opsparet_primo", "label": "Opsparet overskud primo inkl. virksomhedsskat (kr.)", "type": "number", "default": "0"},
    {"name": "haevninger", "label": "Samlede overførsler til privat i året (kr.)", "type": "number"},
    {"name": "foerste_aar", "label": "Første år i virksomhedsordningen", "type": "checkbox"},
    {"name": "privat_gaeld_ind", "label": "Der er indskudt eller trukket gæld/aktiver i året", "type": "checkbox"}
  ]
}
---
# Virksomhedsordningen {{ regnskab.aar }}

**Ejer:** {{ felt.ejer }} · **Virksomhed:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}
**Udarbejdet af:** {{ medarbejder.navn }}, {{ dato.idag }}

Satser {{ regnskab.aar }}: kapitalafkastsats **{{ felt.kapitalafkastsats }} %** (2026: 2 %, uændret fra 2025, VSL § 9, stk. 1; SKM2026.414.SKTST) · virksomhedsskat **{{ felt.virksomhedsskat }} %** (2026: 22 %, VSL § 10, stk. 2).

## 1. Betingelser
- [ ] Der drives selvstændig erhvervsvirksomhed (ikke lønmodtagerlignende eller hobby).
- [ ] Der føres et regnskab, der opfylder bogføringslovens krav, og hvor virksomhedens og privatøkonomiens poster er adskilt (VSL § 2).
- [ ] Ordningen er valgt i oplysningsskemaet rettidigt (kan vælges år for år).
- [ ] Ved flere virksomheder: alle virksomheder skal behandles under ét i ordningen.
{% if kunde.selskabsform_kode == "is" %}- [ ] I/S: ordningen vælges af hver interessent for dennes andel; hver interessent har egen indskudskonto og eget opsparet overskud.
{% endif %}

{% if felt.foerste_aar %}
## 2. Indskudskonto ved indtræden (VSL § 3)
| | Kr. |
|---|---|
| Aktiver indskudt (handelsværdi; ejendomme til ejendomsværdi + evt. tillæg/fradrag, driftsmidler til skattemæssig nedskreven værdi) | |
| ÷ Gæld overført til virksomheden | |
| **Indskudskonto** (kan blive negativ; en negativ saldo er udtryk for privat gæld og udløser rentekorrektion, VSL § 11, stk. 1) | |

- [ ] Ikke-erhvervsmæssige aktiver (privat bil, privatbolig undtagen erhvervsandel, værdipapirer) holdes udenfor.
- [ ] Gæld, der ikke vedrører virksomheden: vurdér behandlingen efter den udvidede hæverækkefølge (Den juridiske vejledning C.C.5.2.7.3).
{% else %}
## 2. Indskudskonto
| | Kr. |
|---|---|
| Indskudskonto primo | {{ felt.indskud_primo }} |
| Årets indskud (efter hæverækkefølgen) | |
| Årets hævninger fra indskudskonto (sidst i hæverækkefølgen) | |
| **Indskudskonto ultimo** | |
{% endif %}
{% if felt.privat_gaeld_ind %}- [ ] **Bemærk:** Indskud og hævninger af gæld/aktiver i året skal behandles efter VSL §§ 3 og 5 (se Den juridiske vejledning C.C.5.2.5 og C.C.5.2.7.3 om overførsel af gæld). Både hævning og indskud på indskudskontoen i samme år udløser rentekorrektion (VSL § 11, stk. 2).
{% endif %}

## 3. Kapitalafkastgrundlag (VSL § 8)
| | Primo | Ultimo |
|---|---|---|
| Virksomhedens aktiver (skattemæssige værdier; ejendomme til ejendomsværdi m.v.) | | |
| ÷ Virksomhedens gæld | | |
| ÷ Mellemregningskonto og beløb hensat til senere hævning | | |
| **Kapitalafkastgrundlag** | {{ felt.kag_primo }} | {{ felt.kag_ultimo }} |

Kapitalafkast = kapitalafkastgrundlag ved indkomstårets begyndelse × {{ felt.kapitalafkastsats }} % (VSL § 7). Er grundlaget negativt, sættes kapitalafkastet til 0 kr. Kapitalafkastet kan ikke overstige årets skattepligtige overskud (efter eventuel overførsel til medarbejdende ægtefælle), jf. Den juridiske vejledning C.C.5.2.9.2.

## 4. Fordeling af årets resultat
| | Kr. |
|---|---|
| Skattemæssigt resultat før renter | {{ felt.resultat }} |
| ÷ Kapitalafkast (kapitalindkomst) | |
| ± Rentekorrektion (VSL § 11 – hvis indskudskontoen primo eller ultimo er negativ, eller der i samme år er både hævet og indskudt på indskudskontoen; rentekorrektionssats 5 % i 2026, VSL § 9 a) | |
| = Resterende overskud | |
| Heraf overført til personlig indkomst (hævet) | |
| Heraf opsparet i virksomheden (opsparet overskud inkl. virksomhedsskat) | |
| Virksomhedsskat {{ felt.virksomhedsskat }} % af opsparet overskud | |

## 5. Hæverækkefølgen (VSL § 5)
Samlede overførsler til privat i året: {{ felt.haevninger }} kr. Hævninger anses for at ske i denne rækkefølge:

1. **Beløb hensat til senere hævning** fra sidste år – først kapitalafkast (VSL § 7), dernæst resterende overskud (VSL § 10, stk. 1).
2. **Årets overskud** – først årets kapitalafkast (og kapitalafkast beskattet som personlig indkomst efter VSL § 23 a), dernæst årets resterende overskud.
3. **Opsparet overskud** fra tidligere år (inkl. godskrevet virksomhedsskat; den betalte virksomhedsskat modregnes i ejerens personlige skat).
4. **Indskudskonto.**

Overførsler til betaling af virksomhedsskat holdes uden for hæverækkefølgen (§ 5, stk. 3), og rentekorrektion indgår ikke (§ 5, stk. 2). Hæves der ud over indskudskontoen, anses det som et privat lån i virksomheden og udløser rentekorrektion (VSL § 11, stk. 1).

| Trin | Saldo til rådighed | Hævet | Rest |
|---|---|---|---|
| 1. Hensat til senere hævning | | | |
| 2a. Årets kapitalafkast | | | |
| 2b. Årets resterende overskud | | | |
| 3. Opsparet overskud | {{ felt.opsparet_primo }} | | |
| 4. Indskudskonto | {{ felt.indskud_primo }} | | |

## 6. Mellemregningskonto (VSL § 4 a)
- [ ] Mellemregningskontoen er uforrentet og må på intet tidspunkt være negativ; ved negativ saldo udlignes den ved en overførsel i hæverækkefølgen.
- [ ] Beløb på mellemregningskontoen indgår ikke i kapitalafkastgrundlaget.
- [ ] Overførsler mellem virksomhed og privatøkonomi i året er bogført via mellemregningskontoen.

## 7. Kontrolpunkter
- [ ] Private udgifter afholdt af virksomheden er behandlet som hævninger (overført i hæverækkefølgen, VSL § 5); erhvervsudgifter betalt privat er behandlet som indskud.
- [ ] Privat andel af bil, telefon, bolig og elforbrug er korrekt opgjort.
- [ ] Blandede aktiver (fx ejendom med privat beboelse) er korrekt opdelt.
- [ ] Hensættelse til senere hævning er foretaget inden fristen for oplysningsskemaet.
- [ ] Ved ophør eller udtræden af ordningen: behandlingen af opsparet overskud og virksomhedsskat vurderes efter VSL (Den juridiske vejledning C.C.5.2.13); vurdér overgang til kapitalafkastordningen eller omdannelse til selskab (skattefri virksomhedsomdannelse).
{% if branche.ejendom %}- [ ] Udlejningsejendom: kontrollér at alle udlejningsejendomme er medtaget, og at ejendomsværdier anvendes korrekt i kapitalafkastgrundlaget.
{% endif %}{% if branche.landbrug %}- [ ] Landbrug: medregn besætning, maskiner og ejendom korrekt; vurdér konjunkturudsving og opsparing.
{% endif %}- [ ] Simulering af hævninger kontra topskattegrænser (mellemskat 641.200 kr., topskat 777.900 kr. efter AM-bidrag i 2026) er drøftet med ejeren.

Konklusion og rådgivning: \_\_\_\_\_\_
