from flask import Flask, render_template, request
import alpaca_trade_api as tradeapi
from config import *
import requests, json

app = Flask(__name__)

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=BASE_URL)

@app.route('/')
def dashboard():
    orders = api.list_orders(status='all', limit=50)
    positions = api.list_positions()
    #print(orders)

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

    order = api.submit_order(symbol, quantity, side, 'limit', 'gtc', limit_price=price)

    chat_message = {
        "content":f"tradingview strategy alert triggered: {quantity} {symbol} @ {price}"
    }

    requests.post(DISCORD_URL, json=chat_message)

    return webhook_message
