"""
alert_store.py — Patient alert CRUD.

Alerts are raised when a patient scan hits CRITICAL or HIGH priority.
Persisted to data/alerts.json.

Public API
----------
raise_alert(patient_id, doctor_id, priority, message, scan_data) → dict
get_alerts_for_doctor(doctor_id)       → list[dict]   (newest first)
get_alerts_for_patient(patient_id)     → list[dict]
get_unreviewed_count(doctor_id)        → int
mark_reviewed(alert_id, notes)         → None
alert_already_raised(patient_id, scan_date, priority) → bool
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime

_UTIL = os.path.dirname(os.path.abspath(__file__))
_STORE_PATH = os.path.join(_UTIL, "..", "..", "data", "alerts.json")

# Only raise alerts for these priorities
ALERT_PRIORITIES = {"CRITICAL", "HIGH"}


def _load() -> list[dict]:
    if not os.path.exists(_STORE_PATH):
        _save([])
    with open(_STORE_PATH, "r") as f:
        return json.load(f)


def _save(alerts: list[dict]) -> None:
    os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)
    with open(_STORE_PATH, "w") as f:
        json.dump(alerts, f, indent=2)


def raise_alert(
    patient_id: str,
    doctor_id: str | None,
    priority: str,
    message: str,
    scan_data: dict,
) -> dict:
    alert = {
        "alert_id":    f"A{uuid.uuid4().hex[:8].upper()}",
        "patient_id":  patient_id,
        "doctor_id":   doctor_id,
        "timestamp":   datetime.now().isoformat(timespec="seconds"),
        "priority":    priority,
        "message":     message,
        "scan_data":   scan_data,
        "reviewed":    False,
        "doctor_notes": "",
    }
    alerts = _load()
    alerts.append(alert)
    _save(alerts)
    return alert


def get_alerts_for_doctor(doctor_id: str) -> list[dict]:
    return sorted(
        [a for a in _load() if a.get("doctor_id") == doctor_id],
        key=lambda a: a["timestamp"],
        reverse=True,
    )


def get_alerts_for_patient(patient_id: str) -> list[dict]:
    return sorted(
        [a for a in _load() if a["patient_id"] == patient_id],
        key=lambda a: a["timestamp"],
        reverse=True,
    )


def get_unreviewed_count(doctor_id: str) -> int:
    return sum(
        1 for a in _load()
        if a.get("doctor_id") == doctor_id and not a["reviewed"]
    )


def mark_reviewed(alert_id: str, notes: str = "") -> None:
    alerts = _load()
    for a in alerts:
        if a["alert_id"] == alert_id:
            a["reviewed"] = True
            a["doctor_notes"] = notes
            _save(alerts)
            return
    raise ValueError(f"Alert {alert_id!r} not found.")


def alert_already_raised(patient_id: str, scan_date: str, priority: str) -> bool:
    """Prevent duplicate alerts for the same scan result."""
    return any(
        a["patient_id"] == patient_id
        and a["timestamp"].startswith(scan_date)
        and a["priority"] == priority
        for a in _load()
    )
