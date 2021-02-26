from app import db
from datetime import datetime


class Portfolio(db.Model):
    ticker = db.Column(db.String(5), primary_key=True)
    total_units = db.Column(db.Integer, nullable=False)
    total_invested = db.Column(db.Float, nullable=False)

class Activity(db.Model):
    activity_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime(), default=datetime.now())
    order_type = db.Column(db.String(1), nullable=False)
    ticker = db.Column(db.String(5), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    buying_power = db.Column(db.Float, nullable=False)

class Watchlist(db.Model):
    ticker = db.Column(db.String(5), primary_key=True)
    industry = db.Column(db.String(50), nullable=False)

