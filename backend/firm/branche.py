"""Branchegrupper til dokumentskabeloner, ud fra kundens DB25-branchekode.

Grupperne bruges i skabelonerne som `{% if branche.byggeri %}` og styrer branchespecifikke afsnit:
risici, materialelister, hvidvaskrisiko, moms. Se docs/skabeloner-format.md.

Hvidvaskrisikoen bygger på Hvidvasksekretariatets og Erhvervsstyrelsens nationale risikovurdering
og branchevejledninger: kontantintensive brancher, byggeri (sort arbejde/fakturafabrikker), bilhandel,
ejendomme, vikar- og rengøringsbranchen, transport, restauration og spil vurderes som højere risiko.
Det er et udgangspunkt – den konkrete vurdering laves altid i risikovurderingen af kunden.
"""

import re

from integrations.industry import describe, normalize_code

# (gruppe, kodepræfikser på 2–6 cifre)
PREFIXES = {
    "landbrug": ("01", "02", "03"),
    "fremstilling": tuple(f"{n:02d}" for n in range(10, 34)),
    "forsyning": ("35", "36", "37", "38", "39"),
    "byggeri": ("41", "42", "43"),
    "engros": ("46",),
    "detail": ("47",),
    "transport": ("49", "50", "51", "52", "53"),
    "hotel": ("55",),
    "restauration": ("56",),
    "medier": ("58", "59", "60"),
    "it": ("61", "62", "63"),
    "finans": ("64", "65", "66"),
    "ejendom": ("68",),
    "holding": ("6421", "701"),
    "bilhandel": ("4671", "4672", "4673", "4781", "4782", "4783", "953"),
    "liberalt_erhverv": ("69", "70", "71", "72", "73", "74", "75"),
    "udlejning_service": ("77", "78", "79", "80", "81", "82"),
    "rengoering": ("812",),
    "vikar": ("78",),
    "undervisning": ("85",),
    "sundhed": ("86", "87", "88"),
    "kultur_fritid": ("90", "91", "92", "93"),
    "spil": ("92",),
    "forening": ("94",),
    "personlig_service": ("95", "96"),
}

LABELS = {
    "landbrug": "landbrug, skovbrug og fiskeri", "fremstilling": "fremstilling", "forsyning": "forsyning",
    "byggeri": "bygge- og anlæg", "engros": "engroshandel", "detail": "detailhandel",
    "bilhandel": "handel med og reparation af motorkøretøjer", "transport": "transport",
    "hotel": "hotel og overnatning", "restauration": "restauration", "medier": "medier og udgivelse",
    "it": "IT og telekommunikation", "finans": "finansiering og forsikring", "ejendom": "fast ejendom",
    "holding": "holding", "liberalt_erhverv": "liberale erhverv og rådgivning",
    "udlejning_service": "udlejning og forretningsservice", "rengoering": "rengøring", "vikar": "vikarbureau",
    "undervisning": "undervisning", "sundhed": "sundhed og social", "kultur_fritid": "kultur og fritid",
    "spil": "spil og lotteri", "forening": "foreninger og organisationer",
    "personlig_service": "personlige serviceydelser",
}

# Grupper der afledes af andre (rækkefølgen betyder noget).
KONTANTINTENSIV = {"detail", "restauration", "personlig_service", "bilhandel", "spil", "hotel"}
MOMSFRITAGET = {"sundhed", "undervisning", "finans", "kultur_fritid", "forening", "spil"}
LAGER = {"fremstilling", "engros", "detail", "bilhandel", "landbrug"}
IGANGVAERENDE = {"byggeri", "liberalt_erhverv", "it"}
# Officielle "klassificerede risikobrancher" efter årsregnskabslovens § 135, stk. 5 og 8:
# BEK nr. 1488 af 27/11/2025 § 1 (DB25-koder, udtømmende; gælder for regnskabsår fra 1/1 2025 og i to år, § 2).
# Hovedbranchekoden i CVR på balancedagen er afgørende. Klasse B-virksomheder i en risikobranche med
# nettoomsætning over 5 mio. kr. i 2 på hinanden følgende år skal have mindst en opstillingserklæring.
RISIKOBRANCHER_KILDE = "BEK nr. 1488 af 27/11/2025 om klassificerede risikobrancher, § 1"
RISIKOBRANCHER = frozenset({
    "494100", "494200", "561110", "561190", "562100", "562200", "563010", "563020", "639100",
    "811000", "812100", "812210", "812290", "812300", "962200",
})

