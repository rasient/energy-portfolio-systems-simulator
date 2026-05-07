from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
import math
import pandas as pd

from .utils import clamp, normalize_weights
from .scenarios import PRIORITIES, STRESS_TESTS

TECH_PROFILES = {
    "Solar": {"cost": 38, "emissions": 8, "reliability": 45, "dependency": 25, "flexibility": 35, "water": 8, "transport": 12},
    "Wind": {"cost": 42, "emissions": 10, "reliability": 48, "dependency": 30, "flexibility": 40, "water": 5, "transport": 15},
    "Nuclear": {"cost": 70, "emissions": 6, "reliability": 92, "dependency": 55, "flexibility": 35, "water": 72, "transport": 25},
    "Gas": {"cost": 58, "emissions": 72, "reliability": 82, "dependency": 78, "flexibility": 75, "water": 25, "transport": 45},
    "Hydro": {"cost": 45, "emissions": 12, "reliability": 78, "dependency": 20, "flexibility": 82, "water": 90, "transport": 18},
    "Geothermal": {"cost": 62, "emissions": 9, "reliability": 80, "dependency": 25, "flexibility": 60, "water": 45, "transport": 14},
    "Biomass": {"cost": 55, "emissions": 35, "reliability": 70, "dependency": 40, "flexibility": 65, "water": 58, "transport": 50},
}

STORAGE_PROFILES = {
    "Battery": {"flexibility": 88, "duration": 35, "cost": 68, "dependency": 60},
    "Pumped hydro": {"flexibility": 76, "duration": 72, "cost": 55, "dependency": 20},
    "Hydrogen": {"flexibility": 58, "duration": 90, "cost": 78, "dependency": 45},
}

ACTOR_WEIGHTS = {
    "Government": {"cost": .18, "emissions": .22, "reliability": .20, "resilience": .22, "dependency": .18},
    "Grid operator": {"cost": .12, "emissions": .10, "reliability": .32, "resilience": .32, "dependency": .14},
    "Industrial sector": {"cost": .34, "emissions": .08, "reliability": .30, "resilience": .14, "dependency": .14},
    "Citizens": {"cost": .32, "emissions": .18, "reliability": .22, "resilience": .18, "dependency": .10},
    "Investors": {"cost": .30, "emissions": .12, "reliability": .18, "resilience": .16, "dependency": .24},
}

@dataclass
class SimulationInput:
    priority: str
    stress_test: str
    generation_mix: Dict[str, float]
    storage_mix: Dict[str, float]
    demand_growth: float
    dependency_sensitivity: float
    timeline_step: int = 20
    water_stress: float = 30
    transport_electrification: float = 25
    industrial_demand: float = 35
    geopolitical_tension: float = 35

