"""
mock_patients.py — ChroniScan mock patient data layer.

Simulates patient health profiles with wound scan history.
Replaces real APIs (Dexcom, lab results, accelerometers) with
realistic clinical scenarios for demo/development purposes.
"""

from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Mock patient dataset
# ---------------------------------------------------------------------------

PATIENTS = [
    {
        "patient_id": "P001",
        "name": "Maria Santos",
        "age": 54,
        "comorbidities": ["Hypertension"],
        "blood_glucose": 112.0,     # mg/dL — normal
        "serum_albumin": 3.8,       # g/dL — adequate nutrition
        "mobility_score": 7,        # 0–10 accelerometer proxy — active
        "post_op_day": 10,
        "wound_history": [
            {
                "date": "2026-02-11",
                "area_cm2": 8.2,
                "ryb_ratios": {"red": 42.0, "yellow": 38.0, "black": 20.0},
            },
            {
                "date": "2026-02-13",
                "area_cm2": 6.9,
                "ryb_ratios": {"red": 52.0, "yellow": 32.0, "black": 16.0},
            },
            {
                "date": "2026-02-16",
                "area_cm2": 5.4,
                "ryb_ratios": {"red": 63.0, "yellow": 28.0, "black": 9.0},
            },
            {
                "date": "2026-02-18",
                "area_cm2": 4.1,
                "ryb_ratios": {"red": 72.0, "yellow": 22.0, "black": 6.0},
            },
            {
                "date": "2026-02-21",
                "area_cm2": 3.1,
                "ryb_ratios": {"red": 78.0, "yellow": 18.0, "black": 4.0},
            },
        ],
    },
    {
        "patient_id": "P002",
        "name": "James Okafor",
        "age": 67,
        "comorbidities": ["Type 2 Diabetes", "Obesity", "Hypertension"],
        "blood_glucose": 224.0,     # mg/dL — hyperglycemic
        "serum_albumin": 2.4,       # g/dL — malnourished
        "mobility_score": 2,        # sedentary
        "post_op_day": 21,
        "wound_history": [
            {
                "date": "2026-01-31",
                "area_cm2": 12.1,
                "ryb_ratios": {"red": 55.0, "yellow": 32.0, "black": 13.0},
            },
            {
                "date": "2026-02-04",
                "area_cm2": 13.4,   # growing — bad sign
                "ryb_ratios": {"red": 52.0, "yellow": 34.0, "black": 14.0},
            },
            {
                "date": "2026-02-09",
                "area_cm2": 12.8,
                "ryb_ratios": {"red": 51.0, "yellow": 31.0, "black": 18.0},
            },
            {
                "date": "2026-02-15",
                "area_cm2": 13.1,
                "ryb_ratios": {"red": 53.0, "yellow": 28.0, "black": 19.0},
            },
            {
                "date": "2026-02-21",
                "area_cm2": 13.5,   # oscillating / not healing
                "ryb_ratios": {"red": 58.0, "yellow": 24.0, "black": 18.0},
            },
        ],
    },
    {
        "patient_id": "P003",
        "name": "Linda Chu",
        "age": 61,
        "comorbidities": ["Type 2 Diabetes"],
        "blood_glucose": 155.0,     # mg/dL — borderline
        "serum_albumin": 3.2,       # g/dL — borderline
        "mobility_score": 3,        # low
        "post_op_day": 16,
        "wound_history": [
            {
                "date": "2026-02-05",
                "area_cm2": 9.5,
                "ryb_ratios": {"red": 44.0, "yellow": 41.0, "black": 15.0},
            },
            {
                "date": "2026-02-09",
                "area_cm2": 8.9,
                "ryb_ratios": {"red": 48.0, "yellow": 38.0, "black": 14.0},
            },
            {
                "date": "2026-02-13",
                "area_cm2": 8.4,
                "ryb_ratios": {"red": 51.0, "yellow": 36.0, "black": 13.0},
            },
            {
                "date": "2026-02-17",
                "area_cm2": 8.1,
                "ryb_ratios": {"red": 53.0, "yellow": 35.0, "black": 12.0},
            },
            {
                "date": "2026-02-21",
                "area_cm2": 7.8,
                "ryb_ratios": {"red": 55.0, "yellow": 33.0, "black": 12.0},
                # red < 60% at post_op_day 16 → Delayed Granulation (LOW)
            },
        ],
    },
    {
        "patient_id": "P004",
        "name": "Robert Vance",
        "age": 73,
        "comorbidities": ["Type 2 Diabetes", "Peripheral Artery Disease", "Obesity"],
        "blood_glucose": 198.0,     # mg/dL — hyperglycemic
        "serum_albumin": 2.7,       # g/dL — low
        "mobility_score": 1,        # nearly immobile
        "post_op_day": 8,
        "wound_history": [
            {
                "date": "2026-02-13",
                "area_cm2": 15.3,
                "ryb_ratios": {"red": 60.0, "yellow": 32.0, "black": 8.0},
            },
            {
                "date": "2026-02-16",
                "area_cm2": 15.9,
                "ryb_ratios": {"red": 55.0, "yellow": 29.0, "black": 16.0},
            },
            {
                "date": "2026-02-18",
                "area_cm2": 16.4,
                "ryb_ratios": {"red": 51.0, "yellow": 27.0, "black": 22.0},
            },
            {
                "date": "2026-02-21",
                "area_cm2": 17.1,
                "ryb_ratios": {"red": 47.0, "yellow": 31.0, "black": 22.0},
                # black 22% >> 15% threshold → CRITICAL
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_patient_by_id(patient_id: str) -> dict | None:
    """Return a single patient dict by ID, or None if not found."""
    for patient in PATIENTS:
        if patient["patient_id"] == patient_id:
            return patient
    return None


def get_latest_wound_data(patient: dict) -> dict:
    """Return the most recent wound_history entry."""
    return patient["wound_history"][-1]


def compute_area_delta(patient: dict, n_days: int = 7) -> float:
    """
    Compute signed change in wound area over the last n_days.

    Searches backwards from the most recent entry to find the oldest
    entry within the n_days window. If only one entry exists, returns 0.0.

    Negative value = wound is shrinking (healing).
    Positive value = wound is stalling or growing.
    """
    history = patient["wound_history"]
    if len(history) < 2:
        return 0.0

    latest = history[-1]
    latest_date = date.fromisoformat(latest["date"])
    cutoff_date = latest_date - timedelta(days=n_days)

    # Find oldest entry within the window
    baseline = None
    for entry in history:
        entry_date = date.fromisoformat(entry["date"])
        if entry_date >= cutoff_date and entry is not latest:
            if baseline is None or entry_date < date.fromisoformat(baseline["date"]):
                baseline = entry

    if baseline is None:
        # All entries are outside window; use the second-to-last as fallback
        baseline = history[-2]

    return latest["area_cm2"] - baseline["area_cm2"]
