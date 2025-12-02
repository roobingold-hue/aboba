import requests

def get_usd_rate():
    # URL API ЦБ
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        usd_rate = data["Valute"]["USD"]["Value"]

        print(f"Курс доллара: {usd_rate:.2f}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении данных: {e}")

get_usd_rate()