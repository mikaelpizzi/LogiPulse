import argparse
import os
import random
import time
from datetime import datetime, timedelta

import duckdb

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "logipulse.duckdb")
RANDOM_SEED = 42
BASE_TIME = datetime(2026, 5, 29, 8, 0, 0)


def init_database():
    """Create the local DuckDB file and the raw_orders table if needed."""
    print(f"Connecting to local database at: {DB_PATH}")
    conn = duckdb.connect(DB_PATH)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_orders (
            order_id VARCHAR PRIMARY KEY,
            user_id VARCHAR,
            driver_id VARCHAR,
            status VARCHAR,
            amount DOUBLE,
            created_at VARCHAR,
            estimated_delivery_minutes INTEGER,
            actual_delivery_minutes INTEGER
        )
        """
    )
    conn.close()
    print("Database and raw table initialized successfully.")


def generate_mock_events(num_orders=200, seed=RANDOM_SEED):
    """Generate deterministic delivery events that follow the project contract."""
    rng = random.Random(seed)
    orders = []
    statuses = [
        "DELIVERED",
        "DELIVERED",
        "DELIVERED",
        "CANCELLED",
        "CREATED",
        "ASSIGNED",
        "PICKED_UP",
    ]

    for index in range(num_orders):
        order_id = f"ord_{index + 1:06d}"
        user_id = f"usr_{rng.randint(100, 999)}"
        driver_id = f"drv_{rng.randint(10, 99)}"
        status = rng.choice(statuses)
        amount = round(rng.uniform(8.0, 55.0), 2)

        order_time = BASE_TIME + timedelta(minutes=index * 15 + rng.randint(0, 20))
        hour = order_time.hour
        is_rush_hour = (12 <= hour <= 14) or (19 <= hour <= 21)
        estimated_delivery = rng.choice([20, 30, 40, 45])

        if status == "DELIVERED":
            if is_rush_hour:
                actual_delivery = estimated_delivery + rng.randint(5, 50)
            else:
                actual_delivery = max(10, estimated_delivery + rng.randint(-5, 12))
        else:
            actual_delivery = None

        orders.append(
            (
                order_id,
                user_id,
                driver_id,
                status,
                amount,
                order_time.isoformat(timespec="seconds"),
                estimated_delivery,
                actual_delivery,
            )
        )

    return orders


def ingest_data(seed=RANDOM_SEED):
    """Generate the mock dataset and load it into DuckDB."""
    init_database()
    conn = duckdb.connect(DB_PATH)

    conn.execute("DELETE FROM raw_orders")
    orders = generate_mock_events(200, seed=seed)

    print(f"Inserting {len(orders)} simulated orders into raw_orders...")
    conn.executemany(
        """
        INSERT OR REPLACE INTO raw_orders
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        orders,
    )

    total_rows = conn.execute("SELECT COUNT(*) FROM raw_orders").fetchone()[0]
    conn.close()

    print(f"Ingestion completed. Total rows in raw_orders: {total_rows}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--random-seed", action="store_true", help="Use current time as seed")
    args = parser.parse_args()
    
    seed = int(time.time()) if args.random_seed else RANDOM_SEED
    ingest_data(seed=seed)
