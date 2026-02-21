"""
doctor_store.py — JSON-backed doctor data store.

Persisted to data/doctors_store.json at the project root.
Seeded with one demo doctor on first run.

Public API
----------
list_doctors()                        → list[dict]
get_doctor(doctor_id)                 → dict | None
get_doctor_by_name(name)              → dict | None
create_doctor(name, specialty, patient_ids) → dict
link_patient(doctor_id, patient_id)   → None
doctor_exists(name)                   → bool
"""

from __future__ import annotations

import json
import os
import sys
import uuid

_UTIL = os.path.dirname(os.path.abspath(__file__))
_STORE_PATH = os.path.join(_UTIL, "..", "..", "data", "doctors_store.json")

_SEED = [
    {
        "doctor_id":   "D001",
        "role":        "doctor",
        "name":        "Dr. Priya Nair",
        "specialty":   "Wound Care & Surgery",
        "patient_ids": ["P001", "P002", "P003", "P004"],
    }
]


def _load() -> list[dict]:
    if not os.path.exists(_STORE_PATH):
        _save(_SEED)
    with open(_STORE_PATH, "r") as f:
        return json.load(f)


def _save(doctors: list[dict]) -> None:
    os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)
    with open(_STORE_PATH, "w") as f:
        json.dump(doctors, f, indent=2)


def list_doctors() -> list[dict]:
    return sorted(_load(), key=lambda d: d["name"])


def get_doctor(doctor_id: str) -> dict | None:
    for d in _load():
        if d["doctor_id"] == doctor_id:
            return d
    return None


def get_doctor_by_name(name: str) -> dict | None:
    for d in _load():
        if d["name"].lower() == name.strip().lower():
            return d
    return None


def doctor_exists(name: str) -> bool:
    return get_doctor_by_name(name) is not None


def create_doctor(
    name: str,
    specialty: str,
    patient_ids: list[str],
) -> dict:
    if doctor_exists(name):
        raise ValueError(f"A doctor named '{name}' already exists.")

    doctor = {
        "doctor_id":   f"D{uuid.uuid4().hex[:6].upper()}",
        "role":        "doctor",
        "name":        name.strip(),
        "specialty":   specialty.strip(),
        "patient_ids": list(patient_ids),
    }
    doctors = _load()
    doctors.append(doctor)
    _save(doctors)
    return doctor


def link_patient(doctor_id: str, patient_id: str) -> None:
    """Add patient_id to a doctor's patient list if not already there."""
    doctors = _load()
    for d in doctors:
        if d["doctor_id"] == doctor_id:
            if patient_id not in d["patient_ids"]:
                d["patient_ids"].append(patient_id)
            _save(doctors)
            return
    raise ValueError(f"Doctor {doctor_id!r} not found.")
