# Format for dokumentskabeloner (admin-portalen → Skabeloner)

Skabelonerne ligger som filer i `backend/firm/doc_templates/<kategori>/<slug>.md`. Én fil = én skabelon.
Filnavnet (uden .md) er skabelonens id; brug små bogstaver, tal og bindestreg (fx `opdragsbrev-revision.md`).

Kategorier (mapper):
| Mappe | Indhold |
|---|---|
| `opdrag` | Opdragsbreve, accept/fortsættelse af kunde, uafhængighed, tilbud, revisorskifte, opsigelse |
| `hvidvask` | Kundekendskab (KYC), risikovurdering, PEP, reelle ejere, løbende overvågning, intern underretning |
| `erklaeringer` | Påtegninger og erklæringer (revision, udvidet gennemgang, review, opstilling, aftalte arbejdshandlinger, selskabsretlige erklæringer, tilskud, omsætning) |
| `ledelse` | Ledelseserklæringer, revisionsprotokollat, ISA 260/265-breve, management letter |
| `selskabsret` | Generalforsamling, bestyrelse, fravalg af revision, udbytte, kapitalforhøjelse/-nedsættelse, ejerbog, likvidation, kapitalejerlån |
| `aarsafslutning` | Materialelister, tjeklister, planlægning, væsentlighed, risikovurdering, bekræftelser (bank, debitor/kreditor, advokat), going concern, efterfølgende begivenheder, nærtstående parter |
| `skat` | Selskabsskat, personlig skat, virksomhedsordning, fuldmagt, udskudt skat |
| `kundebreve` | Følgebreve, påmindelser, rykkere, velkomst, opsigelse, løn/HR (ansættelsesbevis) |

## Filformat
Filen starter med en JSON-blok mellem to linjer med `---`, derefter selve teksten i Markdown med Django-skabelonsyntaks.

```
---
{
  "title": "Opdragsbrev – revision af årsregnskab",
  "description": "Til kapitalselskaber med revisionspligt. Følger ISA 210 og revisorlovens krav.",
  "kind": "brev",
  "references": ["ISA 210", "Revisorloven § 16", "Årsregnskabsloven § 135"],
  "legal_forms": ["aps", "as"],
  "industry_aware": true,
  "fields": [
    {"name": "regnskabsaar", "label": "Regnskabsår", "type": "text", "default": "{{ regnskab.aar }}"},
    {"name": "honorar", "label": "Honorar (kr. ekskl. moms)", "type": "number"},
    {"name": "fakturering", "label": "Fakturering", "type": "select", "options": ["Løbende", "Ved afslutning", "Aconto månedligt"], "default": "Løbende"}
  ]
}
---
# Opdragsbrev
...
```

- `kind`: `brev` (sendes til kunden), `erklaering` (underskrives af revisor), `beslutning` (kundens dokument, fx GF-referat), `arbejdspapir` (internt), `tjekliste` (internt, med afkrydsning).
- `legal_forms`: hvilke selskabsformer skabelonen er relevant for (tom liste = alle). Koder: `aps`, `as`, `ivs`, `enk`, `is`, `pmv`, `fmba`, `forening`, `holding`, `andet`.
- `industry_aware`: true hvis teksten ændrer sig efter kundens branche.
- `fields`: ekstra oplysninger brugeren udfylder. `type`: `text`, `textarea`, `number`, `date`, `select` (med `options`), `checkbox`. `default` må bruge flettefelter. Felterne bruges i teksten som `{{ felt.<name> }}`.
- Felter, der allerede findes i flettefelterne nedenfor, skal IKKE gentages som `fields`.

