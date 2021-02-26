import os
import requests
from dotenv import load_dotenv
load_dotenv()

SECRET_TOKEN = os.getenv("SECRET_TOKEN")
if SECRET_TOKEN is None:
    print("ERROR: you must set secret API token to make requests.")

BASE_URL = os.getenv("BASE_URL")
if BASE_URL is None:
    print("ERROR: you must set a base URL to make requests.")


def get_dividends(ticker, time):
    url = f"{BASE_URL}/stock/{ticker}/dividends/{time}?token={SECRET_TOKEN}"
    result = requests.get(url)
    return result.json()


if __name__ == '__main__':
    print(get_dividends("aapl", "1m"))
