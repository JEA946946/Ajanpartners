"""Officiel schematron-validering af dannede e-fakturaer.

    validate_ubl_xsd(xml, kind) -> [fejl]   UBL 2.1 XSD (OASIS)
    validate_peppol(xml) -> [fejl]   EN 16931 (CEN) + Peppol BIS 3.0, kun flag="fatal"
    validate_oioubl(xml, kind) -> [fejl]   OIOUBL 2.1 (Erhvervsstyrelsen), kun F-regler

Kræver saxonche og filerne i denne mappe (se SOURCES.txt). ``available()`` fortæller, om
valideringen kan køre; testene springer over, hvis ikke.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVRL = "{http://purl.oclc.org/dsdl/svrl}"
PEPPOL = (HERE / "en16931" / "EN16931-UBL-validation.xslt", HERE / "peppol" / "PEPPOL-EN16931-UBL.xslt")
UBL_XSD = {"invoice": HERE / "ubl21" / "maindoc" / "UBL-Invoice-2.1.xsd",
           "credit_note": HERE / "ubl21" / "maindoc" / "UBL-CreditNote-2.1.xsd"}
OIOUBL = {"invoice": HERE / "oioubl" / "OIOUBL_Invoice_Schematron.xsl",
          "credit_note": HERE / "oioubl" / "OIOUBL_CreditNote_Schematron.xsl"}


def available():
    try:
        import saxonche  # noqa: F401
    except ImportError:
        return False
    try:
        import xmlschema  # noqa: F401
    except ImportError:
        return False
    return all(p.exists() for p in (*PEPPOL, *OIOUBL.values(), *UBL_XSD.values()))


def validate_ubl_xsd(xml, kind="invoice"):
    import xmlschema

    if kind not in _STATE.setdefault("xsd", {}):
        _STATE["xsd"][kind] = xmlschema.XMLSchema(str(UBL_XSD[kind]))
    return [f"{e.path}: {e.reason}" for e in _STATE["xsd"][kind].iter_errors(xml)]


_STATE = {}


def _processor():
    if "proc" not in _STATE:
        import atexit

        from saxonche import PySaxonProcessor

        proc = PySaxonProcessor(license=False)
        _STATE.update(proc=proc, xslt=proc.new_xslt30_processor(), exe={})
        atexit.register(_STATE.clear)  # frigiv Saxon før fortolkeren lukker ned
    return _STATE["proc"], _STATE["xslt"]


def _executable(path):
    _, xslt = _processor()
    if path not in _STATE["exe"]:
        _STATE["exe"][path] = xslt.compile_stylesheet(stylesheet_file=str(path))
    return _STATE["exe"][path]


def _run(path, xml):
    proc, _ = _processor()
    node = proc.parse_xml(xml_text=xml)
    return _executable(path).transform_to_string(xdm_node=node)


def validate_peppol(xml):
    errors = []
    for path in PEPPOL:
        for f in ET.fromstring(_run(path, xml)).iter(SVRL + "failed-assert"):
            if f.get("flag", "fatal") == "fatal":
                errors.append(f"{f.get('id')}: {(f.findtext(SVRL + 'text') or '').strip()} @ {f.get('location')}")
    return errors


def validate_oioubl(xml, kind="invoice"):
    root = ET.fromstring(_run(OIOUBL[kind], xml))
    errors = []
    for e in root.iter("Error"):
        text = (e.findtext("Description") or "").strip()
        if text.startswith("[F-"):  # [W-...] er advarsler
            errors.append(f"{text} @ {e.findtext('Xpath')}")
    return errors
