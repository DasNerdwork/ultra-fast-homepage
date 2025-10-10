import os
import requests
import psycopg2
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("PSQL_USER")
DB_PASS = os.getenv("PSQL_PASS")
DB_HOST = os.getenv("PSQL_HOST")
DB_PORT = os.getenv("PSQL_PORT")
DB_NAME = os.getenv("PSQL_DB")
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

MAX_DAYS = 90
BZN = "DE-LU"  # Preiszone Deutschland-Luxemburg

# -------------------------------------
# Datenbank-Setup
# -------------------------------------
def create_table_if_not_exists():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS energy_prices_daily (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL UNIQUE,
            price_ct_per_kwh NUMERIC(10,3) NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tabelle 'energy_prices_daily' existiert oder wurde erstellt.")


def delete_old_entries():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cutoff = date.today() - timedelta(days=MAX_DAYS)
    cur.execute("""
        DELETE FROM energy_prices_daily
        WHERE date < %s
        RETURNING id
    """, (cutoff,))
    deleted = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    if deleted:
        print(f"🧹 Alte Einträge vor {cutoff} gelöscht: {len(deleted)} Einträge entfernt.")


# -------------------------------------
# Fetch-Funktion für Energy-Charts
# -------------------------------------
def fetch_energycharts_daily(start_date, end_date, zone=BZN):
    """Holt Day-Ahead Preise und mittelt sie pro Tag"""
    url = "https://api.energy-charts.info/price"
    params = {"bzn": zone, "start": start_date, "end": end_date}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("price"):
        return []

    df = pd.DataFrame({
        "timestamp": data["unix_seconds"],
        "price_eur_mwh": data["price"]
    })
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
    df["date"] = df["datetime"].dt.date
    df["price_ct_per_kwh"] = df["price_eur_mwh"] / 10  # EUR/MWh → ct/kWh

    df_daily = (
        df.groupby("date")["price_ct_per_kwh"]
        .mean()
        .round(3)
        .reset_index()
        .sort_values("date")
    )

    return [
        {"date": row["date"], "price_ct_per_kwh": row["price_ct_per_kwh"]}
        for _, row in df_daily.iterrows()
    ]


# -------------------------------------
# Daten speichern
# -------------------------------------
def save_prices_to_db(prices):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    for p in prices:
        cur.execute("""
            INSERT INTO energy_prices_daily (date, price_ct_per_kwh)
            VALUES (%s, %s)
            ON CONFLICT (date) DO UPDATE SET price_ct_per_kwh = EXCLUDED.price_ct_per_kwh
        """, (p["date"], p["price_ct_per_kwh"]))

    # Ältere Zeilen abschneiden, falls mehr als MAX_DAYS
    cur.execute("""
        DELETE FROM energy_prices_daily
        WHERE id IN (
            SELECT id FROM energy_prices_daily
            ORDER BY date DESC
            OFFSET %s
        )
    """, (MAX_DAYS,))

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM energy_prices_daily")
    count = cur.fetchone()[0]
    print(f"📈 Aktuell in DB: {count} Einträge (max {MAX_DAYS})")
    cur.close()
    conn.close()


# -------------------------------------
# Main Ablauf
# -------------------------------------
if __name__ == "__main__":
    create_table_if_not_exists()
    delete_old_entries()

    try:
        end = date.today()
        start = end - timedelta(days=MAX_DAYS)
        prices = fetch_energycharts_daily(start.isoformat(), end.isoformat())
        save_prices_to_db(prices)
        print("✅ Strompreise erfolgreich aktualisiert.")
    except Exception as e:
        print("❌ Fehler beim Abrufen oder Speichern:", e)
