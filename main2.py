import threading
import time
import uuid

import numpy as np
import requests
import talib


def get_data(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=200"
        res = requests.get(url)
        return np.array([float(i[4]) for i in res.json()])
    except:
        pass

deals = []
balance = 100
coins = ["SOLUSDT", "ETHUSDT", "XRPUSDT"]
buy = {}
sell = {}
for i in coins:
    buy[i] = False
    sell[i] = True


def tracking():
    while True:
        for coin in coins:
            rsi_list = talib.RSI(get_data(coin), 14)
            print(rsi_list[-1])
            if rsi_list[-1] <= 25 and not buy[coin]:
                price = float(
                    requests.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT").json()['price'])
                quantity = round(((balance // 5) / price), 2)
                sell[coin] = False
                buy[coin] = True
                deals.append({
                    "uuid": uuid.uuid4(),
                    "take profit": price * 1.04,
                    "stop loss": price * 0.97,
                    "quantity": quantity,
                    "dollars": quantity * price,
                    "start price": price,
                    "pnl": 0,
                    "coin": coin
                })
                threading.Thread(target=check_order, args=[price * 1.04, price * 0.97, quantity, coin, deals[-1],
                                                           len(deals) - 1]).start()
            elif rsi_list[-1] >= 101 and not sell:
                pass
        print("-----------------")
        time.sleep(60 * 10)


def check_order(tp: float, sl: float, quantity, coin: str, deal: dict, index: int):
    global buy, sell
    print(tp, sl, quantity, coin)
    while True:
        price = float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin}").json()['price'])
        if deal in deals:
            start = deal['start price']
            one = start / 100
            delta = price - start
            deal['pnl'] = (round(delta / one) * -1, 2)
            deals[index] = deal
            if price <= sl:
                buy[coin] = False
                sell[coin] = True
                deals.remove(index)
                break
            elif price >= tp:
                time.sleep(5)
                tp = tp * 1.04
                sl = tp * 0.97
                deals[index]['take profit'] = tp
                deals[index]['stop loss'] = sl
        else:
            deals.remove(index)
            break
        time.sleep(5)