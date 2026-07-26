import os
import requests
import psycopg2
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from dotenv import load_dotenv

# .env explizit aus dem Projekt-Hauptordner laden, damit das Script
# auch im Cron-Kontext (cwd = /root) die Credentials findet
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

DB_USER = os.getenv("PSQL_USER")
DB_PASS = os.getenv("PSQL_PASS")
DB_HOST = os.getenv("PSQL_HOST")
DB_PORT = os.getenv("PSQL_PORT")
DB_NAME = os.getenv("PSQL_DB")
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
API_KEY = os.getenv("TANKERKOENIG_API_KEY")
STATION_ID = os.getenv("TANKERKOENIG_STATION_ID")
MAX_DAYS = 90

TZ = ZoneInfo("Europe/Berlin")


def is_after_noon() -> bool:
    """Seit der 12-Uhr-Regel (April 2026) gibt es faktisch zwei
    Preisphasen pro Tag: vor 12 Uhr (Tagestief) und ab 12 Uhr
    (nach der einmalig erlaubten Erhöhung)."""
    return datetime.now(TZ).hour >= 12


def create_table_if_not_exists():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            id SERIAL PRIMARY KEY,
            station_id VARCHAR(50) NOT NULL,
            date DATE NOT NULL,
            e5 NUMERIC(5,3),
            e10 NUMERIC(5,3),
            diesel NUMERIC(5,3),
            e5_high NUMERIC(5,3),
            e10_high NUMERIC(5,3),
            diesel_high NUMERIC(5,3),
            UNIQUE (station_id, date)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Tabelle 'daily_prices' existiert oder wurde erstellt.")


def delete_old_entries():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cutoff = date.today() - timedelta(days=MAX_DAYS)
    cur.execute("""
        DELETE FROM daily_prices
        WHERE date < %s AND station_id = %s
        RETURNING id
    """, (cutoff, STATION_ID))
    deleted = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    if deleted:
        print(f"Alte Einträge vor {cutoff} gelöscht: {len(deleted)} Einträge entfernt.")


def fetch_petrol_prices():
    url = f"https://creativecommons.tankerkoenig.de/json/detail.php?id={STATION_ID}&apikey={API_KEY}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    station = data.get("station", {})
    if not station.get("isOpen", False):
        print("Tankstelle geschlossen, keine Preise erfasst.")
        return None

    prices = {}
    for fuel_type in ["e5", "e10", "diesel"]:
        price = station.get(fuel_type)
        if price:
            prices[fuel_type] = round(price, 3)
    return prices if prices else None


def save_prices_to_db(prices: dict):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    today = date.today()

    if is_after_noon():
        # Nachmittagslauf: High-Spalten schreiben (Preis nach der 12-Uhr-Erhöhung)
        cur.execute("""
            INSERT INTO daily_prices (station_id, date, e5_high, e10_high, diesel_high)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (station_id, date) DO UPDATE
            SET e5_high = EXCLUDED.e5_high,
                e10_high = EXCLUDED.e10_high,
                diesel_high = EXCLUDED.diesel_high
        """, (STATION_ID, today, prices.get("e5"), prices.get("e10"), prices.get("diesel")))
        print(f"Eintrag für {today} (ab 12 Uhr / high): {prices}")
    else:
        # Vormittagslauf: Low-Spalten schreiben (Tagestief kurz vor 12)
        cur.execute("""
            INSERT INTO daily_prices (station_id, date, e5, e10, diesel)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (station_id, date) DO UPDATE
            SET e5 = EXCLUDED.e5,
                e10 = EXCLUDED.e10,
                diesel = EXCLUDED.diesel
        """, (STATION_ID, today, prices.get("e5"), prices.get("e10"), prices.get("diesel")))
        print(f"Eintrag für {today} (vor 12 Uhr / low): {prices}")

    # Max. MAX_DAYS Einträge behalten
    cur.execute("""
        DELETE FROM daily_prices
        WHERE id IN (
            SELECT id FROM daily_prices
            WHERE station_id = %s
            ORDER BY date DESC
            OFFSET %s
        )
        RETURNING id
    """, (STATION_ID, MAX_DAYS))
    deleted_extra = cur.fetchall()
    if deleted_extra:
        print(f"{len(deleted_extra)} alte Einträge entfernt ({MAX_DAYS}-Tage-Limit).")

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    create_table_if_not_exists()
    delete_old_entries()

    try:
        price = fetch_petrol_prices()
        if price:
            save_prices_to_db(price)
        else:
            print("Konnte Preise nicht abrufen.")
    except Exception as e:
        print("Fehler beim Abrufen:", e)