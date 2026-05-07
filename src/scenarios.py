from __future__ import annotations

PRIORITIES = {
    "Lowest cost": {"cost": 1.30, "emissions": 0.75, "reliability": 0.85, "resilience": 0.75, "dependency": 0.75},
    "Lowest emissions": {"cost": 0.85, "emissions": 1.35, "reliability": 0.85, "resilience": 0.95, "dependency": 0.80},
    "Highest reliability": {"cost": 0.85, "emissions": 0.80, "reliability": 1.40, "resilience": 1.05, "dependency": 0.90},
    "Highest resilience": {"cost": 0.80, "emissions": 0.85, "reliability": 1.10, "resilience": 1.40, "dependency": 1.00},
    "Lowest external dependency": {"cost": 0.85, "emissions": 0.90, "reliability": 1.00, "resilience": 1.10, "dependency": 1.40},
}

STRESS_TESTS = {
    "Normal conditions": {"demand": 1.00, "renewable_penalty": 0.00, "gas_penalty": 0.00, "transmission_pressure": 0.15, "storage_pressure": 0.15, "cascade": 0.10},
    "Demand spike": {"demand": 1.30, "renewable_penalty": 0.04, "gas_penalty": 0.00, "transmission_pressure": 0.42, "storage_pressure": 0.34, "cascade": 0.35},
    "Fuel shock": {"demand": 1.05, "renewable_penalty": 0.00, "gas_penalty": 0.48, "transmission_pressure": 0.25, "storage_pressure": 0.32, "cascade": 0.42},
    "Low renewable period": {"demand": 1.10, "renewable_penalty": 0.48, "gas_penalty": 0.00, "transmission_pressure": 0.33, "storage_pressure": 0.48, "cascade": 0.45},
    "Transmission bottleneck": {"demand": 1.12, "renewable_penalty": 0.10, "gas_penalty": 0.00, "transmission_pressure": 0.70, "storage_pressure": 0.32, "cascade": 0.58},
    "Storage saturation": {"demand": 1.12, "renewable_penalty": 0.12, "gas_penalty": 0.00, "transmission_pressure": 0.42, "storage_pressure": 0.74, "cascade": 0.52},
}

PRESETS = {
    "Balanced transition": {
        "priority": "Highest resilience",
        "stress_test": "Normal conditions",
        "generation_mix": {"Solar": 22, "Wind": 20, "Nuclear": 24, "Gas": 18, "Hydro": 10, "Geothermal": 4, "Biomass": 2},
        "storage_mix": {"Battery": 35, "Pumped hydro": 25, "Hydrogen": 15},
        "demand_growth": 15,
        "dependency_sensitivity": 55,
    },
    "Maximum renewables": {
        "priority": "Lowest emissions",
        "stress_test": "Low renewable period",
        "generation_mix": {"Solar": 38, "Wind": 34, "Nuclear": 10, "Gas": 6, "Hydro": 7, "Geothermal": 3, "Biomass": 2},
        "storage_mix": {"Battery": 60, "Pumped hydro": 35, "Hydrogen": 45},
        "demand_growth": 20,
        "dependency_sensitivity": 50,
    },
    "Reliability first": {
        "priority": "Highest reliability",
        "stress_test": "Demand spike",
        "generation_mix": {"Solar": 14, "Wind": 12, "Nuclear": 38, "Gas": 22, "Hydro": 10, "Geothermal": 3, "Biomass": 1},
        "storage_mix": {"Battery": 30, "Pumped hydro": 35, "Hydrogen": 20},
        "demand_growth": 18,
        "dependency_sensitivity": 62,
    },
    "Low dependency": {
        "priority": "Lowest external dependency",
        "stress_test": "Fuel shock",
        "generation_mix": {"Solar": 26, "Wind": 22, "Nuclear": 22, "Gas": 8, "Hydro": 12, "Geothermal": 7, "Biomass": 3},
        "storage_mix": {"Battery": 45, "Pumped hydro": 30, "Hydrogen": 35},
        "demand_growth": 12,
        "dependency_sensitivity": 85,
    },
}