# ---------------------------------------------------------------------------------------------------------
# Revisorhusets EGEN, indikative vurdering af brancherisiko efter hvidvaskloven.
#
# Det er IKKE en officiel klassificering og IKKE listen over "klassificerede risikobrancher" efter
# årsregnskabslovens § 135. Den er et udgangspunkt for den konkrete risikovurdering af hver kunde, som
# hvidvaskloven kræver. Begrundelserne bygger på almindeligt kendte risikofaktorer (kontanter, værdifulde og
# let omsættelige aktiver, lange underleverandørkæder, arbejdsintensive brancher med risiko for sort løn,
# komplekse ejerstrukturer og handel over grænser). Vurderingen vises og begrundes på siden
# Admin → Brancherisiko, og skabelonerne henviser til den. Ændres den her, ændres den alle steder.
# ---------------------------------------------------------------------------------------------------------
RISK = {
    "byggeri": ("høj", [
        "Lange kæder af underentreprenører gør det svært at se, hvem der reelt udfører og betaler for arbejdet.",
        "Risiko for fakturaer uden reel ydelse (\"fakturafabrikker\"), der bruges til at skaffe kontanter til sort løn.",
        "Arbejdsintensivt med mange midlertidige og udenlandske medarbejdere og risiko for sort arbejde.",
        "Private kunder betaler i nogle tilfælde kontant eller uden faktura.",
    ], ["Kontrollér underleverandører (CVR, ejere, momsregistrering, om de har ansatte).",
        "Sammenhold lønsum og antal ansatte med omsætningen.", "Store kontanthævninger og betalinger til nye leverandører."]),
    "restauration": ("høj", [
        "Høj andel kontantomsætning, som er svær at efterprøve – ulovlige midler kan blandes ind i omsætningen.",
        "Risiko for sort løn og ufuldstændig registrering af salg.",
        "Hyppige ejerskifter og stråmandskonstruktioner forekommer.",
    ], ["Kasseapparat/POS, Z-rapporter og daglige kasseafstemninger.",
        "Bruttoavance og omsætning sammenholdt med indkøb og branchetal.", "Hvem står reelt bag virksomheden."]),
    "bilhandel": ("høj", [
        "Høj værdi pr. vare, som let kan videresælges – egnet til at placere og flytte midler.",
        "Risiko for kontantbetaling (kontantforbuddet i hvidvaskloven skal overholdes) og handel med udlandet.",
        "Brugtmomsordningen og eksport giver mulighed for fejl og misbrug.",
    ], ["Betalingsform og betaler ved køb og salg.", "Kontantforbuddet overholdes.",
        "Køber/sælger i udlandet og dokumentation for eksport."]),
    "spil": ("høj", [
        "Gevinster kan bruges til at forklare, hvor penge kommer fra.",
        "Kontanter og hurtige ind- og udbetalinger.",
    ], ["Tilladelse fra Spillemyndigheden.", "Kontantstrømme og udbetalinger af gevinster."]),
    "rengoering": ("høj", [
        "Arbejdsintensiv branche med risiko for sort løn og social dumping.",
        "Risiko for fakturaer uden reel ydelse og lange underleverandørkæder.",
    ], ["Lønsum og antal ansatte sammenholdt med omsætningen.", "Underleverandører og kontanthævninger."]),
    "vikar": ("høj", [
        "Arbejdsintensiv branche med risiko for sort løn og misbrug af udenlandsk arbejdskraft.",
        "Mange korte ansættelser og hurtige udbetalinger gør kontrollen sværere.",
    ], ["Afstemning af løn, A-skat og eIndkomst.", "Arbejdstilladelser og registrering af udenlandske ansatte."]),
    "ejendom": ("høj", [
        "Fast ejendom har høj værdi og bruges til at placere større beløb.",
        "Køb kan finansieres med midler af ukendt oprindelse eller via komplekse eller udenlandske ejere.",
        "Lejeindtægter kan modtages kontant.",
    ], ["Finansiering af køb (egne midler, lån, hvorfra).", "Reelle ejere og deres midlers oprindelse.",
        "Handelspriser sammenholdt med markedsværdi."]),
    "detail": ("forhøjet", [
        "Kontantsalg forekommer, og varer kan være let omsættelige.",
    ], ["Kasseafstemning og kontantandel.", "Bruttoavance sammenholdt med branchen."]),
    "transport": ("forhøjet", [
        "Taxa og persontransport har kontantbetaling.",
        "Grænseoverskridende transport og brug af underleverandører.",
    ], ["Kontantandel og kørselsdata (taxameter/kørebøger).", "Underleverandører og udenlandske kunder."]),
    "hotel": ("forhøjet", [
        "Kontantbetaling og betalinger fra udlandet forekommer.",
    ], ["Kasseafstemning og betalinger fra udlandet."]),
    "personlig_service": ("forhøjet", [
        "Små enheder med kontantbetaling (frisør, skønhed, neglesalon m.fl.), hvor omsætningen er svær at efterprøve.",
    ], ["Kasseapparat, kontantandel og omsætning pr. medarbejder."]),
    "holding": ("forhøjet", [
        "Komplekse ejerstrukturer kan skjule, hvem der reelt ejer og kontrollerer.",
        "Midler flyttes mellem koncernselskaber og ejere.",
    ], ["Reelle ejere og koncerndiagram.", "Lån og mellemregninger med ejere og nærtstående."]),
    "finans": ("forhøjet", [
        "Finansielle virksomheder kan selv være omfattet af hvidvaskloven og bruges til at flytte midler.",
    ], ["Tilladelse/registrering hos Finanstilsynet.", "Kundernes midler og pengestrømme."]),
    "engros": ("forhøjet", [
        "Handel med udlandet giver risiko for handelsbaseret hvidvask (fakturering over eller under markedspris).",
    ], ["Priser sammenholdt med markedet.", "Kunder og leverandører i højrisikolande."]),
}
# Kontantintensive virksomheder uden for grupperne ovenfor får "forhøjet".
KONTANT_RISK = ("forhøjet", ["Kontantintensiv aktivitet, hvor omsætningen er svær at efterprøve."],
                ["Kasseafstemning og kontantandel."])
