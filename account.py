from sqlalchemy import exc
from sqlalchemy.sql.expression import func
from models import Watchlist, Portfolio, Activity
from app import db
import metric


def buy_stock(ticker, units):
    unit_price = metric.get_price(ticker)
    total_price = units * unit_price
    max_id = db.session.query(func.max(Activity.activity_id)).scalar()
    
    if max_id is None:
        old_buying_power = 100000
    else:
        old_buying_power = Activity.query.filter(Activity.activity_id == max_id).all()[0].buying_power
    
    new_buying_power = old_buying_power - total_price

    if new_buying_power > 0:
        try:
            db.session.add( Activity(ticker=ticker, 
                units=units, order_type= "b", unit_price=unit_price, total_price=total_price, buying_power=new_buying_power) )
            update_portfolio_buy(ticker, units, total_price)
            db.session.commit()
            return { 'status': True, 'error': None }
        except exc.SQLAlchemyError:
            return { 'status': False, 'error': 'database error' }
    else:
        return { 'status': False, 'error': 'Insufficient Funds' }

def sell_stock(ticker, units):
    unit_price = metric.get_price(ticker)
    row = Portfolio.query.filter(Portfolio.ticker == ticker).all()
    if len(row):
        available_units = int(row[0].total_units)
        units = min(available_units, units) if units >= 1 else int(available_units*units)
        total_price = units * unit_price

        max_id = db.session.query(func.max(Activity.activity_id)).scalar()
        old_buying_power = Activity.query.filter(Activity.activity_id == max_id).all()[0].buying_power
        new_buying_power = old_buying_power + total_price

        try:
            db.session.add( Activity(ticker=ticker, 
                units=units, order_type= "s", unit_price=unit_price, total_price=total_price, buying_power=new_buying_power) )
            update_portfolio_sell(ticker, units, total_price)
            db.session.commit()
            return { 'status': True, 'amount': units, 'error': None }
        except exc.SQLAlchemyError:
            return { 'status': False, 'error': 'database error' }
    else:
        return { 'status': False, 'error': 'No Stock by this name' }

def update_portfolio_buy(ticker, units, total_price):
    row = Portfolio.query.filter(Portfolio.ticker == ticker).all()
    if len(row):
        row[0].total_units = int(row[0].total_units) + units
        row[0].total_invested = int(row[0].total_invested) + total_price
    else:
        db.session.add( Portfolio(ticker=ticker, total_units=units, total_invested=total_price) )

def update_portfolio_sell(ticker, units, total_price):
    row = Portfolio.query.filter(Portfolio.ticker == ticker).all()
    if len(row):
        row[0].total_invested = int(row[0].total_invested) - ((int(row[0].total_invested)/int(row[0].total_units)) * units)
        row[0].total_units = int(row[0].total_units) - units
    
    Portfolio.query.filter(Portfolio.total_units == 0).delete()

def get_watchlist():
    rows = Watchlist.query.all()
    if len(rows):
        watchlist = [row.ticker for row in rows]
    else:
        watchlist = []

    return watchlist

def get_portfolio():
    rows = Portfolio.query.all()
    portfolio = [{'ticker':row.ticker, 'total_units':row.total_units, 'total_invested':row.total_invested} for row in rows]
    return portfolio

def is_stock_in_watchlist(ticker):
    rows = Watchlist.query.filter(Watchlist.ticker == ticker).all()
    return True if len(rows) else False

def add_to_watchlist(ticker):
    industry = metric.get_company(ticker)["industry"]
    try:
        db.session.add( Watchlist(ticker=ticker, industry=industry) )
        db.session.commit()
        return True
    except exc.SQLAlchemyError:
        return False

def remove_from_watchlist(ticker):
    try:
        Watchlist.query.filter(Watchlist.ticker == ticker).delete()
        db.session.commit()
        return True
    except exc.SQLAlchemyError:
        return False





