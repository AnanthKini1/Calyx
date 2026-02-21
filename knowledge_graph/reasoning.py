"""
reasoning.py — ChroniScan Clinical Reasoning Engine.

Evaluates wound healing status using rule-based logic combined with
knowledge graph traversal. Returns a structured result dict suitable
for direct consumption by the Streamlit frontend.

Priority hierarchy (highest wins):
  CRITICAL > HIGH > MEDIUM > LOW > OK

All triggered alerts are collected (no short-circuit) so clinicians
see the full picture even for CRITICAL wounds.
"""

from .graph import get_risk_factors

# ---------------------------------------------------------------------------
# Priority ordering (index = severity rank, 0 = highest)
# ---------------------------------------------------------------------------

PRIORITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "OK"]


def _priority_rank(p: str) -> int:
    """Lower rank = higher severity."""
    return PRIORITY_ORDER.index(p) if p in PRIORITY_ORDER else len(PRIORITY_ORDER)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _classify_tissue_state(tissue_ratios: dict) -> str:
    """Return a plain-English description of the tissue composition."""
    red    = tissue_ratios.get("red", 0.0)
    yellow = tissue_ratios.get("yellow", 0.0)
    black  = tissue_ratios.get("black", 0.0)

    dominant = max(tissue_ratios, key=tissue_ratios.get)
    label = {"red": "granulating", "yellow": "slough-dominant", "black": "eschar-dominant"}.get(dominant, "mixed")
    return f"predominantly {label} (red {red:.0f}%, yellow {yellow:.0f}%, black {black:.0f}%)"


def _format_area_trend(area_delta: float) -> str:
    """Describe area change in plain English."""
    if area_delta < -0.1:
        return f"shrinking by {abs(area_delta):.2f} cm²"
    elif area_delta > 0.1:
        return f"stalled/growing by +{area_delta:.2f} cm²"
    else:
        return "essentially unchanged (±0.1 cm²)"


