"""Pakker og funktioner (feature flags).

Pakkerne gælder for kundens egne brugere. Medarbejdere hos Ajan Partners, der
arbejder i en kunde via en adgang (AccessGrant), er ikke begrænset af pakken:
de leverer selv den bogføring, som Mini-kunder ikke laver.

`FEATURE_PATHS` knytter API-stier (under /api/v1/) til en funktion. En sti, der
ikke står her, er åben for alle pakker. Middleware'en i tenancy/middleware.py
afviser med 403, når kundens pakke mangler funktionen.
"""

FEATURES = {
    "invoicing": "Fakturering, kreditnotaer og tilbud",
    "purchases": "Regninger, udgifter og leverandører",
    "bank": "Bankimport, bankafstemning og bankregler",
    "bank_feed": "Automatisk bankkobling (open banking)",
    "vat": "Momsangivelse og momsafstemning",
    "einvoice_send": "Send e-faktura (Peppol/NemHandel)",
    "einvoice_receive": "Modtag e-faktura",
    "journal": "Manuelle posteringer, journaler og periodeafslutning",
    "lettrage": "Udligning og aldersfordeling",
    "chart_edit": "Rediger kontoplan",
    "payroll": "Løn",
    "projects": "Projekter, afdelinger og budget",
    "reports": "Rapporter (resultat, balance, saldobalance)",
}

# Pakkernes standardindhold. Pakkerne gemmes i databasen (tenancy.Package) og
# kan ændres i admin-portalen; dette er kun det, seed_packages opretter.
DEFAULT_PACKAGES = [
    {
        "code": "mini",
        "name": "Mini",
        "description": "Du uploader bilag og fakturerer – Ajan Partners bogfører.",
        "order": 1,
        "features": ["invoicing", "einvoice_receive", "reports"],
        "limits": {"invoices_per_month": 10, "users": 1},
    },
    {
        "code": "standard",
        "name": "Standard",
        "description": "Fuld bogføring med bank, moms og e-faktura.",
        "order": 2,
        "features": ["invoicing", "purchases", "bank", "bank_feed", "vat", "einvoice_send",
                     "einvoice_receive", "journal", "lettrage", "chart_edit", "reports"],
        "limits": {"invoices_per_month": None, "users": 3},
    },
    {
        "code": "pro",
        "name": "Pro",
        "description": "Alt i Standard plus løn, projekter og ubegrænset antal brugere.",
        "order": 3,
        "features": list(FEATURES),
        "limits": {"invoices_per_month": None, "users": None},
    },
]

FEATURE_PATHS = {
    "invoicing": ("invoices", "credit-notes", "quotes", "reminders"),
    "purchases": ("bills", "expenses", "supplier-mappings"),
    "bank": ("bank-statements", "bank-transactions", "bank-reconciliations", "bank-rules",
             "transactions", "payments"),
    "bank_feed": ("bank-feeds",),
    "vat": ("vat", "reports/tax", "tax-codes"),
    "einvoice_send": ("einvoice/send",),
    "einvoice_receive": ("einvoice/inbox",),
    "journal": ("journal-entries", "journals", "periods", "closing", "year-end"),
    "lettrage": ("lettrage", "reports/aging-receivable", "reports/aging-payable"),
    "payroll": ("payroll",),
    "projects": ("projects", "reports/project-pnl"),
}

# Skrivning til disse stier kræver chart_edit (læsning er åben for alle).
WRITE_FEATURE_PATHS = {
    "chart_edit": ("accounts",),
}


def feature_for_path(subpath, method):
    """The feature a request under /api/v1/ needs, or None."""
    subpath = subpath.strip("/")
    for feature, prefixes in FEATURE_PATHS.items():
        if any(subpath == p or subpath.startswith(p + "/") for p in prefixes):
            return feature
    if method not in ("GET", "HEAD", "OPTIONS"):
        for feature, prefixes in WRITE_FEATURE_PATHS.items():
            if any(subpath == p or subpath.startswith(p + "/") for p in prefixes):
                return feature
    return None
