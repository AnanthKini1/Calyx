"""
medical_importer.py — Multi-format medical history importer.

Accepts PDF, CSV, or JSON files and attempts to extract / map the fields
used in the ChroniScan patient model:

  blood_glucose   (mg/dL)
  serum_albumin   (g/dL)
  mobility_score  (0-10)
  post_op_day     (int)
  comorbidities   (list of known strings)
  age             (int)

Returns a dict with successfully extracted keys and a "warnings" list
describing any fields that could not be resolved.

Usage
-----
from utils.medical_importer import parse_file
result = parse_file(file_bytes, filename)
# result = {
#   "extracted": {"blood_glucose": 145.0, ...},
#   "warnings":  ["Could not detect mobility_score"],
# }
"""

from __future__ import annotations

import io
import json
import re

# ---------------------------------------------------------------------------
# Known comorbidity aliases
# ---------------------------------------------------------------------------

_COMORBIDITY_MAP: dict[str, str] = {
    "type 2 diabetes":           "Type 2 Diabetes",
    "type2 diabetes":            "Type 2 Diabetes",
    "t2dm":                      "Type 2 Diabetes",
    "diabetes mellitus":         "Type 2 Diabetes",
    "diabetes":                  "Type 2 Diabetes",
    "obesity":                   "Obesity",
    "obese":                     "Obesity",
    "bmi > 30":                  "Obesity",
    "hypertension":              "Hypertension",
    "high blood pressure":       "Hypertension",
    "htn":                       "Hypertension",
    "peripheral artery disease": "Peripheral Artery Disease",
    "peripheral arterial disease": "Peripheral Artery Disease",
    "pad":                       "Peripheral Artery Disease",
    "malnutrition":              "Malnutrition",
    "malnourished":              "Malnutrition",
    "protein deficiency":        "Malnutrition",
}

_KNOWN_COMORBIDITIES = list(set(_COMORBIDITY_MAP.values()))

