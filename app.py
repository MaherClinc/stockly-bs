import os
os.environ['IEX_TOKEN'] = 'sk_4cad9231da8f49a58e0430ac1bc9e6dd'

from flask import Flask, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import iexfinance
from iexfinance.stocks import Stock
import requests
import psycopg2
import json
import re

import metric

app = Flask(__name__)

# SQLite for development, Postgres for production
# DATABASE_URL = os.environ.get("DATABASE_URL")
# if DATABASE_URL is None:
#     db_path = os.path.join(os.path.dirname(__file__), "app.db")
#     db_uri = f"sqlite:///{db_path}"
# else:
#     db_uri = DATABASE_URL
#     conn = psycopg2.connect(DATABASE_URL, sslmode="require")

# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
# db = SQLAlchemy(app)

# import models
# from account import get_watchlist, add_to_watchlist, remove_from_watchlist, is_stock_in_watchlist, buy_stock, sell_stock, get_portfolio

def stateBusnLogic(state, content):
    switcher = {
        'market_order_buy': tradeRequest,
        'market_order_buy_confirmed': buyStock,
        'market_order_sell_confirmed': sellStock,
        'market_order_sell': tradeRequest,
        'news': news,
        'overview': overview,
        'stock_info': infoStock,
        'portfolio': portfolio,
        'watchlist_add': addToWatchlist,
        'watchlist_potential': potentialWatchlist,
        'watchlist_remove': removeFromWatchlist,
        'watchlist_view': viewWatchlist
    }
    return switcher.get(state, jsonify)(content)

industryMapping = {
    'consumer_dis': ['F', 'CMG', 'DIS', 'AMZN', 'NFLX'],
    'consumer_sta': ['PEP', 'KR', 'COST', 'PG', 'FL'],
    'energy': ['XOM', 'CVX', 'MPC', 'PSXP', 'OXY'],
    'finance': ['MS', 'JPM', 'GS', 'BRK.A', 'AXP'],
    'healthcare': ['ANTM', 'CVS', 'CNC', 'ABBV', 'UNH'],
    'industrial': ['ROAD', 'TPIC', 'KRNT', 'ROP', 'ITT'],
    'material': ['BLL', 'MOS', 'ECL', 'LIN', 'CF'],
    'real_estate': ['EGP', 'DLR', 'CRG', 'COR', 'MAA'],
    'technology': ['GOOGL', 'AAPL', 'FB', 'TWTR', 'MSFT'],
    'telecom': ['VZ', 'T', 'TMUS', 'S', 'TU'],
    'utility': ['DUK', 'PEG', 'PNW', 'EXC', 'AES'],
    'NULL': []
}

def getTicker(name):

    r = requests.get('https://api.iextrading.com/1.0/ref-data/symbols')
    stockList = r.json()
    return process.extractOne(name, stockList)[0]['symbol']


def tradeRequest(content):
    content = request.json
    print(content['slots'])
    if '_STOCK_NAME_' in content['slots']:
        stockNameFromSlot = content['slots']['_STOCK_NAME_']['values'][0]['tokens']
        ticker = getTicker(stockNameFromSlot)
        stockNameActual = Stock(ticker).get_company_name()

        content['slots']['_STOCK_NAME_']['values'][0]['resolved'] = 1
        #content['slots']['_STOCK_NAME_']['values'][0]['value'] = stockNameActual

    if '_AMOUNT_' in content['slots']:
        amountFromSlot = content['slots']['_AMOUNT_']['values'][0]['tokens']

        content['slots']['_AMOUNT_']['values'][0]['resolved'] = 1
        #content['slots']['_AMOUNT_']['values'][0]['value'] = amountFromSlot

    return jsonify(content)

def processAmount(amountFromSlot):
    string = re.sub('percent', '%', amountFromSlot)
    list_patterns = [r'\d+ *%', r'\d+']
    swaplogic = '|'
    amount = re.findall(swaplogic.join(list_patterns), string)
    amount = amount[0] if len(amount) else None
    if '%' in amount:
        return float(amount.strip('%'))/100
    else:
        return int(amount)

