# Ocean Portfolio Map

An interactive career and journalism portfolio built on a [Global Fishing Watch](https://globalfishingwatch.org/) ocean map.

**Live:** [ocean.ricardoperezsolero.com](https://ocean.ricardoperezsolero.com)

---

## About

When GFW began tracking the ocean, I was reporting on it. This map overlays a decade of field reporting across Southeast Asia, Europe and Latin America onto GFW's live ocean data — showing the geographic overlap between my journalism career and the issues GFW monitors: illegal fishing, vessel encounters, and offshore infrastructure.

## Features

- Career location pins with role descriptions, dates and tags
- Portfolio story pins linked to published work and video
- Tag filter to explore by topic (GFW, Ocean Governance, Journalism, Migration, etc.)
- **AIS vessel presence** — live 24-hour heatmap via GFW 4Wings tile API
- **Vessel encounters** — 7-day heatmap flagging potential transshipment events
- **Offshore infrastructure** — oil platforms and wind farms detected by satellite SAR, filtered to career regions (Europe, Southeast Asia, South America)
- Legend with expandable info panels explaining each GFW data layer
- Mobile-responsive layout with collapsible legend

## Data sources

| Layer | Source | Notes |
|---|---|---|
| AIS vessel presence | GFW 4Wings API (`public-global-presence:latest`) | 24h window, 3-day offset |
| Vessel encounters | GFW 4Wings API (`public-global-encounters-events:latest`) | 7-day window |
| Fixed infrastructure | GFW `public-fixed-infrastructure:v1.1` | SAR + optical, Paolo et al. Nature 2024 |

The infrastructure layer is pre-processed from the raw monthly CSV (~800MB) using `process_infrastructure.py`, which filters to high-confidence detections in three career regions and outputs a 2.3MB GeoJSON. Dataset: December 2025.

## Built with

- Vanilla HTML, CSS and JavaScript — no frameworks
- [MapLibre GL JS](https://maplibre.org/) 4.7.1
- GFW 4Wings tile API for live fishing activity layers
- Python for CSV → GeoJSON data pipeline
- Hosted on Cloudflare Pages (auto-deploy from GitHub `main`)
