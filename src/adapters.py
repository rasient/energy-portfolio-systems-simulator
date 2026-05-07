from __future__ import annotations
import pandas as pd

def create_pypsa_export_preview(payload: dict) -> dict:
    """Adapter-ready placeholder for future PyPSA integration."""
    generation = payload.get("generation_mix", {})
    storage = payload.get("storage_mix", {})
    return {
        "framework": "PyPSA",
        "status": "placeholder_export_ready",
        "note": "This structure can later be converted into pypsa.Network components.",
        "network_components": {
            "buses": ["electricity_bus"],
            "generators": [{"name": k, "p_nom_relative": v} for k, v in generation.items()],
            "stores": [{"name": k, "capacity_relative": v} for k, v in storage.items()],
            "loads": [{"name": "demand", "growth_assumption": payload.get("demand_growth", 0)}],
        },
    }

def create_oemof_export_preview(payload: dict) -> dict:
    """Adapter-ready placeholder for future oemof integration."""
    return {
        "framework": "oemof",
        "status": "placeholder_export_ready",
        "note": "This structure can later be mapped to oemof.solph energy system objects.",
        "energy_system": {
            "sources": payload.get("generation_mix", {}),
            "storages": payload.get("storage_mix", {}),
            "constraints": {
                "stress_test": payload.get("stress_test"),
                "dependency_sensitivity": payload.get("dependency_sensitivity"),
                "water_stress": payload.get("water_stress"),
            },
        },
    }

def simulated_external_results(payload: dict) -> pd.DataFrame:
    results = payload.get("results", {})
    rows = [
        {"Model": "Internal visual model", "Cost": results.get("cost_index", 0), "Emissions": results.get("emissions_index", 0), "Resilience": results.get("resilience", 0)},
        {"Model": "PyPSA placeholder", "Cost": min(100, results.get("cost_index", 0)*0.94+4), "Emissions": min(100, results.get("emissions_index", 0)*0.97+2), "Resilience": max(0, results.get("resilience", 0)*1.02-1)},
        {"Model": "oemof placeholder", "Cost": min(100, results.get("cost_index", 0)*0.96+3), "Emissions": min(100, results.get("emissions_index", 0)*0.95+3), "Resilience": max(0, results.get("resilience", 0)*1.01)},
    ]
    return pd.DataFrame(rows)
