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
from src.i18n import LANGUAGES, translate

st.set_page_config(page_title="Energy Portfolio Systems Simulator", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.1rem; padding-bottom: 2rem;}
.metric-card {padding: .85rem; border-radius: 1rem; border: 1px solid rgba(128,128,128,.25); background: rgba(128,128,128,.06); margin-bottom: .55rem;}
.small-muted {color: #777; font-size: .84rem;}
.phase-box {padding: 1rem; border-radius: 1rem; border: 1px solid rgba(128,128,128,.25); background: rgba(128,128,128,.05);}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    selected_language = st.selectbox("Language / Nyelv", list(LANGUAGES.keys()), index=0, help="Choose the interface language.")
lang = LANGUAGES[selected_language]
t = lambda key: translate(key, lang)

st.title(t("app_title"))
st.caption(t("app_caption"))

GENERATION_DEFAULTS = {"Solar":22,"Wind":20,"Nuclear":24,"Gas":18,"Hydro":10,"Geothermal":4,"Biomass":2}
STORAGE_DEFAULTS = {"Battery":35,"Pumped hydro":25,"Hydrogen":15}

if "scenario" not in st.session_state:
    st.session_state.scenario = PRESETS["Balanced transition"].copy()

with st.sidebar:
    st.header(t("scenario"))
    preset = st.selectbox(t("load_preset"), list(PRESETS.keys()))
    if st.button(t("apply_preset")):
        st.session_state.scenario = PRESETS[preset].copy()
        st.rerun()

    uploaded = st.file_uploader(t("import_scenario"), type=["json"])
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
        st.success(t("scenario_imported"))
        st.rerun()

    st.divider()
    st.header(t("controls"))

    scenario = st.session_state.scenario
    priority = st.selectbox(t("optimization_priority"), list(PRIORITIES.keys()), index=list(PRIORITIES.keys()).index(scenario.get("priority","Highest resilience")))
    stress_test = st.selectbox(t("stress_test"), list(STRESS_TESTS.keys()), index=list(STRESS_TESTS.keys()).index(scenario.get("stress_test","Normal conditions")))
    demand_growth = st.slider(t("demand_growth"), 0, 60, int(scenario.get("demand_growth",15)), 1)
    dependency_sensitivity = st.slider(t("dependency_sensitivity"), 20, 100, int(scenario.get("dependency_sensitivity",55)), 1)

    with st.expander(t("generation_mix"), expanded=False):
        generation_mix = {}
        for tech, default in scenario.get("generation_mix", GENERATION_DEFAULTS).items():
            generation_mix[tech] = st.slider(tech, 0, 100, int(default), 1)

    with st.expander(t("storage_capacities"), expanded=False):
        storage_mix = {}
        for tech, default in scenario.get("storage_mix", STORAGE_DEFAULTS).items():
            storage_mix[tech] = st.slider(tech, 0, 100, int(default), 1)

    with st.expander(t("systems_lab_expansion"), expanded=False):
        water_stress = st.slider(t("water_stress"), 0, 100, int(scenario.get("water_stress",30)), 1)
        transport_electrification = st.slider(t("transport_electrification"), 0, 100, int(scenario.get("transport_electrification",25)), 1)
        industrial_demand = st.slider(t("industrial_demand"), 0, 100, int(scenario.get("industrial_demand",35)), 1)
        geopolitical_tension = st.slider(t("geopolitical_tension"), 0, 100, int(scenario.get("geopolitical_tension",35)), 1)

timeline_step = st.slider(t("playback"), 0, 100, 22, 1)

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

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    t("tab1"),
    t("tab2"),
    t("tab3"),
    t("tab4"),
    t("tab5"),
    t("tab6"),
    t("tab7"),
    t("tab8"),
])