def evaluate_system(config: SimulationInput) -> dict:
    gen_weights = normalize_weights(config.generation_mix)
    storage_weights = normalize_weights(config.storage_mix)
    stress = STRESS_TESTS[config.stress_test]
    priority_weights = PRIORITIES[config.priority]

    avg_cost = sum(gen_weights[t] * TECH_PROFILES[t]["cost"] for t in gen_weights)
    avg_emissions = sum(gen_weights[t] * TECH_PROFILES[t]["emissions"] for t in gen_weights)
    avg_reliability = sum(gen_weights[t] * TECH_PROFILES[t]["reliability"] for t in gen_weights)
    avg_dependency = sum(gen_weights[t] * TECH_PROFILES[t]["dependency"] for t in gen_weights)
    avg_flexibility = sum(gen_weights[t] * TECH_PROFILES[t]["flexibility"] for t in gen_weights)
    avg_water = sum(gen_weights[t] * TECH_PROFILES[t]["water"] for t in gen_weights)
    avg_transport = sum(gen_weights[t] * TECH_PROFILES[t]["transport"] for t in gen_weights)

    storage_capacity = sum(config.storage_mix.values())
    storage_flex = sum(storage_weights[t] * STORAGE_PROFILES[t]["flexibility"] for t in storage_weights) if storage_weights else 0
    storage_duration = sum(storage_weights[t] * STORAGE_PROFILES[t]["duration"] for t in storage_weights) if storage_weights else 0
    storage_cost = sum(storage_weights[t] * STORAGE_PROFILES[t]["cost"] for t in storage_weights) if storage_weights else 0
    storage_dependency = sum(storage_weights[t] * STORAGE_PROFILES[t]["dependency"] for t in storage_weights) if storage_weights else 0

    renewable_share = gen_weights.get("Solar", 0) + gen_weights.get("Wind", 0)
    baseload_share = gen_weights.get("Nuclear", 0) + gen_weights.get("Hydro", 0) + gen_weights.get("Geothermal", 0)
    gas_share = gen_weights.get("Gas", 0)

    timeline_wave = 0.08 * math.sin(config.timeline_step / 10 * math.pi)
    demand_factor = stress["demand"] + (config.demand_growth / 100) * 0.75 + config.transport_electrification / 500 + config.industrial_demand / 650

    renewable_gap = renewable_share * stress["renewable_penalty"] * 100
    gas_exposure = gas_share * stress["gas_penalty"] * 100

    storage_buffer = min(storage_capacity * 0.55, 48) + storage_flex * 0.18 + storage_duration * 0.08
    storage_pressure = clamp(stress["storage_pressure"] * 100 + renewable_gap - storage_buffer * 0.35 + timeline_wave * 100)
    transmission_pressure = clamp(stress["transmission_pressure"] * 100 + demand_factor * 18 + renewable_share * 24 - storage_buffer * 0.22 + timeline_wave * 70)
    backup_requirement = clamp(demand_factor * 35 + renewable_gap * 0.75 - baseload_share * 28 - storage_buffer * 0.25)
    reserve_margin = clamp(100 - backup_requirement - storage_pressure * 0.25 - transmission_pressure * 0.20)

    water_dependency = clamp(avg_water * 0.7 + config.water_stress * 0.45)
    transport_pressure = clamp(avg_transport * 0.55 + config.transport_electrification * 0.55 + transmission_pressure * 0.16)
    industrial_pressure = clamp(config.industrial_demand * 0.62 + backup_requirement * 0.22 + transmission_pressure * 0.20)
    geopolitical_exposure = clamp((avg_dependency * 0.72 + storage_dependency * 0.28 + gas_exposure * 0.45 + config.geopolitical_tension * 0.45) * (config.dependency_sensitivity / 55))

    resilience = clamp(45 + avg_reliability * 0.35 + avg_flexibility * 0.18 + storage_buffer * 0.33 - transmission_pressure * 0.32 - storage_pressure * 0.22 - gas_exposure * 0.18 - geopolitical_exposure * 0.08)
    reliability = clamp(avg_reliability * 0.70 + baseload_share * 30 + storage_buffer * 0.18 - renewable_gap * 0.35 - backup_requirement * 0.20)

    cost_index = clamp(avg_cost + storage_capacity * storage_cost * 0.006 + demand_factor * 7 + gas_exposure * 0.25)
    emissions_index = clamp(avg_emissions + gas_exposure * 0.65 - renewable_share * 8 - storage_capacity * 0.03)
    dependency = clamp(geopolitical_exposure)

    bottleneck_pressure = clamp(max(storage_pressure, transmission_pressure, backup_requirement, water_dependency * 0.7, industrial_pressure * 0.75))
    coordination_drift = clamp(transmission_pressure * 0.35 + storage_pressure * 0.28 + (100 - reserve_margin) * 0.22 + stress["cascade"] * 15)

    cascade_risk = clamp(
        bottleneck_pressure * 0.30 + coordination_drift * 0.25 + water_dependency * 0.14 +
        transport_pressure * 0.13 + industrial_pressure * 0.12 + geopolitical_exposure * 0.12
    )

    headline_score = clamp(
        (100 - cost_index) * priority_weights["cost"] * 0.18
        + (100 - emissions_index) * priority_weights["emissions"] * 0.18
        + reliability * priority_weights["reliability"] * 0.22
        + resilience * priority_weights["resilience"] * 0.25
        + (100 - dependency) * priority_weights["dependency"] * 0.17
    )

    return {
        "cost_index": round(cost_index, 1),
        "emissions_index": round(emissions_index, 1),
        "reliability": round(reliability, 1),
        "resilience": round(resilience, 1),
        "dependency": round(dependency, 1),
        "reserve_margin": round(reserve_margin, 1),
        "storage_flexibility": round(clamp(storage_buffer), 1),
        "transmission_pressure": round(transmission_pressure, 1),
        "storage_pressure": round(storage_pressure, 1),
        "backup_requirement": round(backup_requirement, 1),
        "bottleneck_pressure": round(bottleneck_pressure, 1),
        "coordination_drift": round(coordination_drift, 1),
        "headline_score": round(headline_score, 1),
        "renewable_share": round(renewable_share * 100, 1),
        "baseload_share": round(baseload_share * 100, 1),
        "gas_share": round(gas_share * 100, 1),
        "water_dependency": round(water_dependency, 1),
        "transport_pressure": round(transport_pressure, 1),
        "industrial_pressure": round(industrial_pressure, 1),
        "geopolitical_exposure": round(geopolitical_exposure, 1),
        "cascade_risk": round(cascade_risk, 1),
    }

def simulate_timeline(config: SimulationInput, steps: int = 48) -> pd.DataFrame:
    rows = []
    for step in range(steps):
        local = SimulationInput(**{**config.__dict__, "timeline_step": step})
        result = evaluate_system(local)
        rows.append({"step": step, **result})
    return pd.DataFrame(rows)

def actor_scores(results: dict) -> pd.DataFrame:
    rows = []
    for actor, w in ACTOR_WEIGHTS.items():
        score = (
            (100-results["cost_index"]) * w["cost"] +
            (100-results["emissions_index"]) * w["emissions"] +
            results["reliability"] * w["reliability"] +
            results["resilience"] * w["resilience"] +
            (100-results["dependency"]) * w["dependency"]
        )
        concern = max(
            [
                ("Cost", results["cost_index"]),
                ("Emissions", results["emissions_index"]),
                ("Reliability gap", 100-results["reliability"]),
                ("Resilience gap", 100-results["resilience"]),
                ("Dependency", results["dependency"]),
            ],
            key=lambda x: x[1],
        )[0]
        rows.append({"Actor": actor, "Score": round(score, 1), "Main concern": concern})
    return pd.DataFrame(rows)

def scenario_payload(config: SimulationInput, results: dict) -> dict:
    return {
        "schema": "energy-portfolio-systems-simulator/v1",
        "priority": config.priority,
        "stress_test": config.stress_test,
        "generation_mix": config.generation_mix,
        "storage_mix": config.storage_mix,
        "demand_growth": config.demand_growth,
        "dependency_sensitivity": config.dependency_sensitivity,
        "water_stress": config.water_stress,
        "transport_electrification": config.transport_electrification,
        "industrial_demand": config.industrial_demand,
        "geopolitical_tension": config.geopolitical_tension,
        "results": results,
    }