## Flettefelter (indsættes automatisk når brugeren vælger en kunde)
| Felt | Eksempel |
|---|---|
| `{{ firma.navn }}`, `{{ firma.cvr }}`, `{{ firma.adresse }}` (samlet: vej, postnr. og by), `{{ firma.vej }}`, `{{ firma.postnr }}`, `{{ firma.by }}`, `{{ firma.email }}`, `{{ firma.telefon }}`, `{{ firma.hjemmeside }}` | Ajan Partners, 46922514 … |
| `{{ kunde.navn }}`, `{{ kunde.cvr }}`, `{{ kunde.adresse }}`, `{{ kunde.postnr }}`, `{{ kunde.by }}`, `{{ kunde.email }}`, `{{ kunde.telefon }}` | |
| `{{ kunde.selskabsform }}` (tekst, fx "ApS"), `{{ kunde.selskabsform_kode }}` (fx `aps`) | |
| `{{ kunde.er_kapitalselskab }}` (ApS, A/S, IVS, holding), `{{ kunde.er_personlig }}` (enk, I/S, pmv) | bool |
| `{{ kunde.ledelsesorgan }}` | "direktionen" (ApS) / "bestyrelsen og direktionen" (A/S) / "ledelsen" |
| `{{ kunde.kapitalejere }}` | "anpartshaverne" (ApS) / "aktionærerne" (A/S) / "kapitalejerne" |
| `{{ kunde.branchekode }}` (fx 56.10.10), `{{ kunde.branchetekst }}` | |
| `{{ kunde.regnskabsklasse }}` (B, C …), `{{ kunde.momsperiode }}` (tekst), `{{ kunde.ansvarlig }}` (medarbejder), `{{ kunde.aftalereference }}` | |
| `{{ regnskab.aar }}` (fx "2026" eller "2025/26"), `{{ regnskab.start }}`, `{{ regnskab.slut }}` (datoer, fx 31. december 2026), `{{ regnskab.frist_aarsrapport }}` | |
| `{{ regnskab.omsaetning }}`, `{{ regnskab.resultat }}`, `{{ regnskab.balancesum }}`, `{{ regnskab.egenkapital }}` | formaterede beløb fra bogføringen (kan være tomme) |
| `{{ medarbejder.navn }}`, `{{ medarbejder.titel }}` | den der danner dokumentet |
| `{{ dato.idag }}` (16. november 2026), `{{ dato.aar }}` | |
| `{{ branche.<gruppe> }}` | bool, se grupper nedenfor |
| `{{ branche.hvidvask_risiko }}` | "høj", "forhøjet" eller "normal" |
| `{{ branche.navn }}` | gruppe-navn i tekst, fx "restauration" |

Brug Django-syntaks: `{% if branche.byggeri %} … {% endif %}`, `{% if kunde.selskabsform_kode == "as" %}`, `{% if not kunde.er_kapitalselskab %}`. Ingen andre tags end `if/elif/else/endif`, `for` og filtre `default`. Tomme felter vises som "[…]" i dokumentet, så brugeren kan se, hvad der mangler – skriv derfor ikke selv pladsholdere som "[indsæt]" for flettefelter.

### Branchegrupper (`branche.<gruppe>`, ud fra DB25-koden)
`landbrug` (01–03), `fremstilling` (10–33), `forsyning` (35–39), `byggeri` (41–43), `engros` (46), `detail` (47), `bilhandel` (handel med/reparation af motorkøretøjer), `transport` (49–53), `hotel` (55), `restauration` (56), `medier` (58–60), `it` (61–63), `finans` (64–66), `ejendom` (68), `holding` (64.2x holdingselskaber og 70.10 hovedsæder), `liberalt_erhverv` (69–75), `udlejning_service` (77–82), `rengoering` (81.2x), `vikar` (78), `undervisning` (85), `sundhed` (86–88), `kultur_fritid` (90–93), `spil` (92), `forening` (94), `personlig_service` (95–96: frisør, skønhed, vaskeri …), `kontantintensiv` (detail, restauration, frisør, kiosker, taxa, bilhandel …), `momsfritaget` (sundhed, undervisning, finans, udlejning af fast ejendom …), `lager` (varelager typisk væsentligt: fremstilling, engros, detail, bilhandel, landbrug), `igangvaerende_arbejder` (byggeri, liberale erhverv, it, konsulenter), `investeringsejendomme` (ejendom).

## Indhold – krav
- Skriv som en erfaren senior revisor i et dansk revisionsfirma: præcist, sagligt, på dansk, med korrekte henvisninger til gældende regler (revisorloven, erklæringsbekendtgørelsen, ISA/ISRE/ISRS/ISAE som oversat af FSR – danske revisorer, årsregnskabsloven, selskabsloven, bogføringsloven, hvidvaskloven, skattelovgivningen).
- Brug konkrete standardformuleringer, hvor de findes (fx FSR's eksempler på påtegninger, Erhvervsstyrelsens vejledninger), men skriv dem selv med egne ord, hvor ordlyden er ophavsretligt beskyttet. Lovtekst må citeres.
- Brug branchegrupperne, hvor branchen reelt ændrer indholdet: risici, særlige regnskabsposter, materialeliste, hvidvaskrisiko, momsforhold, særlige skatteregler.
- Brug selskabsform hvor det betyder noget (ApS vs. A/S: organer, revisionsudvalg, kapitalkrav, betegnelser).
- Afslut breve og erklæringer med sted/dato og underskriftsfelt (`{{ firma.navn }}` · `{{ medarbejder.navn }}`, statsautoriseret/registreret revisor angives som felt hvor relevant, fx felt `revisor_titel`).
- Interne arbejdspapirer og tjeklister: brug Markdown-tabeller eller `- [ ]` punkter.
- Hver skabelon skal være brugbar som den er, ikke en skitse.
