---
{
  "title": "Gennemgang af egenkapital og resultatdisponering",
  "description": "Arbejdspapir til egenkapitalopgørelse, bundne og frie reserver, udbytteforslag, kapitaltab og resultatdisponering. Tilpasses selskabsform (kapitalselskab/personlig virksomhed).",
  "kind": "arbejdspapir",
  "references": ["Årsregnskabsloven §§ 31, 41, 43 a, 83", "Selskabsloven §§ 4, 115, 119, 179-183, 194", "Ligningsloven § 16 A (udbytte)", "Kildeskatteloven § 65 (udbytteskat)"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "selskabskapital", "label": "Registreret selskabskapital (kr.)", "type": "number"},
    {"name": "foreslaaet_udbytte", "label": "Foreslået udbytte (kr.)", "type": "number"},
    {"name": "ekstraordinaert_udbytte", "label": "Ekstraordinært udbytte udloddet i året (kr.)", "type": "number"},
    {"name": "bemaerkninger", "label": "Bemærkninger", "type": "textarea"}
  ]
}
---
# Egenkapital og resultatdisponering – {{ kunde.navn }}, {{ regnskab.aar }}

Udarbejdet af: {{ medarbejder.navn }}, {{ dato.idag }}

Årets resultat: **{{ regnskab.resultat }}** · Egenkapital ultimo: **{{ regnskab.egenkapital }}**

{% if kunde.er_kapitalselskab %}
## 1. Egenkapitalopgørelse
| | Selskabskapital | Overkurs ved emission | Reserve for nettoopskrivning efter indre værdis metode | Reserve for udviklingsomkostninger | Andre bundne reserver | Overført resultat | Foreslået udbytte | I alt |
|---|---|---|---|---|---|---|---|---|
| Saldo primo | | | | | | | | |
| Kapitalforhøjelse/-nedsættelse | | | | | | | | |
| Udbetalt udbytte | | | | | | | | |
| Ekstraordinært udbytte | | | | | | | | |
| Årets resultat (disponering) | | | | | | | | |
| Overførsel til/fra bundne reserver | | | | | | | | |
| **Saldo ultimo** | | | | | | | | |

## 2. Kontroller
- [ ] Selskabskapital ({{ felt.selskabskapital }} kr.) stemmer til CVR; ændringer i året er registreret i Erhvervsstyrelsen
- [ ] Primo stemmer til sidste års godkendte årsrapport, og udbytte udbetalt i året svarer til GF-beslutning
- [ ] Ekstraordinært udbytte ({{ felt.ekstraordinaert_udbytte }} kr.) er besluttet med grundlag i seneste årsrapport eller mellembalance (SL §§ 182-183) og var forsvarligt (SL § 179, stk. 2)
- [ ] Udbytteskat (som hovedregel 27 %) er indeholdt, angivet og betalt senest den 10. i måneden efter den måned, hvor udbyttet er vedtaget (for udbytte vedtaget i december: 17. januar) (kildeskatteloven § 65); udbytte til moderselskab vurderet (skattefrit datterselskabsudbytte)
{% if branche.holding %}- [ ] Reserve for nettoopskrivning efter indre værdis metode (ÅRL § 43 a) er opgjort pr. kapitalandel; udbytte fra datterselskaber er modregnet i reserven
{% endif %}- [ ] Reserve for udviklingsomkostninger svarer til aktiverede udviklingsomkostninger (ÅRL § 83, stk. 2, for klasse C; for klasse B jf. Erhvervsstyrelsens vejledning om indregning af immaterielle anlægsaktiver)
{% if branche.ejendom %}- [ ] Dagsværdireguleringer af investeringsejendomme: vurder binding i reserve (ÅRL § 41) og udskudt skat
{% endif %}- [ ] Foreslået udbytte ({{ felt.foreslaaet_udbytte }} kr.) overstiger ikke de frie reserver og er forsvarligt under hensyn til selskabets økonomiske stilling (SL § 179, stk. 2, og § 180, stk. 2); vises som særlig post i egenkapitalen (ÅRL § 31, stk. 1)
- [ ] Ved udlodning i strid med reglerne: tilbagebetalingspligt (SL § 194)
- [ ] **Kapitaltab:** egenkapital under halvdelen af den tegnede kapital? Ledelsen skal senest 6 måneder efter konstateringen sikre, at der afholdes generalforsamling, hvor ledelsen redegør for selskabets økonomiske stilling og foreslår foranstaltninger (SL § 119). Omtales i ledelsesberetning og som usikkerhed om fortsat drift
- [ ] Minimumskapital (ApS 20.000 kr., A/S 400.000 kr.) er overholdt ved kapitalnedsættelse (SL § 4, stk. 2)

## 3. Forslag til resultatdisponering (ÅRL § 31)
| | Beløb |
|---|---|
| Foreslået udbytte for regnskabsåret | {{ felt.foreslaaet_udbytte }} |
| Ekstraordinært udbytte udloddet i året | {{ felt.ekstraordinaert_udbytte }} |
| Overført til reserve for nettoopskrivning/udvikling | |
| Overført resultat | |
| **I alt (= årets resultat)** | {{ regnskab.resultat }} |

- [ ] Disponeringen i årsrapporten svarer til ledelsens forslag og indarbejdes i GF-referat
{% else %}
## 1. Egenkapital i personlig virksomhed
| | Beløb |
|---|---|
| Egenkapital primo | |
| Årets resultat | {{ regnskab.resultat }} |
| Private hævninger | |
| Private andele (bil, telefon, bolig) | |
| Indskud | |
| Betalte personlige skatter | |
| **Egenkapital ultimo** | {{ regnskab.egenkapital }} |

## 2. Kontroller
- [ ] Private hævninger er specificeret og afstemt til bankkonti/mellemregning
- [ ] Private andele er opgjort efter Skattestyrelsens satser for indkomståret
- [ ] Ved virksomhedsordningen: opsparet overskud, kapitalafkastgrundlag, indskudskonto og mellemregningskonto er afstemt; hæverækkefølgen er overholdt (ingen negativ indskudskonto)
- [ ] Ved kapitalafkastordningen: kapitalafkastgrundlag opgjort
- [ ] Negativ egenkapital: vurder fortsat drift og ejers hæftelse
{% endif %}

## 4. Bemærkninger
{{ felt.bemaerkninger }}

Udført: ______________________  Gennemgået: ______________________
