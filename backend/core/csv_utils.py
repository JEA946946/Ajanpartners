"""CSV export helpers with formula-injection protection.

A cell beginning with = + - @ (or tab/CR) is interpreted as a formula by Excel /
Google Sheets when the exported file is opened. Prefixing such cells with a single
quote neutralises that while displaying the original text.
"""

import csv

_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value):
    """Return a spreadsheet-safe version of a single cell value."""
    if value is None:
        return ""
    s = value if isinstance(value, str) else str(value)
    if s and s[0] in _DANGEROUS_PREFIXES:
        return "'" + s
    return s


class SafeWriter:
    """Drop-in for csv.writer that sanitises every cell against formula injection."""

    def __init__(self, fileobj):
        self._w = csv.writer(fileobj)

    def writerow(self, row):
        self._w.writerow([csv_safe(c) for c in row])

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
