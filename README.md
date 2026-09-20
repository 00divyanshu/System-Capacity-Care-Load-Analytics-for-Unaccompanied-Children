# OpsCapacity | Operational Load & Flow Intelligence Engine

> **End-to-end Python pipeline and interactive Streamlit analytics platform for real-time facility stress modeling and intake/discharge forecasting.**

[![Live Demo](https://img.shields.io/badge/🚀%20Streamlit%20Cloud-Live%20Dashboard-0f766e?style=for-the-badge&logo=streamlit)](https://00divyanshu-system-capacity-care-load-a-appstreamlit-app-5fmusb.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Production-Enterprise%20Grade-success?style=flat-square)](#)
[![Tests](https://img.shields.io/badge/pytest-Passing-brightgreen?style=flat-square&logo=pytest)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](#)

---

### 🌐 Live Platform Access
Experience the fully deployed, interactive operational intelligence console:

👉 **[🚀 Launch Live Interactive Dashboard](https://00divyanshu-system-capacity-care-load-a-appstreamlit-app-5fmusb.streamlit.app/)**

---

## 💼 The Business Problem Solved

In high-stakes care delivery, custody management, and institutional bed networks, operations teams frequently grapple with fragmented daily intake records and delayed cross-department handoffs. When intake surges outpace discharge rates without warning, facility bed capacity is breached, emergency transfer costs skyrocket, and compliance vulnerabilities emerge.

**OpsCapacity** bridges the gap between raw, disconnected administrative logs and executive decision-making. By automating data ingestion, synthesizing real-time stress indicators, and forecasting demand up to 30 days ahead, the platform equips operations directors and planners with proactive capacity governance instead of reactive crisis response.

---

## ⚡ Key Features & Business Deliverables

| Capability | Operational Value & Commercial Deliverable |
| :--- | :--- |
| 🔄 **Automated Ingestion & Cleaning** | Ingests multi-year historical logs, reconciles date gaps, resolves stock-flow inconsistencies, and flags non-reporting intervals automatically. |
| 🚨 **Real-Time Stress & Anomaly Scoring** | Monitors net daily intake pressure, detects discharge-to-transfer deficits, computes a rolling volatility index, and categorizes system state (*Normal*, *Watch*, *Strained*, *Relief*). |
| 🎛️ **Dynamic Decision Controls** | Interactive sliders and toggles allow executives to evaluate data at Daily, Weekly, or Monthly granularity, customize rolling averages (7–30 days), and adjust forecast horizons in real time. |
| 📥 **One-Click Data Export Center** | Primary sidebar action exports the active, filtered dataset into standardized CSV reports ready for board presentations, audits, and downstream BI ingestion. |
| 📈 **Multi-Model Forecasting Engine** | Evaluates and visualizes predictive trajectory models (Prophet, XGBoost, Random Forest, Ridge Regression, Rolling Baseline) against historical ground truth. |

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RAW OPERATIONAL LOGS                            │
│           (Daily Apprehensions, Custody, Transfers, Discharges)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    INGESTION & CLEANING ENGINE                         │
│   • Schema Validation & Normalization                                  │
│   • Missing Reporting Date Imputation & Tracking                       │
│   • Stock-Flow Consistency & Anomaly Auditing                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               METRIC & STRESS AGGREGATION ENGINE                       │
│   • Net Intake Pressure (Transfers - Discharges)                       │
│   • Discharge Offset Ratio (Discharges / Transfers)                    │
│   • Care Load Volatility Index (Rolling System Std Dev)                │
│   • Automated State Classifier (Normal | Watch | Strained | Relief)    │
│   • Multi-Model Forecasting Benchmark (XGBoost, Prophet, RF)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
┌───────────────────────────────────┐ ┌───────────────────────────────────┐
│     STREAMLIT EXECUTIVE UI        │ │       EXPORT CENTER (CSV)         │
│  • Headroom-Optimized Header      │ │  • Active Filter Respecting       │
│  • Non-Truncated KPI Cards        │ │  • Granular & Rolling Averaged    │
│  • Interactive Stress Timelines   │ │  • Instant Operational Reporting  │
│  • Anomaly Deep-Dive Review       │ │                                   │
└───────────────────────────────────┘ └───────────────────────────────────┘
```

---

## 📊 Core Operational KPIs Defined

$$
\text{Total in Care} = \text{CBP Custody} + \text{HHS Care Census}
$$

$$
\text{Net Intake Pressure} = \text{Transfers In} - \text{Discharges Out}
$$

$$
\text{Discharge Ratio} = \frac{\text{Discharges Out}}{\text{Transfers In}}
$$

$$
\text{Care Load Volatility Index} = \sigma_{\tau}(\text{Total System Load})
$$

* **Backlog Risk**: Sustained periods where $\text{Net Intake Pressure} > 0$ and $\text{Discharge Ratio} < 1.0$.
* **System States**:
  * 🟢 **Normal**: Intake and discharge flows are balanced within baseline operational variance.
  * 🟡 **Watch**: Net intake is elevated or volatility exceeds standard thresholds.
  * 🔴 **Strained**: Cumulative intake exceeds discharge throughput, indicating active backlog buildup.
  * 🔵 **Relief**: Discharges significantly outpace arrivals, reducing total facility care load.

---

## 🚀 Quickstart Guide

Get the production engine running locally in 3 simple steps:

### 1. Clone the Repository
```bash
git clone https://github.com/00divyanshu/System-Capacity-Care-Load-Analytics-for-Unaccompanied-Children.git
cd "System Capacity & Care Load Analytics for Unaccompanied Children"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Interactive Platform
```bash
streamlit run app.py
```
*(Alternatively: `streamlit run app/streamlit_app.py`)*

---

### (Optional) Execute the Complete Data Pipeline
To refresh processed feature matrices, regenerate figures, and retrain forecast models:
```bash
python run_pipeline.py
```

To run the automated test suite:
```bash
python -m pytest
```

---

## 📁 Repository Structure

```text
├── app.py                     # Root Streamlit entrypoint (quickstart compatible)
├── app/
│   └── streamlit_app.py       # Production Streamlit Cloud dashboard application
├── src/
│   ├── config.py              # Centralized directory paths and parameter constants
│   ├── data_processing.py     # Ingestion, calendar alignment, and cleaning logic
│   ├── features.py            # Feature engineering, ratio modeling, and stress states
│   ├── eda.py                 # Statistical summaries, correlation, and charts
│   ├── forecasting.py         # Multi-model time-series forecasting suite
│   └── artifacts.py           # Report generator and artifact exports
├── data/
│   ├── raw/                   # Immutable raw operational logs
│   └── processed/             # Cleaned daily panel, features, and quality flags
├── outputs/
│   ├── figures/               # Standalone interactive Plotly HTML visualizations
│   ├── forecasts/             # Model predictions and comparison benchmark tables
│   └── tables/                # Summary statistics and correlation matrices
├── tests/
│   └── test_pipeline.py       # Automated unit and integration test assertions
├── requirements.txt           # Verified Python package dependencies
└── README.md                  # Commercial project documentation & executive brief
```

---

## 💼 Commercial & Advisory Engagement

This platform is architected to serve as a customizable foundation for:
- **Hospital & Health Network Bed Management**: Forecasting admissions, transfers, and length-of-stay bottlenecks.
- **Logistics & Custody Facilities**: Automated cross-department flow balancing and capacity anomaly alarms.
- **Humanitarian & NGO Field Operations**: Tracking caseload strain and intake surges in real time.

For customized deployments, proprietary database integrations (BigQuery, Snowflake, PostgreSQL), or custom forecasting algorithms, please open an issue or connect directly via GitHub.

---

*Engineered with precision for mission-critical operational intelligence.*
