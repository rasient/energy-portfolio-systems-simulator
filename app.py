from __future__ import annotations
import json
import streamlit as st
import pandas as pd
import plotly.express as px

from src.model import SimulationInput, evaluate_system, simulate_timeline, actor_scores, scenario_payload
from src.scenarios import PRIORITIES, STRESS_TESTS, PRESETS
from src.visualization import (
    create_network_figure, create_tradeoff_radar, create_pressure_bars,
    create_timeline_figure, create_actor_figure, create_dependency_figure,
    create_scenario_compare
)
from src.utils import scenario_to_json, load_scenario_json
from src.adapters import create_pypsa_export_preview, create_oemof_export_preview, simulated_external_results

st.set_page_config(page_title="Energy Portfolio Systems Simulator", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.1rem; padding-bottom: 2rem;}
.metric-card {padding: .85rem; border-radius: 1rem; border: 1px solid rgba(128,128,128,.25); background: rgba(128,128,128,.06); margin-bottom: .55rem;}
.small-muted {color: #777; font-size: .84rem;}
.phase-box {padding: 1rem; border-radius: 1rem; border: 1px solid rgba(128,128,128,.25); background: rgba(128,128,128,.05);}
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Portfolio Systems Simulator")
st.caption("Full-roadmap prototype: visual MVP + dynamic behavior + scenarios + actors + adapter layer + Systems Lab infrastructure expansion.")

GENERATION_DEFAULTS = {"Solar":22,"Wind":20,"Nuclear":24,"Gas":18,"Hydro":10,"Geothermal":4,"Biomass":2}
STORAGE_DEFAULTS = {"Battery":35,"Pumped hydro":25,"Hydrogen":15}

if "scenario" not in st.session_state:
    st.session_state.scenario = PRESETS["Balanced transition"].copy()

with st.sidebar:
    st.header("Scenario")
    preset = st.selectbox("Load preset", list(PRESETS.keys()))
    if st.button("Apply preset"):
        st.session_state.scenario = PRESETS[preset].copy()
        st.rerun()

    uploaded = st.file_uploader("Import scenario JSON", type=["json"])
    if uploaded:
        imported = load_scenario_json(uploaded.read().decode("utf-8"))
        st.session_state.scenario = {
            "priority": imported.get("priority", "Highest resilience"),
            "stress_test": imported.get("stress_test", "Normal conditions"),
            "generation_mix": imported.get("generation_mix", GENERATION_DEFAULTS),
            "storage_mix": imported.get("storage_mix", STORAGE_DEFAULTS),
            "demand_growth": imported.get("demand_growth", 15),
            "dependency_sensitivity": imported.get("dependency_sensitivity", 55),
            "water_stress": imported.get("water_stress", 30),
            "transport_electrification": imported.get("transport_electrification", 25),
            "industrial_demand": imported.get("industrial_demand", 35),
            "geopolitical_tension": imported.get("geopolitical_tension", 35),
        }
        st.success("Scenario imported.")
        st.rerun()

    st.divider()
    st.header("Controls")

    scenario = st.session_state.scenario
    priority = st.selectbox("Optimization priority", list(PRIORITIES.keys()), index=list(PRIORITIES.keys()).index(scenario.get("priority","Highest resilience")))
    stress_test = st.selectbox("Stress test", list(STRESS_TESTS.keys()), index=list(STRESS_TESTS.keys()).index(scenario.get("stress_test","Normal conditions")))
    demand_growth = st.slider("Demand growth", 0, 60, int(scenario.get("demand_growth",15)), 1)
    dependency_sensitivity = st.slider("Dependency sensitivity", 20, 100, int(scenario.get("dependency_sensitivity",55)), 1)

    with st.expander("Generation mix", expanded=False):
        generation_mix = {}
        for tech, default in scenario.get("generation_mix", GENERATION_DEFAULTS).items():
            generation_mix[tech] = st.slider(tech, 0, 100, int(default), 1)

    with st.expander("Storage capacities", expanded=False):
        storage_mix = {}
        for tech, default in scenario.get("storage_mix", STORAGE_DEFAULTS).items():
            storage_mix[tech] = st.slider(tech, 0, 100, int(default), 1)

    with st.expander("Systems Lab expansion assumptions", expanded=False):
        water_stress = st.slider("Water stress", 0, 100, int(scenario.get("water_stress",30)), 1)
        transport_electrification = st.slider("Transport electrification pressure", 0, 100, int(scenario.get("transport_electrification",25)), 1)
        industrial_demand = st.slider("Industrial demand coupling", 0, 100, int(scenario.get("industrial_demand",35)), 1)
        geopolitical_tension = st.slider("Geopolitical tension", 0, 100, int(scenario.get("geopolitical_tension",35)), 1)

timeline_step = st.slider("Playback timeline step", 0, 100, 22, 1)

config = SimulationInput(
    priority=priority,
    stress_test=stress_test,
    generation_mix=generation_mix,
    storage_mix=storage_mix,
    demand_growth=demand_growth,
    dependency_sensitivity=dependency_sensitivity,
    timeline_step=timeline_step,
    water_stress=water_stress,
    transport_electrification=transport_electrification,
    industrial_demand=industrial_demand,
    geopolitical_tension=geopolitical_tension,
)
results = evaluate_system(config)
payload = scenario_payload(config, results)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Phase 1: Visual MVP",
    "Phase 2: Dynamic Behavior",
    "Phase 3: Scenarios",
    "Phase 4: Actors",
    "Phase 5: Integration",
    "Phase 6: Systems Lab",
    "Education Mode",
])

