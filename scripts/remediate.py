import os
from datetime import datetime

import duckdb
import requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "logipulse.duckdb")
WEBHOOK_URL = os.environ.get("LOGIPULSE_WEBHOOK_URL")


def init_remediation_table(conn):
    """Create the tracking table used to keep the workflow idempotent."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS main.sent_coupons (
            order_id VARCHAR PRIMARY KEY,
            sent_at VARCHAR,
            coupon_code VARCHAR
        )
        """
    )


def run_remediation():
    """Send coupon payloads for severe delays that were not processed yet."""
    if not os.path.exists(DB_PATH):
        print(f"Error: database file not found at '{DB_PATH}'.")
        print("Run 'python scripts/main.py' and 'dbt run' first.")
        return

    if not WEBHOOK_URL:
        print("Warning: LOGIPULSE_WEBHOOK_URL is not set.")
        print("Running in simulation mode and printing payloads to the console.\n")

    conn = duckdb.connect(DB_PATH)
    init_remediation_table(conn)

    query = """
        SELECT d.order_id, d.user_id, d.delay_minutes
        FROM main.fct_deliveries d
        LEFT JOIN main.sent_coupons c ON d.order_id = c.order_id
        WHERE d.is_severely_delayed = TRUE
          AND c.order_id IS NULL
        ORDER BY d.delay_minutes DESC, d.order_id
    """

    try:
        pending_incidents = conn.execute(query).fetchall()
    except Exception as exc:
        print(f"Error querying the mart table: {exc}")
        print("Run 'dbt run' before executing this script.")
        conn.close()
        return

    if not pending_incidents:
        print("No new incidents found for remediation.")
        conn.close()
        return

    print(f"Found {len(pending_incidents)} new incidents to process.")

    for order_id, user_id, delay_minutes in pending_incidents:
        coupon_code = f"DISCULPA{int(delay_minutes)}MIN"
        payload = {
            "event_type": "operational_delay_remediation",
            "user_id": user_id,
            "order_id": order_id,
            "delay_minutes": int(delay_minutes),
            "coupon_code": coupon_code,
            "processed_at": datetime.utcnow().isoformat(),
        }

        success = True

        if WEBHOOK_URL:
            try:
                response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
                if response.status_code in (200, 201, 202, 204):
                    print(f"Sent coupon {coupon_code} for order {order_id}.")
                else:
                    print(
                        f"Failed to send order {order_id}. HTTP status: {response.status_code}"
                    )
                    success = False
            except Exception as exc:
                print(f"Network error sending order {order_id}: {exc}")
                success = False
        else:
            print(f"[SIMULATED] Coupon {coupon_code} generated for user {user_id}.")

        if success:
            conn.execute(
                """
                INSERT INTO main.sent_coupons (order_id, sent_at, coupon_code)
                VALUES (?, ?, ?)
                """,
                (order_id, datetime.utcnow().isoformat(), coupon_code),
            )

    conn.close()
    print("\nReverse ETL remediation process completed.")


if __name__ == "__main__":
    run_remediation()