def _build_reasoning(
    priority: str,
    alerts: list[str],
    active_risk_factors: list[str],
    health_data: dict,
    area_delta: float,
    tissue_ratios: dict,
) -> str:
    """Compose a human-readable clinical explanation paragraph."""
    name        = health_data.get("name", "Patient")
    post_op_day = health_data.get("post_op_day", 0)
    glucose     = health_data.get("blood_glucose", 0.0)
    albumin     = health_data.get("serum_albumin", 0.0)

    tissue_desc  = _classify_tissue_state(tissue_ratios)
    area_desc    = _format_area_trend(area_delta)
    risks_desc   = ", ".join(active_risk_factors) if active_risk_factors else "none identified"

    parts = [
        f"{name} presents at post-op day {post_op_day} with wound area {area_desc}.",
        f"Tissue analysis is {tissue_desc}.",
        f"Blood glucose is {glucose:.1f} mg/dL; serum albumin is {albumin:.1f} g/dL.",
    ]

    if active_risk_factors:
        parts.append(
            f"Active comorbidity risk factors identified by the knowledge graph: {risks_desc}."
        )

    if priority == "CRITICAL":
        parts.append("Immediate clinical escalation is required.")
    elif priority == "HIGH":
        parts.append("Prompt intervention is recommended to prevent deterioration.")
    elif priority in ("MEDIUM", "LOW"):
        parts.append("Ongoing monitoring and targeted supportive care are indicated.")
    else:
        parts.append("Continue current treatment plan.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Core evaluation function
# ---------------------------------------------------------------------------

def evaluate_healing(
    area_delta: float,
    tissue_ratios: dict,
    health_data: dict,
) -> dict:
    """
    Evaluate wound healing status using rule-based clinical logic
    combined with knowledge graph risk factor traversal.

    Parameters
    ----------
    area_delta : float
        Change in wound area (cm²) since last measurement window.
        Negative = shrinking (healing). Positive/zero = stalling/growing.
    tissue_ratios : dict
        RYB tissue composition from computer vision.
        Keys: "red" (granulation), "yellow" (slough), "black" (eschar).
        Values are percentages.
    health_data : dict
        Full patient profile dict from mock_patients.py.

    Returns
    -------
    dict with keys:
        "priority"            : str
        "alerts"              : list[str]
        "reasoning"           : str
        "active_risk_factors" : list[str]
        "recommended_action"  : str
    """
    # Extract values with safe defaults
    black          = tissue_ratios.get("black", 0.0)
    yellow         = tissue_ratios.get("yellow", 0.0)
    red            = tissue_ratios.get("red", 0.0)
    blood_glucose  = health_data.get("blood_glucose", 0.0)
    serum_albumin  = health_data.get("serum_albumin", 4.0)
    mobility_score = health_data.get("mobility_score", 5)
    post_op_day    = health_data.get("post_op_day", 0)

    # -----------------------------------------------------------------------
    # Evaluate all 7 rules — collect (priority_rank, alert_str, action_str)
    # -----------------------------------------------------------------------
    triggered: list[tuple[int, str, str]] = []

    # Rule 1 — CRITICAL: necrotic tissue
    if black > 15:
        triggered.append((
            _priority_rank("CRITICAL"),
            "Critical: Necrotic tissue detected",
            "Urgent surgical debridement consult required",
        ))

    # Rule 2 — HIGH: wound stall with slough
    if area_delta >= 0 and yellow > 10:
        triggered.append((
            _priority_rank("HIGH"),
            "High Priority: Wound Stall",
            "Assess wound bed — debridement and dressing change protocol",
        ))

    # Rule 3 — HIGH: hyperglycemia impeding healing
    if blood_glucose > 180 and area_delta >= 0:
        triggered.append((
            _priority_rank("HIGH"),
            "High Priority: Hyperglycemia Impeding Healing",
            "Notify endocrinology — tighten glycemic control target",
        ))

    # Rule 4 — MEDIUM: nutritional deficiency
    if serum_albumin < 3.0:
        triggered.append((
            _priority_rank("MEDIUM"),
            "Medium: Nutritional Deficiency — consult dietitian",
            "Initiate high-protein supplementation, dietitian referral",
        ))

    # Rule 5 — MEDIUM: low mobility
    if mobility_score < 4:
        triggered.append((
            _priority_rank("MEDIUM"),
            "Medium: Low Mobility — increase repositioning protocol",
            "2-hour repositioning schedule, pressure-relief mattress",
        ))

    # Rule 6 — LOW: delayed granulation
    if post_op_day > 14 and red < 60:
        triggered.append((
            _priority_rank("LOW"),
            "Low: Delayed Granulation — monitor closely",
            "Consider moist wound therapy optimization and follow-up in 48h",
        ))

    # Rule 7 — OK: fallthrough
    if not triggered:
        triggered.append((
            _priority_rank("OK"),
            "On Track: Healing within expected parameters",
            "Continue current treatment plan, next scan in 7 days",
        ))

    # -----------------------------------------------------------------------
    # Resolve priority and assemble output
    # -----------------------------------------------------------------------
    # Sort so highest severity (lowest rank index) is first
    triggered.sort(key=lambda t: t[0])

    highest_rank, _, highest_action = triggered[0]
    priority = PRIORITY_ORDER[highest_rank]
    alerts   = [alert for _, alert, _ in triggered]

    # Knowledge graph risk factor traversal
    active_risk_factors = get_risk_factors(health_data)

    reasoning = _build_reasoning(
        priority=priority,
        alerts=alerts,
        active_risk_factors=active_risk_factors,
        health_data=health_data,
        area_delta=area_delta,
        tissue_ratios=tissue_ratios,
    )

    return {
        "priority":            priority,
        "alerts":              alerts,
        "reasoning":           reasoning,
        "active_risk_factors": active_risk_factors,
        "recommended_action":  highest_action,
    }
