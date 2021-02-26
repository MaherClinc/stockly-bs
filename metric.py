from iexfinance.stocks import Stock
from fuzzywuzzy import process
import datetime
from flask import jsonify

def findAndExecute(stock, metric=None, period=None):
    stats = Stock(stock).get_key_stats()
    if metric:
        if period:
            return {"metric": metric, 
                    "value": metricsMapping[metric](stock, period),
                    "symbol": stock,
                    "key_stats": stats}
        else:
            return {"metric": metric, 
                    "value": metricsMapping[metric](stock),
                    "symbol": stock,
                    "key_stats": stats}
    else:
        historical_data = Stock(stock).get_chart(range="3m")
        return {"historical_data": historical_data, "symbol": stock, "key_stats": stats}


def get_company(stock, *karg):
    return Stock(stock).get_company()

def get_price(stock, *karg):
    return Stock(stock).get_price()

def get_open(stock, *karg):
    return Stock(stock).get_open()

def get_close(stock, *karg):
    return Stock(stock).get_close()

def get_beta(stock, *karg):
    return Stock(stock).get_beta()

def get_pe_ratio(stock, *karg):
    return Stock(stock).get_key_stats()['peRatio']

def get_market_cap(stock, *karg):
    return Stock(stock).get_market_cap()

def get_financials(stock, *karg):
    return Stock(stock).get_financials()

def get_high(stock, period="xxxx"):
    if any(x in period for x in ['1 year', '52 week']):
        return Stock(stock).get_years_high()
    else:
        return Stock(stock).get_ohlc()

def get_low(stock, period="xxxx"):
    if any(x in period for x in ['1 year', '52 week']):
        return Stock(stock).get_years_low()
    else:
        return Stock(stock).get_ohlc()

def get_earnings(stock, period="xxxx"):  #max upto 1 year
    if 'year' in period:
        return Stock(stock).get_earnings(last = 4)
    elif 'quarter' in period:
        last = [int(s) for s in period.split() if s.isdigit()]
        return Stock(stock).get_earnings(last = last[0])
    else:
        return Stock(stock).get_earnings()

def get_shares_outstanding(stock, *karg):
    return Stock(stock).get_shares_outstanding()

def get_float(stock):
    return Stock(stock).get_float()

def get_dividends(stock, period="1 year"):
    possiblePeriods = {
        "5 years": "5y",
        "2 years": "2y",
        "1 year": "1y",
        "year to date": "ytd",
        "ytd": "ytd",
        "6 months": "6m",
        "3 months": "3m",
        "1 month": "1m"
    }

    identiedPeriod = process.extractOne(period, possiblePeriods.keys())[0]
    selectedPeriod = possiblePeriods[identiedPeriod]
    return Stock(stock).get_dividends(range = selectedPeriod)

def get_change_percent(stock, period="2 year"):
    possiblePeriods = {
        "5 years": "year5ChangePercent",
        "2 years": "year2ChangePercent",
        "1 year": "year1ChangePercent",
        "year to date": "ytdChangePercent",
        "ytd": "ytdChangePercent",
        "6 months": "month6ChangePercent",
        "3 months": "month3ChangePercent",
        "1 month": "month1ChangePercent",
        "5 day": "day5ChangePercent"
    }

    identiiedPeriod = process.extractOne(period, possiblePeriods.keys())[0]
    return Stock(stock).get_key_stats()[ possiblePeriods[identiiedPeriod] ]

def get_volume(stock, period="30 day"):
    possiblePeriods = {
        "10 day": "avg10Volume",
        "30 day": "avg30Volume"
    }
    identiiedPeriod = process.extractOne(period, possiblePeriods.keys())[0]
    return Stock(stock).get_key_stats()[ possiblePeriods[identiiedPeriod] ]

def get_moving_avg(stock, period="200 day"):
    possiblePeriods = {
        "50 day": "day50MovingAvg",
        "200 day": "day200MovingAvg"
    }
    identiiedPeriod = process.extractOne(period, possiblePeriods.keys())[0]
    return Stock(stock).get_key_stats()[ possiblePeriods[identiiedPeriod] ]

#unpaid version of iex-cloud
#get_financials() will work in paid version.
#showing previous day's ohlc. "price" is previous day's closing price

metricsMapping = {
    'price': get_close,
    'beta': get_beta,
    'eps': get_earnings,
    'outstanding': get_shares_outstanding,
    'floating': get_float,
    'dividend': get_dividends,
    'open': get_open,
    'close': get_close,
    'high': get_high,
    'low': get_low,
    'change_percent': get_change_percent,
    'volume': get_volume,
    'market_cap': get_market_cap,
    'per': get_pe_ratio,
    'moving_avg': get_moving_avg,
    'financials': get_financials,
    'NULL': get_close
}