NORMAL_RISK = ("normal", ["Branchen har ikke i sig selv særlige risikofaktorer – risikoen vurderes konkret for kunden."], [])
HOEJ_RISIKO = {g for g, (lvl, _, _) in RISK.items() if lvl == "høj"}
FORHOEJET_RISIKO = {g for g, (lvl, _, _) in RISK.items() if lvl == "forhøjet"}

# Titler, der afslører særlige forhold.
_KIOSK = re.compile(r"kiosk|tankstation|taxi|taxa|vaskeri|frisør|skønhed|neglesalon|tatover", re.I)
_UDLEJNING_FAST = re.compile(r"udlejning af .*(bolig|erhvervsejendom|fast ejendom)", re.I)


def groups(code):
    """{gruppe: True, …} for kundens branchekode (tom hvis koden mangler eller er ukendt)."""
    norm, _ = normalize_code(code)
    if not norm:
        return set(), None
    info = describe(norm) or {}
    title = " ".join([info.get("title", "")] + [p.get("title", "") for p in info.get("path", [])])
    found = {g for g, prefixes in PREFIXES.items() if norm.startswith(prefixes)}
    if "holding" in found:
        found.discard("finans")  # holdingselskaber er ikke finansielle virksomheder i hvidvasklovens forstand
    extra = set()
    if found & KONTANTINTENSIV or _KIOSK.search(title) or norm.startswith(("4933", "4711", "473")):
        extra.add("kontantintensiv")
    if found & MOMSFRITAGET or (norm.startswith("68") and _UDLEJNING_FAST.search(info.get("title", ""))):
        extra.add("momsfritaget")
    if found & LAGER:
        extra.add("lager")
    if found & IGANGVAERENDE:
        extra.add("igangvaerende_arbejder")
    if "ejendom" in found:
        extra.add("investeringsejendomme")
    return found | extra, info


def assess(found):
    """(niveau, begrundelser, fokuspunkter) – det højeste niveau blandt kundens grupper."""
    hits = [(g, RISK[g]) for g in found if g in RISK]
    for level in ("høj", "forhøjet"):
        chosen = [r for _, r in hits if r[0] == level]
        if chosen:
            return level, [x for r in chosen for x in r[1]], [x for r in chosen for x in r[2]]
    if "kontantintensiv" in found:
        return KONTANT_RISK
    return NORMAL_RISK


def overview():
    """Til siden Brancherisiko: alle grupper med niveau, begrundelse, fokus og kodepræfikser."""
    rows = []
    for g, (level, reasons, focus) in RISK.items():
        rows.append({"group": g, "label": LABELS.get(g, g), "level": level, "reasons": reasons, "focus": focus,
                     "prefixes": list(PREFIXES.get(g, ()))})
    for g in PREFIXES:
        if g not in RISK:
            rows.append({"group": g, "label": LABELS.get(g, g), "level": "normal", "reasons": NORMAL_RISK[1],
                         "focus": [], "prefixes": list(PREFIXES[g])})
    order = {"høj": 0, "forhøjet": 1, "normal": 2}
    rows.sort(key=lambda r: (order[r["level"]], r["label"]))
    return rows


def context(code):
    """Flettefelterne `branche.*`."""
    found, info = groups(code)
    norm, _ = normalize_code(code)
    risk, reasons, focus = assess(found)
    main = next((g for g in ("bilhandel", "holding", "rengoering", "vikar", "spil", *PREFIXES) if g in found), None)
    ctx = {g: g in found for g in [*PREFIXES, "kontantintensiv", "momsfritaget", "lager",
                                   "igangvaerende_arbejder", "investeringsejendomme"]}
    ctx.update({
        "risikobranche": bool(norm and norm in RISIKOBRANCHER),
        "hvidvask_risiko": risk,
        "hvidvask_grunde": reasons,
        "hvidvask_fokus": focus,
        "navn": LABELS.get(main, "") if main else "",
        "grupper": sorted(found),
        "titel": (info or {}).get("title", ""),
    })
    return ctx
