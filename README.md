# LogiPulse

LogiPulse is a local modern data stack pipeline built with DuckDB, dbt Core, Streamlit,
and Python. It simulates last-mile deliveries, detects critical delays, validates data
quality in CI, and triggers compensation webhooks (Reverse ETL).

This repository is fully local-first: no cloud accounts, no external databases, and
no paid services. Everything runs on your machine.

## Architecture summary

1) Ingestion (Python) generates deterministic events into DuckDB.
2) Transformation (dbt) models data in three layers: staging, intermediate, marts.
3) Analytics (Streamlit) reads the final mart table and shows KPIs and incident detail.
4) Remediation (Reverse ETL) sends a coupon payload for delayed orders with idempotency.

## Project layout

- app.py: Streamlit operational dashboard with bilingual UI and light/dark modes.
- scripts/main.py: deterministic data generator and ingestion.
- scripts/remediate.py: reverse ETL remediation with idempotency tracking.
- dbt_project/: dbt models, profiles, and tests.
- .github/workflows/dbt_ci.yml: CI pipeline for dbt debug/run/test.

## Data contract (core fields)

Raw table: raw_orders

- order_id (varchar)
- user_id (varchar)
- driver_id (varchar)
- status (varchar)
- amount (double)
- created_at (varchar, ISO 8601)
- estimated_delivery_minutes (integer)
- actual_delivery_minutes (integer, nullable)

Mart table: fct_deliveries

- order_id
- user_id
- driver_id
- amount
- created_at
- delay_minutes
- is_severely_delayed (true if delay_minutes > 15)

## Local setup

### Python version

Use Python 3.10. dbt 1.7/1.8 is not compatible with Python 3.13.

### Create venv and install dependencies

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

WSL (Ubuntu or other Linux distros):

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the pipeline (E2E)

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

WSL note: the dbt and Streamlit commands are the same in WSL.

## Reverse ETL (optional)

If LOGIPULSE_WEBHOOK_URL is not set, the script runs in simulation mode and prints
payloads to the console.

Windows PowerShell:

```bash
$env:LOGIPULSE_WEBHOOK_URL="https://webhook.site/your-id"
python scripts/remediate.py
```

macOS / Linux:

```bash
export LOGIPULSE_WEBHOOK_URL="https://webhook.site/your-id"
python scripts/remediate.py
```

WSL (Ubuntu or other Linux distros):

```bash
export LOGIPULSE_WEBHOOK_URL="https://webhook.site/your-id"
python scripts/remediate.py
```

Idempotency: if you run the script again, it should not resend the same incidents.

## Dashboard features

- Bilingual UI (English and Espanol).
- Light and dark theme toggle.
- Filters for date window, delay range, and critical-only view.
- KPI cards, delay distribution, and delay trend charts.

## Demo script (5 minutes)

Run this sequence from the project root to demonstrate the full flow:

```bash
python scripts/main.py
cd dbt_project
dbt run --profiles-dir .
dbt test --profiles-dir .
cd ..
streamlit run app.py
```

Optional remediation demo (simulation mode):

```bash
python scripts/remediate.py
```

WSL note: use the same commands as macOS/Linux in WSL.

## CI pipeline

The GitHub Actions workflow runs on push and pull requests to main:

1) Install Python dependencies.
2) Generate a local DuckDB database with mock data.
3) Run dbt debug, run, and test.

File: .github/workflows/dbt_ci.yml

## Troubleshooting

- If pip install hangs, confirm Python 3.10 is active: python --version.
- If dbt cannot find profiles, run dbt with --profiles-dir . inside dbt_project.
- If the dashboard shows no data, rerun scripts/main.py and dbt run.
- If remediation sends duplicates, delete main.sent_coupons or check the join logic.

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
