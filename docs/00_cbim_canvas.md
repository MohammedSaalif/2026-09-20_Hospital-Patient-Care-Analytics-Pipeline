# CBIM Problem Canvas

## Problem Canvas

| Element | Description |
| :--- | :--- |
| **Situation** | The hospital currently relies on siloed data systems (EHR, lab results, wearables) preventing a unified view of patient health and operational metrics. Data extraction is manual and prone to errors. |
| **Question** | How can we automate the integration, validation, and serving of multi-source patient data to improve risk assessment and clinical decision-making? |
| **Complication** | Data is often dirty or incomplete. Privacy regulations require masking Protected Health Information (PHI). Mentor's reference code had critical bugs (e.g., dropping tables instead of upserting) and poor validation logic. |
| **Success** | - 99% automated data ingestion (Assumption: Simulator reliability). <br> - 100% PHI masked before data warehouse loading. <br> - Pipeline runs idempotently without data duplication. <br> - Sub-second API response for patient queries. |
| **Stakeholders** | **Data Engineers**: Need scalable, reliable pipelines. <br> **Clinicians**: Need accurate, timely patient risk profiles. <br> **Hospital Admin**: Need operational insights (wait times, no-shows). |
| **Single Source of Truth** | A centralized MySQL data warehouse modeled as a Star Schema, serving as the definitive source for BI tools and serving APIs. |

## Stakeholder Needs Matrix

| Stakeholder | Primary Need | Secondary Need | Pain Point Addressed |
| :--- | :--- | :--- | :--- |
| **Data Engineers** | Maintainable pipeline code | Clear error logging and data quality gates | Buggy mentor code, manual ETL jobs |
| **Clinicians** | Accurate Patient 360 views | Identification of High-Risk patients | Siloed data, delayed lab results |
| **Hospital Admin** | Operational Dashboards | Resource utilization metrics (wait times) | Inability to track department efficiency |

## How the Canvas Drives Design Decisions

The CBIM (Context, Background, Issue, Method - adapted here as Situation, Question, Complication, Success) Problem Canvas acts as the foundational blueprint for the architecture. By explicitly identifying the **Complication** (dirty data, PHI concerns, and buggy legacy code), we designed a robust validation rules engine and incorporated SHA-256 hashing for data governance. The **Success** criteria mandated an idempotent pipeline design, leading to the decision to use "upsert" operations rather than full table replacements. Finally, mapping **Stakeholder Needs** directly influenced our downstream serving layer: FastAPI for sub-second clinical queries and Streamlit for administrative executive dashboards, ensuring every technical decision traces back to a business requirement.
