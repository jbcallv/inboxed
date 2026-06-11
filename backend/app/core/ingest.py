import csv
import io
from typing import Any
import openpyxl

_FIELD_ALIASES: dict[str, list[str]] = {
    "first_name":       ["first name", "firstname", "first", "given name", "given_name"],
    "last_name":        ["last name", "lastname", "last", "surname", "family name", "family_name"],
    "company_name":     ["company", "company name", "organization", "organisation", "org", "name"],
    "company_website":  ["website", "company website", "url", "site"],
    "position":         ["title", "job title", "jobtitle", "role", "position"],
    "bio":              ["bio", "about", "description", "summary", "matchmaking_message", "match_message"],
    "email":            ["email", "email address", "e-mail", "emailaddress"],
}

# Extra columns used only to build a synthetic bio — not stored as their own fields
_BIO_SUPPLEMENT_COLS = [
    "subtypes",
    "company_insights.industry", "company_insights.employees", "company_insights.revenue",
    "company_insights.founded_year",
    "city", "state",
    "rating", "reviews",
    "contact_linkedin",
]

_KNOWN_FIELDS = set(_FIELD_ALIASES)


def parse_upload(
    content: bytes,
    filename: str,
    column_map: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    if filename.lower().endswith(".xlsx"):
        rows, headers = _parse_xlsx(content)
    else:
        rows, headers = _parse_csv(content)

    mapping = column_map or _detect_mapping(headers)
    supplement_map = _detect_supplement_cols(headers)
    result = []
    for row in rows:
        if not _has_useful_data(row, mapping):
            continue
        contact = _map_row(row, mapping)
        if not contact.get("bio"):
            synth = _synthesize_bio(row, supplement_map)
            if synth:
                contact["bio"] = synth
        result.append(contact)
    return result


def _parse_csv(content: bytes) -> tuple[list[dict], list[str]]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    headers = reader.fieldnames or []
    return rows, list(headers)


def _parse_xlsx(content: bytes) -> tuple[list[dict], list[str]]:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    all_rows = list(ws.iter_rows(values_only=True))
    if not all_rows:
        return [], []
    headers = [str(h).strip() if h is not None else "" for h in all_rows[0]]
    rows = [
        {headers[i]: (str(v).strip() if v is not None else "") for i, v in enumerate(row)}
        for row in all_rows[1:]
    ]
    return rows, headers


def _detect_mapping(headers: list[str]) -> dict[str, str]:
    normalised = {h: h.strip().lower() for h in headers}
    mapping: dict[str, str] = {}
    for field, aliases in _FIELD_ALIASES.items():
        for header, norm in normalised.items():
            if norm == field or norm in aliases:
                mapping[field] = header
                break
    return mapping


def _detect_supplement_cols(headers: list[str]) -> dict[str, str]:
    """Returns {canonical_supplement_name: actual_header} for bio-supplement columns."""
    lower = {h.strip().lower(): h for h in headers}
    found = {}
    for col in _BIO_SUPPLEMENT_COLS:
        if col in lower:
            found[col] = lower[col]
    return found


def _map_row(row: dict, mapping: dict[str, str]) -> dict[str, Any]:
    return {
        field: (row.get(source_header) or "").strip()
        for field, source_header in mapping.items()
    }


def _has_useful_data(row: dict, mapping: dict[str, str]) -> bool:
    email_col = mapping.get("email", "")
    return bool((row.get(email_col) or "").strip())


def _synthesize_bio(row: dict, supplement_map: dict[str, str]) -> str:
    """Builds a bio string from supplemental columns when no explicit bio exists."""
    parts = []
    for col in _BIO_SUPPLEMENT_COLS:
        header = supplement_map.get(col)
        if not header:
            continue
        val = (row.get(header) or "").strip()
        if not val or val.lower() in ("none", "null", "false", "true"):
            continue
        if col == "company_insights.employees":
            parts.append(f"~{val} employees")
        elif col == "company_insights.revenue":
            try:
                rev = int(float(val))
                parts.append(f"~${rev:,} revenue")
            except ValueError:
                pass
        elif col == "company_insights.founded_year":
            parts.append(f"founded {val}")
        elif col == "rating":
            reviews_header = supplement_map.get("reviews")
            reviews_val = (row.get(reviews_header) or "").strip() if reviews_header else ""
            try:
                stars = float(val)
                suffix = f" ({int(float(reviews_val))} reviews)" if reviews_val else ""
                parts.append(f"{stars}/5 stars{suffix}")
            except ValueError:
                pass
        elif col == "reviews":
            continue  # handled inside rating block above
        elif col == "contact_linkedin":
            parts.append(f"LinkedIn: {val}")
        else:
            parts.append(val)
    return " | ".join(parts)
