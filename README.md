# Energy Portfolio Systems Simulator

A full-roadmap Streamlit prototype for exploring energy portfolio trade-offs, storage behavior, bottlenecks, resilience, actor perspectives, and interconnected infrastructure stress.

This project is designed as a **visual systems-understanding layer** — not a replacement for scientific grid-optimization frameworks.

---

## What This App Does

The app lets users explore energy systems through simple, visual interactions:

- choose an energy portfolio
- adjust storage capacities
- apply stress tests
- compare scenarios
- observe bottlenecks
- compare actor perspectives
- simulate energy-water-transport dependencies
- export/import scenarios
- view placeholder adapter outputs for future PyPSA/oemof integration

---

## Implemented Roadmap

The original future roadmap is now represented inside the app as working prototype modules.

### Phase 1 — Visual MVP

Implemented:

- simple scenario controls
- generation sliders
- storage sliders
- stress-test selector
- animated network map
- bottleneck pressure indicators
- trade-off outputs
- basic resilience reading

### Phase 2 — Better Visual Behavior

Implemented as simplified visual simulations:

- pulse propagation
- congestion buildup
- storage charge/discharge timeline
- coordination drift
- stress propagation over time

### Phase 3 — Scenario System

Implemented:

- scenario presets
- save/export scenario as JSON
- import scenario JSON
- compare scenarios side-by-side
- educational explanation mode

### Phase 4 — Actor Perspectives

Implemented:

- government perspective
- grid operator perspective
- industrial sector perspective
- citizen perspective
- investor perspective

Each actor applies different priority weights and interprets the same system differently.

### Phase 5 — External Model Integration

Implemented as an adapter-ready interface:

- PyPSA export placeholder
- oemof export placeholder
- standardized scenario schema
- simulated external model result preview
- integration notes

This is not a real PyPSA/oemof backend yet. It creates the interface layer and future integration structure.

### Phase 6 — Systems Lab Expansion

Implemented as simplified systems-dependency simulations:

- energy-water dependency
- transport-energy dependency
- industrial demand coupling
- geopolitical dependency map
- resilience/cascade simulation

---

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Project Positioning

This project complements tools such as PyPSA and oemof.

Those frameworks focus on deep technical optimization.

This app focuses on:

- visual understanding
- scenario exploration
- infrastructure trade-offs
- coordination pressure
- resilience communication
- decision-support visualization

---

## Part of Systems Lab

This project is part of a broader exploration:

→ understanding how systems behave when treated as interconnected.

Main repo:

https://github.com/rasient/systems-lab
