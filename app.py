import requests, json, os, talib, csv
import alpaca_trade_api as tradeapi
import yfinance as yf
import pandas as pd
from flask import Flask, render_template, request
from config import *
from patterns import candlestick_patterns
from datetime import date

app = Flask(__name__)

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=BASE_URL)

today = date.today()

@app.route('/')
def dashboard():
    orders = api.list_orders(status='all', limit=50)
    positions = api.list_positions()

    return render_template('dashboard.html', alpaca_orders=orders, alpaca_positions=positions)

@app.route('/webhook', methods=['POST'])
def webhook():
    webhook_message = json.loads(request.data)

    if webhook_message['passphrase'] != WEBHOOK_PASSPHRASE:
        return "no"

    price = webhook_message['strategy']['order_price']
    quantity = webhook_message['strategy']['order_contracts']
    symbol = webhook_message['ticker']
    side = webhook_message['strategy']['order_action']

    order = api.submit_order(symbol, quantity, side, 'market', 'gtc', limit_price=price)

    chat_message = {
        "content":f"tradingview strategy alert triggered: {quantity} {symbol} @ {price}"
    }

    requests.post(DISCORD_URL, json=chat_message)

    return webhook_message

@app.route('/analytics')
def analytics():
    path = './datasets/daily/'
    pattern = request.args.get('pattern', None)
    stocks = {}

    with open('./datasets/companies.csv') as f:
        for row in csv.reader(f):
            stocks[row[0]] = {'company':row[1]}
    if pattern:
        datafiles = os.listdir(path)
        for file in datafiles:
            df = pd.read_csv(path + file)
            pattern_function = getattr(talib, pattern)
            symbol = file.split('.')[0]
            try:
                result = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                last = result.tail(1).values[0]
                if last > 0:
                    stocks[symbol][pattern] = 'bullish'
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'
                else:
                    stocks[symbol][pattern] = None

            except:
                pass

    return render_template('analytics.html', candlestick_patterns=candlestick_patterns, stocks=stocks, pattern=pattern)

@app.route('/snapshot')
def snapshot():
    #today = global today
    with open('./datasets/companies.csv') as f:
        companies = f.read().splitlines()
        for company in companies:
            symbol = company.split(',')[0]
            df = yf.download(symbol, start="2019-01-01", end=today.strftime("%Y-%m-%d"))
            df.to_csv('./datasets/daily/{}.csv'.format(symbol))

    return {
        'code':'success'
    }