with tab1:
    left, center, right = st.columns([1.0,2.15,1.0], gap="large")
    with left:
        st.subheader("Portfolio")
        st.write(f"**Priority:** {priority}")
        st.write(f"**Stress test:** {stress_test}")
        st.metric("Renewable share", f"{results['renewable_share']}%")
        st.metric("Baseload share", f"{results['baseload_share']}%")
        st.metric("Gas share", f"{results['gas_share']}%")
    with center:
        st.plotly_chart(create_network_figure(generation_mix, storage_mix, results, timeline_step), use_container_width=True)
        st.info("Warmer/larger nodes indicate pressure. Pulses become denser and less smooth as bottlenecks increase.")
    with right:
        st.subheader("Outputs")
        st.metric("System score", results["headline_score"])
        st.metric("Resilience", results["resilience"])
        st.metric("Reserve margin", results["reserve_margin"])
        st.plotly_chart(create_tradeoff_radar(results), use_container_width=True)
    st.plotly_chart(create_pressure_bars(results), use_container_width=True)

with tab2:
    st.subheader("Phase 2 — Better Visual Behavior")
    df_time = simulate_timeline(config, 60)
    st.plotly_chart(create_timeline_figure(df_time), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Storage charge/discharge proxy")
        storage_df = df_time[["step","storage_flexibility","storage_pressure","reserve_margin"]].copy()
        storage_df["charge_proxy"] = (storage_df["storage_flexibility"] - storage_df["storage_pressure"]*0.35).clip(0,100)
        fig = px.area(storage_df, x="step", y=["charge_proxy","storage_pressure"], title="Storage Buffer vs Storage Pressure")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### Congestion buildup proxy")
        congestion = df_time[["step","transmission_pressure","coordination_drift","bottleneck_pressure"]]
        fig = px.line(congestion, x="step", y=["transmission_pressure","coordination_drift","bottleneck_pressure"], title="Pulse Drift / Congestion Buildup")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Phase 3 — Scenario System")
    scenario_json = scenario_to_json(payload)
    st.download_button("Download current scenario JSON", scenario_json, file_name="energy_scenario.json", mime="application/json")

    rows = []
    for name, preset_data in PRESETS.items():
        local_config = SimulationInput(
            priority=preset_data["priority"],
            stress_test=preset_data["stress_test"],
            generation_mix=preset_data["generation_mix"],
            storage_mix=preset_data["storage_mix"],
            demand_growth=preset_data["demand_growth"],
            dependency_sensitivity=preset_data["dependency_sensitivity"],
            timeline_step=timeline_step,
            water_stress=water_stress,
            transport_electrification=transport_electrification,
            industrial_demand=industrial_demand,
            geopolitical_tension=geopolitical_tension,
        )
        row = {"Scenario": name, **evaluate_system(local_config)}
        rows.append(row)
    compare_df = pd.DataFrame(rows)
    st.plotly_chart(create_scenario_compare(compare_df), use_container_width=True)
    st.dataframe(compare_df, use_container_width=True)

with tab4:
    st.subheader("Phase 4 — Actor Perspectives")
    actor_df = actor_scores(results)
    st.plotly_chart(create_actor_figure(actor_df), use_container_width=True)
    st.dataframe(actor_df, use_container_width=True)

    st.markdown("""
    Different actors interpret the same system differently:

    - government balances emissions, resilience, cost, and dependency
    - grid operators prioritize reliability and resilience
    - industry prioritizes cost and reliable supply
    - citizens prioritize affordability and continuity
    - investors prioritize risk-adjusted opportunity and dependency exposure
    """)

with tab5:
    st.subheader("Phase 5 — External Model Integration Layer")
    st.warning("This is adapter-ready placeholder logic, not real PyPSA/oemof execution yet.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### PyPSA export preview")
        st.json(create_pypsa_export_preview(payload))
    with c2:
        st.markdown("### oemof export preview")
        st.json(create_oemof_export_preview(payload))

    st.markdown("### Simulated external model result comparison")
    external_df = simulated_external_results(payload)
    st.dataframe(external_df, use_container_width=True)
    st.plotly_chart(px.bar(external_df, x="Model", y=["Cost","Emissions","Resilience"], barmode="group", title="Internal vs External Placeholder Outputs"), use_container_width=True)

with tab6:
    st.subheader("Phase 6 — Systems Lab Expansion")
    st.plotly_chart(create_dependency_figure(results), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Water dependency", results["water_dependency"])
    c2.metric("Transport pressure", results["transport_pressure"])
    c3.metric("Industrial pressure", results["industrial_pressure"])
    c4.metric("Geopolitical exposure", results["geopolitical_exposure"])

    st.markdown("### Simplified cascade reading")
    if results["cascade_risk"] < 35:
        st.success("Cascade risk is low. Infrastructure coupling remains manageable.")
    elif results["cascade_risk"] < 65:
        st.warning("Cascade risk is moderate. Stress can propagate across energy, water, transport, or industrial demand.")
    else:
        st.error("Cascade risk is high. Multiple infrastructure dependencies are under simultaneous pressure.")

with tab7:
    st.subheader("Education Mode")
    st.markdown(f"""
    ### What the current scenario teaches

    **Priority:** {priority}  
    **Stress test:** {stress_test}

    This scenario shows how an energy portfolio behaves when generation, storage, demand, and external dependencies interact.

    Key readings:

    - **Resilience:** {results['resilience']} / 100
    - **Bottleneck pressure:** {results['bottleneck_pressure']} / 100
    - **Coordination drift:** {results['coordination_drift']} / 100
    - **Cascade risk:** {results['cascade_risk']} / 100

    ### Interpretation

    A system can still function while becoming less resilient.

    This prototype helps users see the transition from:

    **stable → stressed → fragile → unstable**

    The purpose is not exact grid prediction.

    The purpose is visual systems understanding.
    """)

st.divider()
st.caption("Prototype model only. This app is for visual systems understanding, not scientific grid prediction.")
