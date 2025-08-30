import requests
import pandas as pd
from datetime import date, timedelta

BZN = "DE-LU"  # Preiszone Deutschland-Luxemburg

def fetch_energycharts_daily(start_date, end_date, zone=BZN):
    """Holt Day-Ahead Preise und mittelt sie pro Tag"""
    url = "https://api.energy-charts.info/price"
    params = {
        "bzn": zone,
        "start": start_date,
        "end": end_date,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("price"):
        return pd.DataFrame(columns=["date", "price"])

    df = pd.DataFrame({
        "timestamp": data["unix_seconds"],
        "price_eur_mwh": data["price"]
    })
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
    df["date"] = df["datetime"].dt.date
    df["price"] = df["price_eur_mwh"] / 10  # EUR/MWh → ct/kWh

    # Mittelwert pro Tag bilden
    df_daily = df.groupby("date")["price"].mean().reset_index()
    return df_daily.sort_values("date").reset_index(drop=True)

if __name__ == "__main__":
    end = date.today()
    start = end - timedelta(days=90)

    df_daily = fetch_energycharts_daily(start.isoformat(), end.isoformat())

    print("\n📊 Tagesdurchschnitt Strompreise (ct/kWh):")
    print(df_daily.to_string(index=False))
