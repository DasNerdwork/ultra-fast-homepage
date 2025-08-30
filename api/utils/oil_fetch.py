from datetime import datetime, timedelta
import requests

def fetch_heizoel_price(last: int = 30):
    """Holt die letzten X Tage Heizölpreise."""
    min_date = (datetime.today() - timedelta(days=last)).strftime("%m-%d-%Y")
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

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return {
            "ok": True,
            "httpStatus": resp.status_code,
            "values": data.get("Values", [])
        }
    except requests.RequestException as e:
        return {
            "ok": False,
            "httpStatus": None,
            "error": str(e)
        }