# Regex patterns for numeric field extraction
_PATTERNS = {
    "blood_glucose": [
        r"(?:blood[\s_-]*glucose|glucose|bg|fasting[\s_-]*glucose)[\s:=]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl|mg/?dl)?",
        r"([0-9]+(?:\.[0-9]+)?)\s*mg/dl\s*(?:glucose|bg)",
    ],
    "serum_albumin": [
        r"(?:serum[\s_-]*albumin|albumin|alb)[\s:=]*([0-9]+(?:\.[0-9]+)?)\s*(?:g/dl|g/?dl)?",
        r"([0-9]+(?:\.[0-9]+)?)\s*g/dl\s*(?:albumin|alb)",
    ],
    "post_op_day": [
        r"(?:post[\s_-]*op(?:erative)?[\s_-]*day|pod|days[\s_-]*post[\s_-]*op|days[\s_-]*since[\s_-]*surgery)[\s:=]*([0-9]+)",
        r"([0-9]+)\s*days?\s+(?:post[\s_-]*op|after surgery|post surgery)",
    ],
    "age": [
        r"(?:age|patient age|dob|year[s]? old)[\s:=]*([0-9]{1,3})",
        r"([0-9]{1,3})\s*(?:year[s]?[\s_-]*old|y/?o\b)",
    ],
    "mobility_score": [
        r"(?:mobility[\s_-]*score|ambulation[\s_-]*score|mobility)[\s:=]*([0-9]|10)(?:/10)?",
    ],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_file(file_bytes: bytes, filename: str) -> dict:
    """
    Detect format from filename extension and parse accordingly.
    Returns {"extracted": dict, "warnings": list[str]}.
    """
    lower = filename.lower()
    if lower.endswith(".json"):
        return _parse_json(file_bytes)
    elif lower.endswith(".csv"):
        return _parse_csv(file_bytes)
    elif lower.endswith(".pdf"):
        return _parse_pdf(file_bytes)
    else:
        return {
            "extracted": {},
            "warnings": [f"Unsupported file type: {filename}. Use PDF, CSV, or JSON."],
        }


# ---------------------------------------------------------------------------
# Format parsers
# ---------------------------------------------------------------------------

def _parse_json(file_bytes: bytes) -> dict:
    try:
        raw = json.loads(file_bytes.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        return {"extracted": {}, "warnings": [f"JSON parse error: {e}"]}

    # Flatten one level of nesting if the root is a list
    if isinstance(raw, list):
        raw = raw[0] if raw else {}

    extracted: dict = {}
    warnings:  list = []

    # Normalise keys: lowercase, replace spaces/hyphens with underscores
    flat = {_norm_key(k): v for k, v in raw.items()}

    _extract_numeric(flat, extracted, warnings)
    _extract_comorbidities_from_dict(flat, extracted)

    _warn_missing(extracted, warnings)
    return {"extracted": extracted, "warnings": warnings}


def _parse_csv(file_bytes: bytes) -> dict:
    try:
        import pandas as pd
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return {"extracted": {}, "warnings": [f"CSV parse error: {e}"]}

    # Normalise column names
    df.columns = [_norm_key(c) for c in df.columns]

    extracted: dict = {}
    warnings:  list = []

    # Take first row values
    row = df.iloc[0].to_dict() if len(df) > 0 else {}
    _extract_numeric(row, extracted, warnings)
    _extract_comorbidities_from_dict(row, extracted)

    # If comorbidities column contains a delimited string
    for col in df.columns:
        if "comorbid" in col or "condition" in col or "diagnosis" in col:
            val = str(row.get(col, ""))
            _extract_comorbidities_from_text(val, extracted)
            break

    _warn_missing(extracted, warnings)
    return {"extracted": extracted, "warnings": warnings}


def _parse_pdf(file_bytes: bytes) -> dict:
    extracted: dict = {}
    warnings:  list = []

    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except ImportError:
            return {
                "extracted": {},
                "warnings": ["PDF parsing requires pdfplumber or pypdf. "
                             "Install with: pip install pdfplumber"],
            }
    except Exception as e:
        return {"extracted": {}, "warnings": [f"PDF parse error: {e}"]}

    _extract_numeric_from_text(text, extracted, warnings)
    _extract_comorbidities_from_text(text, extracted)
    _warn_missing(extracted, warnings)
    return {"extracted": extracted, "warnings": warnings}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _norm_key(k: str) -> str:
    return re.sub(r"[\s\-]+", "_", str(k).lower().strip())


_FIELD_ALIASES: dict[str, list[str]] = {
    "blood_glucose":  ["blood_glucose", "glucose", "bg", "fasting_glucose", "blood_sugar"],
    "serum_albumin":  ["serum_albumin", "albumin", "alb"],
    "post_op_day":    ["post_op_day", "pod", "days_since_surgery", "postoperative_day",
                       "days_post_op", "post_operative_day"],
    "age":            ["age", "patient_age", "years_old"],
    "mobility_score": ["mobility_score", "mobility", "ambulation_score"],
}


def _extract_numeric(flat: dict, extracted: dict, warnings: list) -> None:
    """Try to map dict keys to our field names."""
    for field, aliases in _FIELD_ALIASES.items():
        for alias in aliases:
            if alias in flat:
                try:
                    val = float(str(flat[alias]).replace(",", "").strip())
                    if field in ("post_op_day", "age", "mobility_score"):
                        extracted[field] = int(val)
                    else:
                        extracted[field] = round(val, 1)
                except (ValueError, TypeError):
                    pass
                break


def _extract_numeric_from_text(text: str, extracted: dict, warnings: list) -> None:
    lower = text.lower()
    for field, patterns in _PATTERNS.items():
        if field in extracted:
            continue
        for pat in patterns:
            m = re.search(pat, lower)
            if m:
                try:
                    val = float(m.group(1))
                    if field in ("post_op_day", "age", "mobility_score"):
                        extracted[field] = int(val)
                    else:
                        extracted[field] = round(val, 1)
                except ValueError:
                    pass
                break


def _extract_comorbidities_from_dict(flat: dict, extracted: dict) -> None:
    found = set(extracted.get("comorbidities", []))
    for key, val in flat.items():
        if any(x in key for x in ("comorbid", "condition", "diagnosis", "disease")):
            _extract_comorbidities_from_text(str(val), extracted)
    # Also check boolean-style columns
    for alias, canonical in _COMORBIDITY_MAP.items():
        norm = _norm_key(alias)
        if norm in flat:
            v = flat[norm]
            if str(v).lower() in ("true", "yes", "1", "x"):
                found.add(canonical)
    if found:
        extracted["comorbidities"] = list(found)


def _extract_comorbidities_from_text(text: str, extracted: dict) -> None:
    lower = text.lower()
    found = set(extracted.get("comorbidities", []))
    for alias, canonical in _COMORBIDITY_MAP.items():
        if alias in lower:
            found.add(canonical)
    if found:
        extracted["comorbidities"] = list(found)


def _warn_missing(extracted: dict, warnings: list) -> None:
    important = ["blood_glucose", "serum_albumin"]
    for f in important:
        if f not in extracted:
            warnings.append(f"Could not detect '{f}' — you can set it manually.")
