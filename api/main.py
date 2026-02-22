"""
api/main.py — ChroniScan FastAPI Backend

Provides REST endpoints consumed by the React frontend.
Run with:  uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from datetime import date
from typing import Optional

import base64

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make project root importable
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from knowledge_graph import evaluate_healing

# ---------------------------------------------------------------------------
# JSON store paths
# ---------------------------------------------------------------------------

_PATIENTS_PATH = os.path.join(_ROOT, "data", "patients_store.json")
_DOCTORS_PATH  = os.path.join(_ROOT, "data", "doctors_store.json")


def _load_patients() -> list[dict]:
    with open(_PATIENTS_PATH) as f:
        return json.load(f)


def _save_patients(data: list[dict]) -> None:
    with open(_PATIENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _load_doctors() -> list[dict]:
    with open(_DOCTORS_PATH) as f:
        return json.load(f)


def _save_doctors(data: list[dict]) -> None:
    with open(_DOCTORS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="ChroniScan API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterPatientRequest(BaseModel):
    email: str
    password: str
    name: str
    age: int
    comorbidities: list[str] = []
    blood_glucose: float = 110.0
    serum_albumin: float = 3.8
    mobility_score: int = 7
    post_op_day: int = 0
    doctor_id: Optional[str] = None


class RegisterDoctorRequest(BaseModel):
    email: str
    password: str
    name: str
    specialty: str = "General Surgery"
    patient_ids: list[str] = []


class ScanRequest(BaseModel):
    area_cm2: float
    ryb_ratios: dict  # {"red": float, "yellow": float, "black": float}
    scan_day: Optional[int] = None


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.post("/api/auth/login")
def login(req: LoginRequest):
    ph = _hash(req.password)

    for p in _load_patients():
        if p.get("email", "").lower() == req.email.strip().lower():
            if p.get("password_hash") == ph:
                return _safe_patient(p)
            raise HTTPException(status_code=401, detail="Wrong password")

    for d in _load_doctors():
        if d.get("email", "").lower() == req.email.strip().lower():
            if d.get("password_hash") == ph:
                return _safe_doctor(d)
            raise HTTPException(status_code=401, detail="Wrong password")

    raise HTTPException(status_code=404, detail="No account found with that email")


@app.post("/api/auth/register/patient")
def register_patient(req: RegisterPatientRequest):
    patients = _load_patients()
    if any(p.get("email", "").lower() == req.email.lower() for p in patients):
        raise HTTPException(status_code=409, detail="Email already registered")

    new_patient = {
        "patient_id":     f"P{uuid.uuid4().hex[:6].upper()}",
        "role":           "patient",
        "name":           req.name.strip(),
        "email":          req.email.strip().lower(),
        "password_hash":  _hash(req.password),
        "age":            req.age,
        "comorbidities":  req.comorbidities,
        "blood_glucose":  req.blood_glucose,
        "serum_albumin":  req.serum_albumin,
        "mobility_score": req.mobility_score,
        "post_op_day":    req.post_op_day,
        "doctor_id":      req.doctor_id,
        "wound_history":  [],
        "imported_history": {},
    }
    patients.append(new_patient)
    _save_patients(patients)
    return _safe_patient(new_patient)


@app.post("/api/auth/register/doctor")
def register_doctor(req: RegisterDoctorRequest):
    doctors = _load_doctors()
    if any(d.get("email", "").lower() == req.email.lower() for d in doctors):
        raise HTTPException(status_code=409, detail="Email already registered")

    new_doctor = {
        "doctor_id":    f"D{uuid.uuid4().hex[:6].upper()}",
        "role":         "doctor",
        "name":         req.name.strip(),
        "email":        req.email.strip().lower(),
        "password_hash": _hash(req.password),
        "specialty":    req.specialty,
        "patient_ids":  req.patient_ids,
    }
    doctors.append(new_doctor)
    _save_doctors(doctors)
    return _safe_doctor(new_doctor)


# ---------------------------------------------------------------------------
# Patient routes
# ---------------------------------------------------------------------------

@app.get("/api/patients")
def get_all_patients():
    return [_safe_patient(p) for p in _load_patients()]


@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: str):
    for p in _load_patients():
        if p["patient_id"] == patient_id:
            return _safe_patient(p)
    raise HTTPException(status_code=404, detail="Patient not found")


@app.get("/api/patients/{patient_id}/analysis")
def get_patient_analysis(patient_id: str):
    patients = _load_patients()
    patient = next((p for p in patients if p["patient_id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    history = patient.get("wound_history", [])
    if not history:
        raise HTTPException(status_code=404, detail="No wound history")

    latest = history[-1]
    # area delta vs previous scan
    if len(history) >= 2:
        area_delta = latest["area_cm2"] - history[-2]["area_cm2"]
    else:
        area_delta = 0.0

    result = evaluate_healing(
        area_delta=area_delta,
        tissue_ratios=latest["ryb_ratios"],
        health_data=patient,
    )
    return {
        "area_cm2":   latest["area_cm2"],
        "area_delta": area_delta,
        "ryb_ratios": latest["ryb_ratios"],
        "scan_date":  latest["date"],
        **result,
    }


@app.post("/api/patients/{patient_id}/scan")
def add_scan(patient_id: str, req: ScanRequest):
    patients = _load_patients()
    for p in patients:
        if p["patient_id"] == patient_id:
            scan_entry = {
                "date":      str(date.today()),
                "area_cm2":  req.area_cm2,
                "ryb_ratios": req.ryb_ratios,
            }
            p.setdefault("wound_history", []).append(scan_entry)
            _save_patients(patients)

            # Run KG analysis immediately
            history = p["wound_history"]
            area_delta = req.area_cm2 - history[-2]["area_cm2"] if len(history) >= 2 else 0.0
            kg_result = evaluate_healing(
                area_delta=area_delta,
                tissue_ratios=req.ryb_ratios,
                health_data=p,
            )
            return {
                "area_cm2":   req.area_cm2,
                "area_delta": area_delta,
                "ryb_ratios": req.ryb_ratios,
                "scan_date":  scan_entry["date"],
                **kg_result,
            }
    raise HTTPException(status_code=404, detail="Patient not found")


# ---------------------------------------------------------------------------
# Doctor routes
# ---------------------------------------------------------------------------

@app.get("/api/doctors/{doctor_id}")
def get_doctor(doctor_id: str):
    for d in _load_doctors():
        if d["doctor_id"] == doctor_id:
            return _safe_doctor(d)
    raise HTTPException(status_code=404, detail="Doctor not found")


@app.get("/api/doctors/{doctor_id}/patients")
def get_doctor_patients(doctor_id: str):
    doctor = next((d for d in _load_doctors() if d["doctor_id"] == doctor_id), None)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    pids = set(doctor.get("patient_ids", []))
    result = []
    for p in _load_patients():
        if p["patient_id"] in pids:
            # Include latest analysis summary
            history = p.get("wound_history", [])
            latest  = history[-1] if history else None
            if latest and len(history) >= 2:
                area_delta = latest["area_cm2"] - history[-2]["area_cm2"]
            else:
                area_delta = 0.0

            summary = {}
            if latest:
                kg = evaluate_healing(
                    area_delta=area_delta,
                    tissue_ratios=latest["ryb_ratios"],
                    health_data=p,
                )
                summary = {
                    "priority":   kg["priority"],
                    "area_cm2":   latest["area_cm2"],
                    "area_delta": area_delta,
                    "ryb_ratios": latest["ryb_ratios"],
                    "scan_date":  latest["date"],
                    "alerts":     kg["alerts"],
                }
            result.append({**_safe_patient(p), "latest_summary": summary})
    return result


@app.post("/api/doctors/{doctor_id}/patients/{patient_id}")
def add_patient_to_doctor(doctor_id: str, patient_id: str):
    doctors = _load_doctors()
    patients = _load_patients()
    if not any(p["patient_id"] == patient_id for p in patients):
        raise HTTPException(status_code=404, detail="Patient not found")
    for d in doctors:
        if d["doctor_id"] == doctor_id:
            pids = d.setdefault("patient_ids", [])
            if patient_id not in pids:
                pids.append(patient_id)
                _save_doctors(doctors)
            return _safe_doctor(d)
    raise HTTPException(status_code=404, detail="Doctor not found")


@app.delete("/api/doctors/{doctor_id}/patients/{patient_id}")
def remove_patient_from_doctor(doctor_id: str, patient_id: str):
    doctors = _load_doctors()
    for d in doctors:
        if d["doctor_id"] == doctor_id:
            pids = d.get("patient_ids", [])
            if patient_id in pids:
                pids.remove(patient_id)
                _save_doctors(doctors)
            return _safe_doctor(d)
    raise HTTPException(status_code=404, detail="Doctor not found")


@app.get("/api/doctors")
def get_all_doctors():
    return [_safe_doctor(d) for d in _load_doctors()]


# ---------------------------------------------------------------------------
# Helpers — strip password_hash before sending to frontend
# ---------------------------------------------------------------------------

def _safe_patient(p: dict) -> dict:
    return {k: v for k, v in p.items() if k != "password_hash"}


def _safe_doctor(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "password_hash"}


# ---------------------------------------------------------------------------
# Vision scan route
# ---------------------------------------------------------------------------

@app.post("/api/scan/analyze")
async def vision_analyze(
    patient_id: str = Form(...),
    file: UploadFile = File(None),
):
    """Accept an uploaded wound image (or use demo), run CV pipeline + KG."""
    from vision import analyze_frame, analyze_patient

    patient = next((p for p in _load_patients() if p["patient_id"] == patient_id), None)

    if file and file.filename:
        raw = await file.read()
        arr = np.frombuffer(raw, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        vision_result = analyze_frame(frame)
    else:
        # Demo mode: synthesize image from latest stored scan
        if not patient or not patient.get("wound_history"):
            raise HTTPException(
                status_code=400,
                detail="No wound history found. Please upload a real image for the first scan.",
            )
        vision_result = analyze_patient(patient_id, patient_data=patient)

    annotated = vision_result.get("annotated_image")
    img_b64 = ""
    if annotated is not None:
        _, jpeg = cv2.imencode(".jpg", annotated)
        img_b64 = base64.b64encode(jpeg.tobytes()).decode()

    # Area delta vs last stored scan
    history = patient.get("wound_history", []) if patient else []
    area_cm2 = vision_result.get("area_cm2", 0.0)
    area_delta = area_cm2 - history[-1]["area_cm2"] if history else 0.0

    ryb = vision_result.get("ryb_ratios", {"red": 0.0, "yellow": 0.0, "black": 0.0})

    kg_result = evaluate_healing(
        area_delta=area_delta,
        tissue_ratios=ryb,
        health_data=patient or {},
    )

    return {
        "area_cm2":           area_cm2,
        "area_delta":         area_delta,
        "ryb_ratios":         ryb,
        "coin_found":         vision_result.get("coin_found", False),
        "annotated_image_b64": img_b64,
        **kg_result,
    }
