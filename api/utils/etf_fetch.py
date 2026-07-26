import os
import psycopg2
import yfinance as yf
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

# ETFs und zugehörige Tabellen
ETFS = {
    "spdr_prices_daily": "SPPW.DE",
    "vaneck_prices_daily": "SMH.DE",
    "xtrackers_prices_daily": "XDWD.DE"
}

def create_table_if_not_exists(table_name):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL UNIQUE,
            price_eur NUMERIC(20,3) NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Tabelle '{table_name}' existiert oder wurde erstellt.")

def delete_old_entries(table_name):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cutoff = date.today() - timedelta(days=MAX_DAYS)
    cur.execute(f"""
        DELETE FROM {table_name}
        WHERE date < %s
        RETURNING id
    """, (cutoff,))
    deleted = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    if deleted:
        print(f"Alte Einträge vor {cutoff} in {table_name} gelöscht: {len(deleted)} Einträge entfernt.")

def fetch_etf_prices(ticker):
    """Holt die letzten MAX_DAYS historischen Schlusskurse des ETFs und füllt fehlende Tage."""
    end_date = date.today()
    start_date = end_date - timedelta(days=MAX_DAYS)

    etf = yf.Ticker(ticker)
    data = etf.history(start=start_date, end=end_date)

    if data.empty or 'Close' not in data.columns:
        print(f"⚠️ Keine Daten von yfinance für {ticker} erhalten, überspringe.")
        return []

    df = data[['Close']].reset_index()
    df.rename(columns={'Date': 'date', 'Close': 'price_eur'}, inplace=True)
    df['date'] = df['date'].dt.date
    df['price_eur'] = df['price_eur'].round(3)

    # Alle Kalendertage generieren und fehlende Preise füllen
    all_dates = pd.date_range(start=start_date, end=end_date).date
    df_all = pd.DataFrame({'date': all_dates})
    df_merged = df_all.merge(df, on='date', how='left')
    df_merged['price_eur'] = df_merged['price_eur'].ffill().bfill()

    # NaN-Zeilen dürfen NIE in die DB (Postgres NUMERIC akzeptiert NaN,
    # kaputtes JSON in der API wäre die Folge)
    df_merged = df_merged.dropna(subset=['price_eur'])

    return df_merged.to_dict('records')

def save_prices_to_db(table_name, prices):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    for p in prices:
        cur.execute(f"""
            INSERT INTO {table_name} (date, price_eur)
            VALUES (%s, %s)
            ON CONFLICT (date) DO UPDATE SET price_eur = EXCLUDED.price_eur
        """, (p["date"], p["price_eur"]))

    # Sicherstellen, dass nur MAX_DAYS Einträge in der Tabelle sind
    cur.execute(f"""
        DELETE FROM {table_name}
        WHERE id IN (
            SELECT id FROM {table_name}
            ORDER BY date DESC
            OFFSET %s
        )
    """, (MAX_DAYS,))

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    for table_name, ticker in ETFS.items():
        print(f"\nVerarbeite {table_name} ({ticker}) …")
        try:
            create_table_if_not_exists(table_name)
            delete_old_entries(table_name)
            prices = fetch_etf_prices(ticker)
            if not prices:
                print(f"Keine Preise für {ticker}, Tabelle bleibt unverändert.")
                continue
            save_prices_to_db(table_name, prices)
            print(f"{len(prices)} Einträge gespeichert in {table_name}")
        except Exception as e:
            print(f"❌ Fehler bei {table_name} ({ticker}): {e}")