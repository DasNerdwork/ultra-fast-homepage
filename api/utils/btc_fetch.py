import os
import requests
import psycopg2
from datetime import date, datetime, timedelta, timezone
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
        CREATE TABLE IF NOT EXISTS btc_prices_daily (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL UNIQUE,
            price_eur NUMERIC(20,2) NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Tabelle 'btc_prices_daily' existiert oder wurde erstellt.")


def delete_old_entries():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cutoff = date.today() - timedelta(days=MAX_DAYS)
    cur.execute("""
        DELETE FROM btc_prices_daily
        WHERE date < %s
        RETURNING id
    """, (cutoff,))
    deleted = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    if deleted:
        print(f"Alte Einträge vor {cutoff} gelöscht: {len(deleted)} Einträge entfernt.")


def fetch_btc_prices():
    """Holt die letzten MAX_DAYS historischen Preise + aktuellen Preis"""
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "eur", "days": MAX_DAYS, "interval": "daily"}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # DataFrame ähnlich wie petrol_fetch
    prices = []
    for ts, price in data.get("prices", []):
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date()
        prices.append({"date": dt, "price_eur": round(price, 2)})

    # Sicherstellen, dass heutiger Preis aktuell ist
    today = date.today()
    if not any(p["date"] == today for p in prices):
        # aktueller Preis
        url_current = "https://api.coingecko.com/api/v3/simple/price"
        resp_current = requests.get(url_current, params={"ids": "bitcoin", "vs_currencies": "eur"}, timeout=15)
        resp_current.raise_for_status()
        current_price = resp_current.json()["bitcoin"]["eur"]
        prices.append({"date": today, "price_eur": round(current_price, 2)})

    return prices


def save_prices_to_db(prices):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    for p in prices:
        cur.execute("""
            INSERT INTO btc_prices_daily (date, price_eur)
            VALUES (%s, %s)
            ON CONFLICT (date) DO UPDATE SET price_eur = EXCLUDED.price_eur
        """, (p["date"], p["price_eur"]))

    # Sicherstellen, dass nur MAX_DAYS Einträge in der Tabelle sind
    cur.execute("""
        DELETE FROM btc_prices_daily
        WHERE id IN (
            SELECT id FROM btc_prices_daily
            ORDER BY date DESC
            OFFSET %s
        )
    """, (MAX_DAYS,))

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM btc_prices_daily")
    count = cur.fetchone()[0]
    print(f"In der Tabelle aktuell: {count} Einträge (max {MAX_DAYS})")
    cur.close()
    conn.close()


if __name__ == "__main__":
    create_table_if_not_exists()
    delete_old_entries()

    try:
        prices = fetch_btc_prices()
        save_prices_to_db(prices)
    except Exception as e:
        print("Fehler beim Abrufen oder Speichern:", e)
