from __future__ import annotations
import math
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

NODE_POSITIONS = {
    "Solar": (0.10, 0.82),
    "Wind": (0.10, 0.64),
    "Nuclear": (0.10, 0.45),
    "Gas": (0.10, 0.25),
    "Hydro": (0.10, 0.08),
    "Battery": (0.48, 0.76),
    "Pumped hydro": (0.48, 0.50),
    "Hydrogen": (0.48, 0.24),
    "Grid / Demand": (0.86, 0.50),
}
EDGES = [
    ("Solar", "Battery"), ("Wind", "Battery"), ("Hydro", "Pumped hydro"),
    ("Nuclear", "Grid / Demand"), ("Gas", "Grid / Demand"), ("Hydro", "Grid / Demand"),
    ("Battery", "Grid / Demand"), ("Pumped hydro", "Grid / Demand"), ("Hydrogen", "Grid / Demand"),
    ("Solar", "Grid / Demand"), ("Wind", "Grid / Demand"),
]

def pressure_color(value: float) -> str:
    if value < 35: return "#2e7d32"
    if value < 65: return "#f9a825"
    return "#c62828"

def create_network_figure(generation_mix: dict, storage_mix: dict, results: dict, timeline_step: int) -> go.Figure:
    fig = go.Figure()
    drift = results["coordination_drift"] / 100
    bottleneck = results["bottleneck_pressure"]
    transmission = results["transmission_pressure"]

    for idx, (source, target) in enumerate(EDGES):
        x0, y0 = NODE_POSITIONS[source]; x1, y1 = NODE_POSITIONS[target]
        phase = math.sin((timeline_step + idx * 1.7) / 4.0)
        width = 1.4 + transmission / 30 + max(phase, 0) * drift * 3
        opacity = 0.28 + min(0.55, transmission / 150)
        fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines",
            line=dict(width=width, color=f"rgba(80,80,80,{opacity})"), hoverinfo="skip", showlegend=False))
        t = ((timeline_step * (0.045 + drift * 0.035)) + idx * 0.13) % 1.0
        pxv = x0 + (x1-x0)*t; pyv = y0 + (y1-y0)*t
        fig.add_trace(go.Scatter(x=[pxv], y=[pyv], mode="markers",
            marker=dict(size=6+bottleneck/18+max(phase,0)*4, color=pressure_color(bottleneck), opacity=0.58),
            hoverinfo="skip", showlegend=False))

    xs, ys, labels, sizes, colors, hover = [], [], [], [], [], []
    for name, (x,y) in NODE_POSITIONS.items():
        xs.append(x); ys.append(y); labels.append(name)
        if name in generation_mix: size = 18 + generation_mix[name]*0.38
        elif name in storage_mix: size = 18 + storage_mix[name]*0.32
        else: size = 35 + bottleneck*0.10
        sizes.append(size)
        if name in ["Battery", "Pumped hydro", "Hydrogen"]: pressure = results["storage_pressure"]
        elif name == "Grid / Demand": pressure = bottleneck
        else: pressure = results["transmission_pressure"] * 0.65
        colors.append(pressure_color(pressure))
        hover.append(f"{name}<br>Pressure: {pressure:.1f}")

    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=labels, textposition="bottom center",
        marker=dict(size=sizes, color=colors, line=dict(width=2, color="white"), opacity=0.9),
        hovertext=hover, hoverinfo="text", showlegend=False))

    fig.update_layout(height=560, margin=dict(l=10,r=10,t=35,b=10),
        xaxis=dict(visible=False, range=[-0.05,1.05]), yaxis=dict(visible=False, range=[-0.08,0.92]),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text="Live Energy Portfolio Systems Map", x=0.03, font=dict(size=18)))
    return fig

def create_tradeoff_radar(results: dict) -> go.Figure:
    categories = ["Low Cost", "Low Emissions", "Reliability", "Resilience", "Low Dependency"]
    values = [100-results["cost_index"], 100-results["emissions_index"], results["reliability"], results["resilience"], 100-results["dependency"]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values+[values[0]], theta=categories+[categories[0]], fill="toself", name="System profile"))
    fig.update_layout(height=330, margin=dict(l=20,r=20,t=35,b=20), polar=dict(radialaxis=dict(visible=True, range=[0,100])), showlegend=False, title="Trade-Off Shape")
    return fig

def create_pressure_bars(results: dict) -> go.Figure:
    data = pd.DataFrame({"Metric":["Transmission","Storage","Backup","Coordination drift","Bottleneck","Cascade risk"],
                         "Value":[results["transmission_pressure"],results["storage_pressure"],results["backup_requirement"],results["coordination_drift"],results["bottleneck_pressure"],results["cascade_risk"]]})
    fig = px.bar(data, x="Value", y="Metric", orientation="h", text="Value", title="Pressure & Bottleneck Indicators", range_x=[0,100])
    fig.update_layout(height=330, margin=dict(l=10,r=20,t=45,b=10))
    return fig

def create_timeline_figure(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col in ["resilience", "bottleneck_pressure", "coordination_drift", "cascade_risk", "reserve_margin"]:
        fig.add_trace(go.Scatter(x=df["step"], y=df[col], mode="lines", name=col.replace("_"," ").title()))
    fig.update_layout(height=420, title="Phase 2 — Time-Based System Behavior", xaxis_title="Playback step", yaxis_title="Score / pressure", yaxis=dict(range=[0,100]))
    return fig

def create_actor_figure(actor_df: pd.DataFrame) -> go.Figure:
    fig = px.bar(actor_df, x="Actor", y="Score", text="Score", color="Main concern", title="Phase 4 — Actor Perspective Scores", range_y=[0,100])
    fig.update_layout(height=420)
    return fig

def create_dependency_figure(results: dict) -> go.Figure:
    labels = ["Energy Core", "Water", "Transport", "Industry", "Geopolitics", "Cascade Risk"]
    values = [results["bottleneck_pressure"], results["water_dependency"], results["transport_pressure"], results["industrial_pressure"], results["geopolitical_exposure"], results["cascade_risk"]]
    fig = go.Figure(go.Scatterpolar(r=values+[values[0]], theta=labels+[labels[0]], fill="toself"))
    fig.update_layout(height=430, title="Phase 6 — Interconnected Infrastructure Exposure", polar=dict(radialaxis=dict(range=[0,100])))
    return fig

def create_scenario_compare(df: pd.DataFrame) -> go.Figure:
    melted = df.melt(id_vars=["Scenario"], value_vars=["headline_score","resilience","reliability","dependency","cascade_risk"], var_name="Metric", value_name="Value")
    fig = px.bar(melted, x="Scenario", y="Value", color="Metric", barmode="group", title="Phase 3 — Scenario Comparison", range_y=[0,100])
    fig.update_layout(height=440)
    return fig
