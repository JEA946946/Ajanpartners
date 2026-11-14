"""Shared upload validation for stored files (documents, expense receipts)."""

import os

# Extensions that make sense for receipts/accounting documents.
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".xls", ".xlsx", ".csv", ".doc", ".docx", ".txt",
}

MAX_UPLOAD_MB = 15


def validate_upload(uploaded_file):
    """Return an error message if the file is not acceptable, else None."""
    if uploaded_file is None:
        return None
    ext = os.path.splitext(uploaded_file.name or "")[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return (
            f"File type '{ext or 'unknown'}' is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
        )
    if uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        return f"File is too large (max {MAX_UPLOAD_MB} MB)"
    return None
