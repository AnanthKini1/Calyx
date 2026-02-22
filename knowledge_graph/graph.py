"""
graph.py — ChroniScan Clinical Knowledge Graph.

Encodes evidence-based relationships between patient comorbidities,
biomarker states, and wound healing outcomes as a directed NetworkX graph.
Edge weights represent clinical evidence strength (0.0–1.0).
"""

from __future__ import annotations

import networkx as nx

# ---------------------------------------------------------------------------
# Node taxonomy constants
# ---------------------------------------------------------------------------

CONDITION_NODES = [
    "Type_2_Diabetes",
    "Obesity",
    "Hypertension",
    "Peripheral_Artery_Disease",
    "Malnutrition",
    "Low_Mobility",
]

BIOMARKER_NODES = [
    "Hyperglycemia",        # blood_glucose > 180 mg/dL
    "Low_Serum_Albumin",    # serum_albumin < 3.0 g/dL
    "High_BMI",             # proxy for Obesity comorbidity
    "Poor_Perfusion",       # proxy for Peripheral Artery Disease
]

OUTCOME_NODES = [
    "Wound_Stagnation",
    "Infection_Risk",
    "Delayed_Healing",
    "Necrosis_Risk",
]

# Maps human-readable comorbidity strings (from patient profiles) → graph node IDs
COMORBIDITY_TO_NODE: dict[str, str] = {
    "Type 2 Diabetes":           "Type_2_Diabetes",
    "Obesity":                   "Obesity",
    "Hypertension":              "Hypertension",
    "Peripheral Artery Disease": "Peripheral_Artery_Disease",
    "Malnutrition":              "Malnutrition",
    "Low_Mobility":              "Low_Mobility",
}

# Module-level cache — graph is built once and reused
_GRAPH_CACHE: nx.DiGraph | None = None


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def _build() -> nx.DiGraph:
    """Internal builder — constructs the clinical knowledge DiGraph."""
    G = nx.DiGraph()

    # Add condition nodes
    for node in CONDITION_NODES:
        G.add_node(node, type="condition", description=node.replace("_", " "))

    # Add biomarker nodes
    for node in BIOMARKER_NODES:
        G.add_node(node, type="biomarker", description=node.replace("_", " "))

    # Add outcome nodes
    for node in OUTCOME_NODES:
        G.add_node(node, type="outcome", description=node.replace("_", " "))

    # ------------------------------------------------------------------
    # Edges: Conditions → Biomarkers
    # ------------------------------------------------------------------
    G.add_edge("Type_2_Diabetes", "Hyperglycemia",
               weight=0.95, label="causes_chronic_hyperglycemia")
    G.add_edge("Type_2_Diabetes", "Low_Serum_Albumin",
               weight=0.60, label="impairs_protein_synthesis")
    G.add_edge("Obesity", "High_BMI",
               weight=1.00, label="defines")
    G.add_edge("Obesity", "Low_Serum_Albumin",
               weight=0.45, label="associated_with_malnutrition")
    G.add_edge("Malnutrition", "Low_Serum_Albumin",
               weight=0.95, label="directly_causes")
    G.add_edge("Peripheral_Artery_Disease", "Poor_Perfusion",
               weight=0.90, label="reduces_tissue_oxygenation")

    # ------------------------------------------------------------------
    # Edges: Conditions → Outcomes (direct, strong evidence)
    # ------------------------------------------------------------------
    G.add_edge("Low_Mobility", "Wound_Stagnation",
               weight=0.70, label="reduces_offloading_and_perfusion")
    G.add_edge("Hypertension", "Wound_Stagnation",
               weight=0.40, label="microvascular_disease")
    G.add_edge("Type_2_Diabetes", "Delayed_Healing",
               weight=0.80, label="multi_mechanism_impairment")

    # ------------------------------------------------------------------
    # Edges: Biomarkers → Outcomes
    # ------------------------------------------------------------------
    G.add_edge("Hyperglycemia", "Wound_Stagnation",
               weight=0.85, label="impairs_neutrophil_function")
    G.add_edge("Hyperglycemia", "Infection_Risk",
               weight=0.80, label="promotes_bacterial_growth")
    G.add_edge("Hyperglycemia", "Delayed_Healing",
               weight=0.85, label="inhibits_collagen_synthesis")
    G.add_edge("Low_Serum_Albumin", "Delayed_Healing",
               weight=0.80, label="insufficient_tissue_repair_substrate")
    G.add_edge("Low_Serum_Albumin", "Wound_Stagnation",
               weight=0.75, label="reduces_oncotic_pressure")
    G.add_edge("High_BMI", "Wound_Stagnation",
               weight=0.65, label="increases_wound_tension")
    G.add_edge("High_BMI", "Infection_Risk",
               weight=0.60, label="adipose_tissue_hypoxia")
    G.add_edge("Poor_Perfusion", "Necrosis_Risk",
               weight=0.90, label="tissue_ischemia")
    G.add_edge("Poor_Perfusion", "Delayed_Healing",
               weight=0.85, label="insufficient_oxygen_delivery")

    return G


