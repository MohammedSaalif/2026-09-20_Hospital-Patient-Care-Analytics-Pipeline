# Problem and Scope

## Case Study Narrative

"St. Jude Medical Center" is a mid-sized healthcare provider struggling with a common industry challenge: fragmented data. Patient demographics are stored in a legacy SQL database, appointments are tracked in a scheduling system, lab results are delivered via flat files, and newer initiatives like wearable health monitoring exist in isolated silos. 

When a patient arrives for an appointment, doctors lack a unified view of their recent lab results and wearable data. Furthermore, hospital administrators have no reliable way to track operational bottlenecks, such as department wait times or patient no-show rates. 

The data engineering team was tasked with building an automated, scalable analytics pipeline to consolidate these sources. However, the initial prototype (provided by a mentor) was riddled with bugs: it lacked robust data validation, mishandled database writes (dropping tables on every run), and failed to secure Protected Health Information (PHI).

This project aims to deliver a production-grade ETL/ELT pipeline that securely integrates this data into a centralized Star Schema data warehouse, applies rigorous data quality gates, calculates patient risk scores, and exposes this curated data through a Serving API and an Executive Dashboard.

## Scope Boundaries

### In-Scope
- **Data Ingestion**: Automated extraction of synthetic data from simulated source APIs (patients, appointments, labs, wearables).
- **Data Processing**: Transformation and cleaning using `pandas`.
- **Data Quality**: Implementation of a validation rules engine (e.g., checking for nulls, range constraints) with soft/critical failure gates.
- **Data Governance**: Masking PHI (names, phone numbers) using SHA-256 hashing before loading into the warehouse.
- **Storage**: Loading curated data into a MySQL Star Schema using idempotent upserts.
- **Serving Layer**: A FastAPI application to serve queries (e.g., Patient 360, High-Risk patients).
- **Visualization**: A Streamlit dashboard consuming the serving API for executive and clinical insights.
- **Bug Fixes**: Rectifying all known issues in the mentor's reference codebase.

### Out-of-Scope
- **Real-time Streaming**: Data is processed in micro-batches; true real-time streaming (e.g., Kafka) is not implemented.
- **Machine Learning Models**: The risk scoring is rule-based; predictive ML models are outside the current scope.
- **Complex Authentication**: OAuth/JWT for the APIs and Dashboards is mocked or excluded for simplicity.
- **Cloud Deployment**: The current project is designed to run locally (Localhost/Docker) for presentation purposes; cloud provisioning (AWS/GCP) is not covered.

## Assumptions

1. **Data Availability**: The source data simulator (FastAPI `/source/*` endpoints) will be highly available during pipeline execution.
2. **Schema Stability**: The structure of the incoming JSON data from the source systems will not change abruptly without versioning.
3. **Local Environment**: The user has MySQL installed locally or running via Docker, with credentials matching the `.env` configuration.
4. **Data Volume**: The data volume is small enough to fit into memory for Pandas processing. For larger datasets, a transition to PySpark or a pure ELT push-down approach would be required.
5. **Idempotency**: The primary keys provided by the source systems (e.g., `patient_id`) are reliable and can be used to perform UPSERT operations in the warehouse safely.
