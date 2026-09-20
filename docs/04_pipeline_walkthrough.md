# Pipeline Walkthrough

## 1. Extraction (`extract.py`)
**What it does:** Reaches out to the source API simulator, downloads JSON data, saves it locally, and converts it into Pandas DataFrames.
**Concept:** **Batch vs. Streaming**. We pull data in discrete "batches" (e.g., daily) rather than keeping a continuous streaming connection open.
**Concept:** **Storage Layers (Raw)**. Saving raw JSON payloads acts as our 'Bronze' layer, allowing us to replay the pipeline without re-querying the API.

## 2. Transformation (`transform.py`)
**What it does:** Cleans the data, parses dates, calculates derived columns (like wait times), and hashes PHI.
**Concept:** **ETL vs. ELT**. We are doing ETL (Extract, Transform, Load) by transforming the data in Python (pandas) *before* loading it into the database. An ELT approach would load raw data into MySQL first, then transform it using SQL.

## 3. Validation (`validate.py`)
**What it does:** Runs a rules engine against the DataFrames to ensure data integrity.
**Concept:** **Data Quality Gates**. Like a bouncer at a club, the validation gate checks IDs (data constraints). If critical rules fail, the pipeline stops.

## 4. Loading (`load.py`)
**What it does:** Opens a connection to MySQL and writes the DataFrames to the Star Schema tables.
**Concept:** **Idempotency**. An operation is idempotent if running it once has the same effect as running it multiple times. We use "UPSERTs" (Update or Insert) so that re-running the pipeline updates existing rows instead of duplicating them.

## 5. Orchestration (`pipeline.py`)
**What it does:** The main script that glues all the stages together, generating run IDs, logging execution times, and catching errors.
**Concept:** **Orchestration**. Coordinating the dependency graph of tasks (Extract -> Transform -> Validate -> Load).

---

## The 6 Critical Bug Fixes (Mentor Code vs Production Code)

The mentor's reference codebase (`Calibo_ETL_Pipeline`) contained several dangerous bugs. Here is how we fixed them:

### 1. `validate.py`: The Silent Pass Bug
**Bug:** The `.all` property was missing parentheses, meaning it evaluated to a function reference (which is always Truthy) rather than executing the check.
**Before:** `if (df['age'] > 0).all:`
**After:** `if (df['age'] > 0).all():`
**Why it matters:** Bad data was silently passing validation, polluting the downstream warehouse.

### 2. `transform.py`: Malformed f-string
**Bug:** Missing the `f` prefix on a format string.
**Before:** `print("Transformed Shape:{df.shape}")`
**After:** `print(f"Transformed Shape: {df.shape}")`
**Why it matters:** Logs were printing literal string text rather than the actual dataframe dimensions, making debugging impossible.

### 3. `extract.py`: Malformed Print Statement
**Bug:** Misuse of `len(df.columns)` and missing spaces.
**Before:** `print("Extracted"+str(len(df))+"rows and"+str(len(df.columns))+"cols")`
**After:** `print(f"Extracted {len(df)} rows and {len(df.columns)} cols")`
**Why it matters:** Poor readability and unpythonic code.

### 4. `config.py`: Hardcoded Secrets
**Bug:** Database passwords were in plaintext in the code.
**Before:** `DB_PASS = "root123"`
**After:** `DB_PASS = os.getenv("DB_PASS")`
**Why it matters:** A massive security vulnerability. Passwords committed to version control can lead to data breaches. We moved secrets to a `.env` file.

### 5. `load.py`: The Destructive Load
**Bug:** `if_exists="replace"` in pandas `to_sql` drops the entire database table and recreates it every time the pipeline runs.
**Before:** `df.to_sql(table, engine, if_exists="replace")`
**After:** Implemented an SQLAlchemy UPSERT (Insert on Duplicate Key Update).
**Why it matters:** Dropping tables destroys historical data. Upserts allow incremental loads and maintain table constraints/indexes.

### 6. `validate.py`: Assert-based Validation
**Bug:** Using `assert` statements meant the pipeline crashed instantly on the first error, losing visibility into other data issues.
**Before:** `assert df['id'].is_unique`
**After:** Built a rules engine that evaluates all rules, logs failures to `data_quality_results`, and decides whether to halt based on severity.
**Why it matters:** Graceful error handling and comprehensive Data Observability are essential in production pipelines.