def buyStock(content):
    content = request.json

    if '_STOCK_NAME_' in content['slots']:
        stockNameFromSlot = content['slots']['_STOCK_NAME_']['values'][0]['tokens']
        ticker = getTicker(stockNameFromSlot)
    
    if '_AMOUNT_' in content['slots']:
        amount = content['slots']['_AMOUNT_']['values'][0]['tokens']
    
    if ticker and amount.isdigit():
        content["slots"]["_BUY_ORDER_"] = {
            "type": "string",
            "values": [{
                "tokens": "buy",
                "resolved": 1,
                "value": ticker,
                "numOfShares": amount,
                "limitPrice": metric.get_price(ticker),
                "error": None
            }]
        }

    # if ticker and amount.isdigit():
    #     res = buy_stock(ticker, int(amount))
    #     if res['status']:
    #         content["slots"]["_BUY_ORDER_"]['values'][0]['resolved'] = 1
    #     else:
    #         content["slots"]["_BUY_ORDER_"]['values'][0]['resolved'] = -1
    #         content["slots"]["_BUY_ORDER_"]['values'][0]['error'] = res['error']

    return jsonify(content)

def sellStock(content):
    content = request.json
    if '_STOCK_NAME_' in content['slots']:
        stockNameFromSlot = content['slots']['_STOCK_NAME_']['values'][0]['tokens']
        ticker = getTicker(stockNameFromSlot)
    
    if '_AMOUNT_' in content['slots']:
        amount = processAmount( content['slots']['_AMOUNT_']['values'][0]['tokens'] )
        print(amount)

    content["slots"]["_SELL_ORDER_"] = {
        "type": "string",
        "values": [{
            "tokens": "sell",
            "resolved": -1,
            "value": ticker,
            "numOfShares": amount,
            "limitPrice": metric.get_price(ticker),
            "error": None
        }]
    }

    res = sell_stock(ticker, float(amount))
    if res['status']:
        content["slots"]["_SELL_ORDER_"]['values'][0]['resolved'] = 1
        content["slots"]["_SELL_ORDER_"]['values'][0]['numOfShares'] = res['amount']
    else:
        content["slots"]["_SELL_ORDER_"]['values'][0]['resolved'] = -1
        content["slots"]["_SELL_ORDER_"]['values'][0]['error'] = res['error']

    return jsonify(content)

def news(content):
    content = request.json

    if '_STOCK_NAME_' in content['slots']:

        stockName = content['slots']['_STOCK_NAME_']['values'][0]['tokens']
        ticker = getTicker(stockName)
        print(ticker)
        companyName = Stock(ticker).get_company_name()
        content['slots']['_STOCK_NAME_']['values'][0]['resolved'] = 1
        content['slots']['_STOCK_NAME_']['values'][0]['value'] = companyName
        news = Stock(ticker).get_news()
    
    if '_INDUSTRY_' in content['slots']:
        industry = content['slots']['_INDUSTRY_']['values'][0]['industry_name_dest']
        content['slots']['_INDUSTRY_']['values'][0]['resolved'] = 1
        content['slots']['_INDUSTRY_']['values'][0]['value'] = industry
        companies = industryMapping[industry]
        news = [Stock(ticker).get_news(last=2) for ticker in companies]

    content['slots']['_OUTPUT_'] = {
        'type': 'string',
        'values': [{
            "resolved": 1,
            "tokens": "news",
            "value": news
        }]
    }

    return jsonify(content)


def infoStock(content):
    content = request.json
    stockNameFromSlot = periodFromSlot = measure = None
    
    if '_STOCK_NAME_' in content['slots']:
        stockNameFromSlot = content['slots']['_STOCK_NAME_']['values'][0]['tokens']
        ticker = getTicker(stockNameFromSlot)
        stockNameActual = Stock(ticker).get_company_name()
        content['slots']['_STOCK_NAME_']['values'][0]['resolved'] = 1
        content['slots']['_STOCK_NAME_']['values'][0]['value'] = stockNameActual
    
    if '_PERIOD_' in content['slots']:
        periodFromSlot = content['slots']['_STOCK_NAME_']['values'][0]['tokens']
        content['slots']['_PERIOD_']['values'][0]['resolved'] = 1
        content['slots']['_PERIOD_']['values'][0]['value'] = periodFromSlot
    
    if '_METRIC_' in content['slots']:
        metricFromSlot = content['slots']['_METRIC_']['values'][0]['tokens']
        content['slots']['_METRIC_']['values'][0]['resolved'] = 1
        content['slots']['_METRIC_']['values'][0]['value'] = metricFromSlot
        measure = content['slots']['_METRIC_']['values'][0]['metric_dest']

    metricValue = metric.findAndExecute(ticker, measure, periodFromSlot)

    content['slots']["_OUTPUT_"] = {
        'type': 'string',
        'values': [{
            "resolved": 1,
            "tokens": "stock info",
            "value": metricValue
        }]
    }

    return jsonify(content)


