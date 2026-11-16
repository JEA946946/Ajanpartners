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
HOEJ_RISIKO = {"bilhandel", "spil", "restauration", "byggeri", "rengoering", "vikar", "ejendom"}
FORHOEJET_RISIKO = {"detail", "transport", "hotel", "personlig_service", "holding", "finans", "engros"}

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


def context(code):
    """Flettefelterne `branche.*`."""
    found, info = groups(code)
    if found & HOEJ_RISIKO:
        risk = "høj"
    elif found & FORHOEJET_RISIKO or "kontantintensiv" in found:
        risk = "forhøjet"
    else:
        risk = "normal"
    main = next((g for g in ("bilhandel", "holding", "rengoering", "vikar", "spil", *PREFIXES) if g in found), None)
    ctx = {g: g in found for g in [*PREFIXES, "kontantintensiv", "momsfritaget", "lager",
                                   "igangvaerende_arbejder", "investeringsejendomme"]}
    ctx.update({
        "hvidvask_risiko": risk,
        "navn": LABELS.get(main, "") if main else "",
        "grupper": sorted(found),
        "titel": (info or {}).get("title", ""),
    })
    return ctx
