import os
import requests
import psycopg2
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("PSQL_USER")
DB_PASS = os.getenv("PSQL_PASS")
DB_HOST = os.getenv("PSQL_HOST")
DB_PORT = os.getenv("PSQL_PORT")
DB_NAME = os.getenv("PSQL_DB")
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

MAX_DAYS = 90

def create_table_if_not_exists():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS heizoel_prices_daily (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL UNIQUE,
            price_eur NUMERIC(10, 3) NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Tabelle 'heizoel_prices_daily' existiert oder wurde erstellt.")


def delete_old_entries():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cutoff = date.today() - timedelta(days=MAX_DAYS)
    cur.execute("DELETE FROM heizoel_prices_daily WHERE date < %s RETURNING id", (cutoff,))
    deleted = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    if deleted:
        print(f"🧹 Alte Einträge gelöscht: {len(deleted)} vor {cutoff}")


def fetch_heizoel_prices(days: int = MAX_DAYS):
    min_date = (datetime.today() - timedelta(days=days)).strftime("%m-%d-%Y")
    max_date = datetime.today().strftime("%m-%d-%Y")

    url = (
        f"https://www.heizoel24.de/api/chartapi/GetAveragePriceHistory"
        f"?countryId=1&minDate={min_date}&maxDate={max_date}"
    )
    headers = {
        'Origin': 'https://www.heizoel24.de',
        'Referer': 'https://www.heizoel24.de/',
        'User-Agent': 'Mozilla/5.0'
    }

    print(f"📡 Lade Heizölpreise von {min_date} bis {max_date} ...")
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    values = data.get("Values", [])
    prices = []
    for entry in values:
        try:
            # Timestamp in Sekunden umwandeln
            d = datetime.fromtimestamp(entry["date"] / 1000).date()
            prices.append({
                "date": d,
                "price_eur": round(entry["value"], 3)
            })
        except Exception as e:
            print("⚠️ Fehler bei Eintrag:", e)
            continue

    print(f"✅ {len(prices)} Tagespreise geladen.")
    return prices


def save_prices_to_db(prices):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    for p in prices:
        cur.execute("""
            INSERT INTO heizoel_prices_daily (date, price_eur)
            VALUES (%s, %s)
            ON CONFLICT (date) DO UPDATE SET price_eur = EXCLUDED.price_eur;
        """, (p["date"], p["price_eur"]))

    conn.commit()
    cur.close()
    conn.close()
    print(f"💾 {len(prices)} Preise gespeichert/aktualisiert.")


if __name__ == "__main__":
    create_table_if_not_exists()
    delete_old_entries()
    try:
        prices = fetch_heizoel_prices()
        save_prices_to_db(prices)
    except Exception as e:
        print("❌ Fehler beim Abrufen oder Speichern:", e)
