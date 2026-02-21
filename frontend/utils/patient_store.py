"""
patient_store.py — JSON-backed patient data store.

Patients are persisted to data/patients_store.json at the project root.
On first run the store is seeded with the mock patients from mock_patients.py
so the demo works immediately without any registration step.

Public API
----------
list_patients()                          → list[dict]
list_patients_for_doctor(doctor_id)      → list[dict]
get_patient(patient_id)                  → dict | None
create_patient(fields, doctor_id)        → dict
update_patient_fields(patient_id, patch) → None
add_wound_scan(patient_id, scan_entry)   → None
get_latest_scan(patient)                 → dict | None
compute_area_delta(patient, n_days)      → float
patient_exists(name)                     → bool
"""

from __future__ import annotations

import json
import os
import sys
import uuid

_UTIL = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_UTIL, "..", ".."))  # project root

from data.mock_patients import PATIENTS as _MOCK_PATIENTS

_STORE_PATH = os.path.join(_UTIL, "..", "..", "data", "patients_store.json")


# ---------------------------------------------------------------------------
# Internal I/O
# ---------------------------------------------------------------------------

def _load() -> list[dict]:
    if not os.path.exists(_STORE_PATH):
        _seed()
    with open(_STORE_PATH, "r") as f:
        data = json.load(f)
    # Back-fill role and doctor_id for legacy records
    for p in data:
        p.setdefault("role", "patient")
        p.setdefault("doctor_id", "D001")
        p.setdefault("imported_history", {})
    return data


def _save(patients: list[dict]) -> None:
    os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)
    with open(_STORE_PATH, "w") as f:
        json.dump(patients, f, indent=2)


def _seed() -> None:
    """Write mock patients (with role fields) to the store on first run."""
    seeded = []
    for p in _MOCK_PATIENTS:
        seeded.append({
            **p,
            "role":             "patient",
            "doctor_id":        "D001",
            "imported_history": {},
        })
    _save(seeded)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_patients() -> list[dict]:
    return sorted(_load(), key=lambda p: p["name"])


def list_patients_for_doctor(doctor_id: str) -> list[dict]:
    return sorted(
        [p for p in _load() if p.get("doctor_id") == doctor_id],
        key=lambda p: p["name"],
    )


def get_patient(patient_id: str) -> dict | None:
    for p in _load():
        if p["patient_id"] == patient_id:
            return p
    return None


def patient_exists(name: str) -> bool:
    return any(p["name"].lower() == name.strip().lower() for p in _load())


def create_patient(
    name: str,
    age: int,
    comorbidities: list[str],
    blood_glucose: float,
    serum_albumin: float,
    mobility_score: int,
    post_op_day: int,
    doctor_id: str | None = None,
) -> dict:
    if patient_exists(name):
        raise ValueError(f"A patient named '{name}' already exists.")

    patient = {
        "patient_id":       f"P{uuid.uuid4().hex[:6].upper()}",
        "role":             "patient",
        "name":             name.strip(),
        "age":              age,
        "comorbidities":    comorbidities,
        "blood_glucose":    blood_glucose,
        "serum_albumin":    serum_albumin,
        "mobility_score":   mobility_score,
        "post_op_day":      post_op_day,
        "doctor_id":        doctor_id,
        "wound_history":    [],
        "imported_history": {},
    }

    patients = _load()
    patients.append(patient)
    _save(patients)
    return patient


def update_patient_fields(patient_id: str, patch: dict) -> None:
    """Merge patch dict into the patient record and persist."""
    patients = _load()
    for p in patients:
        if p["patient_id"] == patient_id:
            p.update(patch)
            _save(patients)
            return
    raise ValueError(f"Patient {patient_id!r} not found.")


def add_wound_scan(patient_id: str, scan_entry: dict) -> None:
    patients = _load()
    for p in patients:
        if p["patient_id"] == patient_id:
            p.setdefault("wound_history", []).append(scan_entry)
            _save(patients)
            return
    raise ValueError(f"Patient {patient_id!r} not found.")


def get_latest_scan(patient: dict) -> dict | None:
    history = patient.get("wound_history", [])
    return history[-1] if history else None


def compute_area_delta(patient: dict, n_days: int = 7) -> float:
    from data.mock_patients import compute_area_delta as _orig
    return _orig(patient, n_days)
