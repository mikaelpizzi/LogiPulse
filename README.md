# LogiPulse

LogiPulse is an end-to-end local modern data stack pipeline built with DuckDB, dbt Core,
Streamlit, and Python. It detects last-mile delivery incidents, runs CI data tests,
visualizes operational KPIs, and triggers customer compensation webhooks (Reverse ETL).

## Project layout

- app.py: Streamlit operational dashboard.
- scripts/main.py: deterministic data generator and ingestion.
- scripts/remediate.py: reverse ETL remediation with idempotency.
- dbt_project/: dbt models, profiles, and tests.

## Local setup

1) Create and activate a virtual environment (Python 3.10 recommended).
2) Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the pipeline

1) Generate mock data:

```bash
python scripts/main.py
```

2) Run dbt models and tests:

```bash
cd dbt_project
dbt debug --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
cd ..
```

3) Launch the dashboard:

```bash
streamlit run app.py
```

## Reverse ETL (optional)

Set a webhook URL to send payloads. If not set, the script runs in simulation mode.

```bash
export LOGIPULSE_WEBHOOK_URL="https://webhook.site/your-id"
python scripts/remediate.py
```

## Commit workflow

Use frequent, atomic commits. Recommended stages:

- env setup and requirements
- ingestion script
- dbt configuration
- staging model
- intermediate and mart models
- dbt tests
- dashboard
- remediation
