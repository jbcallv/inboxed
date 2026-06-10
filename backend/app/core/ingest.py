import csv
import io
from typing import Any
import openpyxl

_FIELD_ALIASES: dict[str, list[str]] = {
    "first_name":       ["first name", "firstname", "first", "given name", "given_name"],
    "last_name":        ["last name", "lastname", "last", "surname", "family name", "family_name"],
    "company_name":     ["company", "company name", "organization", "organisation", "org"],
    "company_website":  ["website", "company website", "domain", "url", "site"],
    "position":         ["title", "job title", "jobtitle", "role", "position"],
    "bio":              ["bio", "about", "description", "summary"],
    "email":            ["email", "email address", "e-mail", "emailaddress"],
}

_KNOWN_FIELDS = set(_FIELD_ALIASES)


def parse_upload(
    content: bytes,
    filename: str,
    column_map: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """
    Parses CSV or XLSX bytes into a list of contact dicts.
    column_map overrides auto-detection: keys are canonical field names,
    values are the source column headers.
    """
    if filename.lower().endswith(".xlsx"):
        rows, headers = _parse_xlsx(content)
    else:
        rows, headers = _parse_csv(content)

    mapping = column_map or _detect_mapping(headers)
    return [_map_row(row, mapping) for row in rows if _has_useful_data(row, mapping)]


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
    """Returns {canonical_field: source_header} for matched columns."""
    normalised = {h: h.strip().lower() for h in headers}
    mapping: dict[str, str] = {}
    for field, aliases in _FIELD_ALIASES.items():
        for header, norm in normalised.items():
            if norm == field or norm in aliases:
                mapping[field] = header
                break
    return mapping


def _map_row(row: dict, mapping: dict[str, str]) -> dict[str, Any]:
    return {
        field: row.get(source_header, "").strip()
        for field, source_header in mapping.items()
    }


def _has_useful_data(row: dict, mapping: dict[str, str]) -> bool:
    first = row.get(mapping.get("first_name", ""), "").strip()
    last = row.get(mapping.get("last_name", ""), "").strip()
    if not first and not last:
        return False
    return any(bool(row.get(h, "").strip()) for h in mapping.values())
