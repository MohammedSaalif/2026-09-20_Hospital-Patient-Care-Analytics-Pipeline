# Presentation Guide & Script

## 10-12 Slide Outline with Speaker Notes

**Slide 1: Title Slide**
*   *Content*: Hospital Patient Care Analytics Pipeline. Student Name.
*   *Speaker Notes*: "Hello everyone. Today I'll present my Data Engineering project, building an automated analytics pipeline for St. Jude Medical Center."

**Slide 2: The Problem (CBIM Context)**
*   *Content*: Siloed data (EHR, Labs, Wearables), poor data quality, buggy legacy code.
*   *Speaker Notes*: "The hospital struggled with fragmented systems. Doctors couldn't get a unified view of patient health, and the legacy codebase provided to us had critical bugs that corrupted data and exposed PHI."

**Slide 3: End-to-End Architecture**
*   *Content*: Mermaid Architecture Diagram from `02_architecture.md`.
*   *Speaker Notes*: "This is the architecture I designed. We extract from source APIs, perform ETL using Pandas, validate through strict quality gates, and load into a MySQL Star Schema, which serves a FastAPI backend and Streamlit dashboard."

**Slide 4: Data Modeling (Star Schema)**
*   *Content*: ER Diagram showing Fact and Dimension tables.
*   *Speaker Notes*: "I modeled the warehouse using a Star Schema. Dimensions like Patient and Doctor provide context, while Fact tables capture events like Appointments and Wearable readings, optimized for fast analytics."

**Slide 5: Data Quality & Validation Gates**
*   *Content*: Soft vs Critical rules.
*   *Speaker Notes*: "We don't just load data blindly. I implemented a rules engine. Critical failures like missing IDs stop the pipeline. Soft failures log warnings but let the healthy data through."

**Slide 6: Security & Governance (PHI Masking)**
*   *Content*: SHA-256 hashing explanation.
*   *Speaker Notes*: "To comply with data privacy standards, I implemented SHA-256 hashing on names and phone numbers during the transform phase, ensuring PII is secured before hitting the warehouse."

**Slide 7: Fixing the Mentor's Code (Top 3 Bugs)**
*   *Content*: Show before/after for `replace` -> `upsert`, missing parentheses in validation, and plaintext passwords.
*   *Speaker Notes*: "The baseline code had issues. Most importantly, it used 'replace' which dropped tables every run. I rewrote the loading logic to use idempotent UPSERTs, preserving historical data."

**Slide 8: The Serving Layer (FastAPI)**
*   *Content*: API Endpoints overview.
*   *Speaker Notes*: "To serve the data, I built a RESTful API using FastAPI. It handles routing, HTTP status codes, and provides a clean interface between the database and the frontend."

**Slide 9: Executive Dashboard (Streamlit)**
*   *Content*: Screenshot of the dashboard.
*   *Speaker Notes*: "Finally, stakeholders consume this data via a Streamlit dashboard, providing high-level KPIs and detailed Patient 360 views."

**Slide 10: Live Demo**
*   *Content*: "Demo Time"

**Slide 11: Future Enhancements**
*   *Content*: Airflow scheduling, PySpark for big data, Cloud deployment.
*   *Speaker Notes*: "To scale this for production, I would migrate orchestration to Airflow, use PySpark instead of Pandas for larger volumes, and deploy on AWS."

**Slide 12: Q&A**
*   *Content*: "Questions?"

---

## 5-Minute Demo Script

1.  **Start in the Terminal**: Show the empty database.
2.  **Trigger Pipeline**: Run `python src/hospital_pipeline/pipeline.py`. Point out the terminal logs showing Extraction, Transformation, Validation, and Loading.
3.  **Show the Database**: Open MySQL Workbench/CLI, run a quick `SELECT COUNT(*)` on `fact_appointments` to show data landed.
4.  **Idempotency Test**: Run the pipeline *again*. Show that the row counts in the database did *not* double. "Because of our UPSERT logic, the pipeline is idempotent."
5.  **Start API**: Run `uvicorn api.main:app --reload`. Open the Swagger UI in the browser (`http://localhost:8000/docs`). Execute the `/api/v1/patients/high-risk` endpoint to show the JSON response.
6.  **Start Streamlit**: Run `streamlit run app/streamlit_app.py`. Click through the Overview, Executive Dashboard, and Patient 360 pages.

