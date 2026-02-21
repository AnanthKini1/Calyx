"""
run_demo.py — ChroniScan Knowledge Graph Demo

Loads each mock patient, runs evaluate_healing(), and prints
a formatted clinical report. Use this as the integration test
and as the demo script for presentations.

Usage:
    python run_demo.py
"""

from data.mock_patients import PATIENTS, get_latest_wound_data, compute_area_delta
from knowledge_graph import evaluate_healing

SEPARATOR = "=" * 62
DIVIDER   = "-" * 62

PRIORITY_ICON = {
    "CRITICAL": "🚨 CRITICAL",
    "HIGH":     "⚠️  HIGH",
    "MEDIUM":   "🔶 MEDIUM",
    "LOW":      "🔵 LOW",
    "OK":       "✅ OK",
}


def print_patient_report(patient: dict, result: dict, area_delta: float) -> None:
    """Print a formatted clinical summary block for one patient."""
    latest = get_latest_wound_data(patient)
    ryb    = latest["ryb_ratios"]

    print(SEPARATOR)
    print(
        f"PATIENT: {patient['name']} ({patient['patient_id']}) | "
        f"Age: {patient['age']} | Post-Op Day: {patient['post_op_day']}"
    )
    print(f"Comorbidities: {', '.join(patient['comorbidities']) or 'None'}")
    print(
        f"Blood Glucose: {patient['blood_glucose']:.1f} mg/dL | "
        f"Albumin: {patient['serum_albumin']:.1f} g/dL | "
        f"Mobility: {patient['mobility_score']}/10"
    )

    print(DIVIDER)
    print("LATEST WOUND SCAN:")
    delta_sign = "+" if area_delta >= 0 else ""
    print(f"  Area Change (7d): {delta_sign}{area_delta:.2f} cm²")
    print(
        f"  Tissue: "
        f"Red {ryb['red']:.0f}% | "
        f"Yellow {ryb['yellow']:.0f}% | "
        f"Black {ryb['black']:.0f}%"
    )

    print(DIVIDER)
    priority_label = PRIORITY_ICON.get(result["priority"], result["priority"])
    print(f"CLINICAL ASSESSMENT: [{priority_label}]")

    print("ALERTS:")
    for alert in result["alerts"]:
        print(f"  [!] {alert}")

    if result["active_risk_factors"]:
        print(f"ACTIVE RISK FACTORS: {', '.join(result['active_risk_factors'])}")

    print("REASONING:")
    # Word-wrap reasoning at ~58 chars for terminal readability
    words  = result["reasoning"].split()
    line   = "  "
    for word in words:
        if len(line) + len(word) + 1 > 60:
            print(line)
            line = "  " + word
        else:
            line = line + " " + word if line.strip() else "  " + word
    if line.strip():
        print(line)

    print(f"RECOMMENDED ACTION:")
    print(f"  >> {result['recommended_action']}")
    print(SEPARATOR)
    print()


def main() -> None:
    print()
    print("ChroniScan — Knowledge Graph Clinical Assessment Demo")
    print(f"Running assessment for {len(PATIENTS)} patients...\n")

    for patient in PATIENTS:
        area_delta = compute_area_delta(patient, n_days=7)
        latest     = get_latest_wound_data(patient)

        result = evaluate_healing(
            area_delta=area_delta,
            tissue_ratios=latest["ryb_ratios"],
            health_data=patient,
        )

        print_patient_report(patient, result, area_delta)


if __name__ == "__main__":
    main()