def overview(content):
    content = request.json

    #marketGainers = list( map(lambda x: Stock(x['symbol']).get_company()['companyName'], iexfinance.stocks.get_market_gainers()) )
    #marketLosers = list( map(lambda x: Stock(x['symbol']).get_company()['companyName'], iexfinance.stocks.get_market_losers()) )
    
    content['slots'] = {
        "_OUTPUT_": {
        "values": [{
                "resolved": 1,
                "tokens": "market gainers",
                "value": iexfinance.stocks.get_market_gainers()
            }, {
                "resolved": 1,
                "tokens": "market losers",
                "value": iexfinance.stocks.get_market_losers()
            }, {
                "resolved": 1,
                "tokens": "most active",
                "value": iexfinance.stocks.get_market_most_active()
            }]
        }
    }
    return jsonify(content)


def portfolio(content):
    portfolio = get_portfolio()
    if len(portfolio):
        for obj in portfolio:
            obj['company'] = metric.get_company(obj['ticker'])['companyName']
            obj['historical_data'] = Stock(obj['ticker']).get_chart(range='1m')

    content["slots"]["_OUTPUT_"] = {
        "type": "string",
        "values": [
            {
                "tokens": "portfolio",
                "resolved": 1,
                "value": portfolio
            }
        ]
    }

    return jsonify(content)


def addToWatchlist(content):
    content = request.json
    if '_STOCK_NAME_' in content['slots']:
        stockNameFromSlot = content['slots']['_STOCK_NAME_']['values'][0]['tokens']
        ticker = getTicker(stockNameFromSlot)
        stockNameActual = Stock(ticker).get_company_name()
        content['slots']['_STOCK_NAME_']['values'][0]['value'] = stockNameActual
        
        added = True if is_stock_in_watchlist(ticker) else add_to_watchlist(ticker) 
        if added:
            content['slots']['_STOCK_NAME_']['values'][0]['resolved'] = 1
        
    return jsonify(content)


def removeFromWatchlist(content):
    if '_STOCK_NAME_' in content['slots']:
        stockNameFromSlot = content['slots']['_STOCK_NAME_']['values'][0]['tokens']
        ticker = getTicker(stockNameFromSlot)
        stockNameActual = Stock(ticker).get_company_name()
        content['slots']['_STOCK_NAME_']['values'][0]['value'] = stockNameActual

        removed = remove_from_watchlist(ticker)
        if removed:
            content['slots']['_STOCK_NAME_']['values'][0]['resolved'] = 1
        
    return jsonify(content)


def viewWatchlist(content):
    watchlist = get_watchlist()
    watchlist_new = []

    if len(watchlist):
        for ticker in watchlist:
            historical_data = Stock(ticker).get_chart(range='1m')
            companyName = metric.get_company(ticker)['companyName']

            watchlist_new.append({
                'companyName': companyName,
                'historical_data': historical_data
            })

    if '_STOCK_NAME_' in content['slots']:
        stockNameFromSlot = content['slots']['_STOCK_NAME_']['values'][0]['tokens']
        ticker = getTicker(stockNameFromSlot)
        stockNameActual = Stock(ticker).get_company_name()
        content['slots']['_STOCK_NAME_']['values'][0]['value'] = stockNameActual

        isStockPresent = is_stock_in_watchlist(ticker)
        content['slots']['_STOCK_NAME_']['values'][0]['resolved'] = 1 if isStockPresent else -1

    content["slots"]["_OUTPUT_"] = {
        "type": "string",
        "values": [
            {
                "tokens": "watchlist",
                "resolved": 1,
                "value": watchlist_new
            }
        ]
    }

    return jsonify(content)


def potentialWatchlist(content):
    return jsonify(content)


@app.route("/", methods=["POST"])
def handle():
    content = request.json
    print(content)
    print(content['state'])
    print(content['intent'])

    if content['intent'] == 'cs_yes':
        pass
    else:
        for slot in content['slots']:
            if slot == '_STOCK_NAME_':
                #content['slots'][slot]['values'] = [v for v in content['slots'][slot]['values'] if not (v['stock_name_dest'] == 'stopword' )]
                content['slots'][slot]['values'] = [v for v in content['slots'][slot]['values']]

        for slot in content['slots']:
            if len(content['slots'][slot]['values']) > 1:
                content['slots'][slot]['values'] = [v for v in content['slots'][slot]['values'] if not (v['resolved'] == 1 )]
            elif len(content['slots'][slot]['values']) == 1: pass
            else: return jsonify(content)

    return stateBusnLogic(content['state'], content)