with tab1:
    left, center, right = st.columns([1.0,2.15,1.0], gap="large")
    with left:
        st.subheader(t("portfolio"))
        st.write(f"**{t('priority')}:** {priority}")
        st.write(f"**{t('stress_test')}:** {stress_test}")
        st.metric(t("renewable_share"), f"{results['renewable_share']}%")
        st.metric(t("baseload_share"), f"{results['baseload_share']}%")
        st.metric(t("gas_share"), f"{results['gas_share']}%")
    with center:
        st.plotly_chart(create_network_figure(generation_mix, storage_mix, results, timeline_step), use_container_width=True)
        st.info(t("network_info"))
    with right:
        st.subheader(t("outputs"))
        st.metric(t("system_score"), results["headline_score"])
        st.metric(t("resilience"), results["resilience"])
        st.metric(t("reserve_margin"), results["reserve_margin"])
        st.plotly_chart(create_tradeoff_radar(results), use_container_width=True)
    st.plotly_chart(create_pressure_bars(results), use_container_width=True)

with tab2:
    st.subheader(t("phase2_title"))
    df_time = simulate_timeline(config, 60)
    st.plotly_chart(create_timeline_figure(df_time), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### " + t("storage_proxy"))
        storage_df = df_time[["step","storage_flexibility","storage_pressure","reserve_margin"]].copy()
        storage_df["charge_proxy"] = (storage_df["storage_flexibility"] - storage_df["storage_pressure"]*0.35).clip(0,100)
        fig = px.area(storage_df, x="step", y=["charge_proxy","storage_pressure"], title="Storage Buffer vs Storage Pressure")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### " + t("congestion_proxy"))
        congestion = df_time[["step","transmission_pressure","coordination_drift","bottleneck_pressure"]]
        fig = px.line(congestion, x="step", y=["transmission_pressure","coordination_drift","bottleneck_pressure"], title="Pulse Drift / Congestion Buildup")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader(t("phase3_title"))
    scenario_json = scenario_to_json(payload)
    st.download_button(t("download_json"), scenario_json, file_name="energy_scenario.json", mime="application/json")

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
    st.subheader(t("phase4_title"))
    actor_df = actor_scores(results)
    st.plotly_chart(create_actor_figure(actor_df), use_container_width=True)
    st.dataframe(actor_df, use_container_width=True)

    st.markdown(t("actor_text"))

with tab5:
    st.subheader(t("phase5_title"))
    st.warning(t("adapter_warning"))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### " + t("pypsa_preview"))
        st.json(create_pypsa_export_preview(payload))
    with c2:
        st.markdown("### " + t("oemof_preview"))
        st.json(create_oemof_export_preview(payload))

    st.markdown("### " + t("external_compare"))
    external_df = simulated_external_results(payload)
    st.dataframe(external_df, use_container_width=True)
    st.plotly_chart(px.bar(external_df, x="Model", y=["Cost","Emissions","Resilience"], barmode="group", title="Internal vs External Placeholder Outputs"), use_container_width=True)

with tab6:
    st.subheader(t("phase6_title"))
    st.plotly_chart(create_dependency_figure(results), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("water_dependency"), results["water_dependency"])
    c2.metric(t("transport_pressure"), results["transport_pressure"])
    c3.metric(t("industrial_pressure"), results["industrial_pressure"])
    c4.metric(t("geopolitical_exposure"), results["geopolitical_exposure"])

    st.markdown("### " + t("cascade_reading"))
    if results["cascade_risk"] < 35:
        st.success(t("cascade_low"))
    elif results["cascade_risk"] < 65:
        st.warning(t("cascade_medium"))
    else:
        st.error(t("cascade_high"))

with tab7:
    st.subheader(t("education_title"))
    st.markdown(f"""
    ### {t('what_teaches')}

    **{t('priority')}:** {priority}  
    **{t('stress_test')}:** {stress_test}

    {t('scenario_shows')}

    {t('key_readings')}

    - **{t('resilience')}:** {results['resilience']} / 100
    - **Bottleneck pressure:** {results['bottleneck_pressure']} / 100
    - **Coordination drift:** {results['coordination_drift']} / 100
    - **Cascade risk:** {results['cascade_risk']} / 100

    ### {t('interpretation')}

    {t('stable_sentence')}

    {t('transition_sentence')}

    **{t('transition')}**

    {t('purpose1')}

    {t('purpose2')}
    """)

with tab8:
    st.subheader(t("language_title"))
    st.markdown(t("language_body"))
    st.markdown(t("cooperation_points"))
    st.info("Translation is treated here as a systems feature: it helps different people coordinate around the same model.")

st.divider()
st.caption(t("footer"))