def build_graph() -> nx.DiGraph:
    """
    Construct and return the clinical knowledge DiGraph.
    Results are cached — the graph is built only once per process.
    """
    global _GRAPH_CACHE
    if _GRAPH_CACHE is None:
        _GRAPH_CACHE = _build()
    return _GRAPH_CACHE


# ---------------------------------------------------------------------------
# Patient-specific graph traversal
# ---------------------------------------------------------------------------

def get_risk_factors(patient_data: dict, G: nx.DiGraph | None = None) -> list[str]:
    """
    Traverse the knowledge graph for a given patient and return
    the OUTCOME node IDs reachable from the patient's active nodes.

    Algorithm:
    1. Map comorbidities and biomarker thresholds → active graph nodes
    2. BFS from each active node (max depth 2) to find reachable OUTCOME nodes
    3. Return deduplicated outcomes sorted by cumulative edge weight (highest first)

    Parameters
    ----------
    patient_data : dict
        Patient profile dict from mock_patients.py
    G : nx.DiGraph, optional
        Pre-built graph (uses cached build_graph() if omitted)

    Returns
    -------
    list[str]
        Outcome node IDs ordered by activation strength
    """
    if G is None:
        G = build_graph()

    comorbidities = patient_data.get("comorbidities", [])
    blood_glucose  = patient_data.get("blood_glucose", 0.0)
    serum_albumin  = patient_data.get("serum_albumin", 4.0)
    mobility_score = patient_data.get("mobility_score", 10)

    # Step 1: Build set of active starting nodes
    active_nodes: set[str] = set()

    # Map comorbidities
    for comorbidity in comorbidities:
        node_id = COMORBIDITY_TO_NODE.get(comorbidity)
        if node_id and node_id in G:
            active_nodes.add(node_id)

    # Activate biomarker nodes based on thresholds
    if blood_glucose > 180:
        active_nodes.add("Hyperglycemia")
    if serum_albumin < 3.0:
        active_nodes.add("Low_Serum_Albumin")
    if "Obesity" in comorbidities:
        active_nodes.add("High_BMI")
    if "Peripheral Artery Disease" in comorbidities:
        active_nodes.add("Poor_Perfusion")
    if mobility_score < 4:
        active_nodes.add("Low_Mobility")

    # Step 2: BFS up to depth 2 from each active node, collect OUTCOME nodes
    # Track cumulative weight for each reached outcome
    outcome_weights: dict[str, float] = {}

    for start_node in active_nodes:
        if start_node not in G:
            continue

        # BFS: (node, depth, cumulative_weight)
        queue = [(start_node, 0, 1.0)]
        visited = {start_node}

        while queue:
            current, depth, cumulative_weight = queue.pop(0)

            node_type = G.nodes[current].get("type", "")
            if node_type == "outcome":
                outcome_weights[current] = max(
                    outcome_weights.get(current, 0.0),
                    cumulative_weight,
                )

            if depth < 2:
                for neighbor in G.successors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        edge_weight = G[current][neighbor].get("weight", 0.5)
                        queue.append((neighbor, depth + 1, cumulative_weight * edge_weight))

    # Step 3: Return outcome IDs sorted by activation weight descending
    return sorted(outcome_weights.keys(), key=lambda n: outcome_weights[n], reverse=True)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def get_graph_summary(G: nx.DiGraph) -> dict:
    """Return a summary dict of the knowledge graph for debugging/display."""
    return {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "condition_nodes": [n for n, d in G.nodes(data=True) if d.get("type") == "condition"],
        "biomarker_nodes": [n for n, d in G.nodes(data=True) if d.get("type") == "biomarker"],
        "outcome_nodes":   [n for n, d in G.nodes(data=True) if d.get("type") == "outcome"],
    }
