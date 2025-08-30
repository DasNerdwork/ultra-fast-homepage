import os
import requests
import psycopg2
from datetime import date, timedelta
from dotenv import load_dotenv
import random

load_dotenv()

DB_USER = os.getenv("PSQL_USER")
DB_PASS = os.getenv("PSQL_PASS")
DB_HOST = os.getenv("PSQL_HOST")
DB_PORT = os.getenv("PSQL_PORT")
DB_NAME = os.getenv("PSQL_DB")
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
API_KEY = os.getenv("TANKERKOENIG_API_KEY")
STATION_ID = os.getenv("TANKERKOENIG_STATION_ID")
MAX_DAYS = 90

def create_table_if_not_exists():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Prüfen, ob Tabelle schon existiert
    cur.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables 
            WHERE table_name = 'daily_prices'
        )
    """)
    exists = cur.fetchone()[0]

    if not exists:
        cur.execute("""
            CREATE TABLE daily_prices (
                id SERIAL PRIMARY KEY,
                station_id VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                e5 NUMERIC(5,3),
                e10 NUMERIC(5,3),
                diesel NUMERIC(5,3),
                UNIQUE (station_id, date)
            );
        """)
        conn.commit()
        print("Tabelle daily_prices neu erstellt.")

        # Tabelle direkt mit Testwerten für die letzten MAX_DAYS füllen
        today = date.today()
        for i in range(MAX_DAYS-1):
            d = today - timedelta(days=MAX_DAYS - i)
            cur.execute("""
                INSERT INTO daily_prices (station_id, date, e5, e10, diesel)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                STATION_ID,
                d,
                round(random.uniform(1.50, 1.70), 3),
                round(random.uniform(1.50, 1.70), 3),
                round(random.uniform(1.40, 1.60), 3)
            ))
        conn.commit()
        print(f"Tabelle mit {MAX_DAYS} Testeinträgen geseedet.")
    else:
        print("Tabelle existiert bereits.")

    cur.close()
    conn.close()


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
    print(f"Alte Einträge vor {cutoff} gelöscht: {len(deleted)} Einträge entfernt.")


def fetch_petrol_prices():
    url = f"https://creativecommons.tankerkoenig.de/json/detail.php?id={STATION_ID}&apikey={API_KEY}"
    resp = requests.get(url)
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

    cur.execute("""
        INSERT INTO daily_prices (station_id, date, e5, e10, diesel)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (station_id, date) DO UPDATE
        SET e5 = EXCLUDED.e5,
            e10 = EXCLUDED.e10,
            diesel = EXCLUDED.diesel
        RETURNING xmax
    """, (
        STATION_ID,
        today,
        prices.get("e5"),
        prices.get("e10"),
        prices.get("diesel")
    ))

    result = cur.fetchone()
    action = "NEU erstellt" if result and result[0] == 0 else "aktualisiert"
    print(f"Eintrag für {today} {action}: {prices}")

    # Sicherstellen, dass max. MAX_DAYS Einträge in der Tabelle sind
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
        print(f"Zusätzliche alte Einträge entfernt, um {MAX_DAYS}-Tage-Limit einzuhalten: {len(deleted_extra)} Einträge gelöscht.")

    cur.execute("SELECT COUNT(*) FROM daily_prices WHERE station_id = %s", (STATION_ID,))
    count = cur.fetchone()[0]
    print(f"Aktuell in der Tabelle: {count} Einträge für diese Station (max {MAX_DAYS})")

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