---

## Likely Mentor Questions & Model Answers

**1. Why did you choose MySQL over a NoSQL database like MongoDB?**
*Answer*: Healthcare analytics requires complex aggregations and joins (e.g., joining patients with lab results and appointments). Relational databases and Star Schemas are heavily optimized for this. NoSQL is better for unstructured data, but our data is highly structured.

**2. Why batch processing (micro-batch) instead of real-time streaming?**
*Answer*: Most clinical decisions in this context (like calculating a daily risk score from wearables) don't require sub-second latency. Batching daily or hourly reduces architectural complexity and infrastructure costs compared to maintaining a Kafka cluster.

**3. How does your pipeline handle bad data?**
*Answer*: Through Validation Gates. I defined a rules catalog. If a critical rule fails (like a missing primary key), the pipeline halts to prevent warehouse corruption. If a soft rule fails (like an impossible age), it drops the row, logs it to `data_quality_results`, and continues.

**4. What is HTTP 429 and how would you handle it?**
*Answer*: 429 means "Too Many Requests" (Rate Limiting). If the source API returns a 429, my pipeline's extract function should catch it and implement an Exponential Backoff strategy—waiting a few seconds, then retrying, doubling the wait time on subsequent failures.

**5. Why did you change the pandas `to_sql` method from 'replace' to an upsert?**
*Answer*: 'Replace' drops the entire table and recreates it. In production, this destroys all historical data. Using UPSERT (Insert on Duplicate Key Update) allows us to incrementally load new records and update existing ones without losing history.

**6. How would this pipeline scale in production with 100x the data volume?**
*Answer*: Pandas runs in-memory on a single machine, so it would eventually fail (OOM errors). To scale, I would replace Pandas with PySpark for distributed processing, and migrate from local MySQL to a cloud data warehouse like Snowflake or AWS Redshift.

**7. What is idempotency and why is it important in Data Engineering?**
*Answer*: Idempotency means an operation produces the same result whether executed once or multiple times. It's crucial because pipelines inevitably fail and need to be re-run. If a pipeline isn't idempotent, re-running it will create duplicate records and ruin analytics.

**8. Why validate data *before* loading it? Why not load it all and clean it later?**
*Answer*: We are using an ETL pattern. Validating before loading protects the Data Warehouse (the "Gold" layer) from being polluted. If stakeholders query the warehouse and see garbage data, trust in the data team is lost. We stop garbage at the gate.

**9. Explain your Star Schema design. What's the difference between a Fact and a Dimension?**
*Answer*: Dimensions are the "nouns" (Patients, Doctors) containing descriptive attributes used for filtering. Facts are the "verbs" or events (Appointments, Lab Results) containing measurable numbers (Wait time, HR) and foreign keys to dimensions.

**10. How did you handle Protected Health Information (PHI)?**
*Answer*: I implemented a one-way SHA-256 hashing algorithm on identifying columns like names and phone numbers during the transformation phase. This allows us to track unique patients and join tables without exposing their actual identities in the warehouse.

**11. What is the Medallion Architecture and how does your project relate?**
*Answer*: It's a data design pattern (Bronze, Silver, Gold). My project mimics this: the `data/raw/` JSON files are Bronze (immutable source), the in-memory cleaned Pandas dataframes are Silver, and the MySQL Star Schema is the Gold layer serving business users.

**12. What would change if you connected this to real hospital data instead of a simulator?**
*Answer*: Security would be vastly stricter (VPNs, strict RBAC, no local `.env` files). Data volumes would be larger, requiring Spark. Also, real hospital data formats like HL7 or FHIR would require much more complex parsing logic than our simple JSON payloads.
