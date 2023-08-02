import threading
import time
import uuid

import requests
from binance import Client
from telebot import TeleBot, types

import main2

crypto = ["BTC", "ETH", "XRP", "BNB", "ADA", "DOGE", "SOL", "TRX", "MATIC", "LTC", "DOT", "AVAX",
          "WBTC", "BCH", "SHIB", "LINK", "XLM", "UNI", "ATOM", "XMR", "ETC",
          "FIL", "ICP", "LDO", "HBAR", "APT", "ARB", "NEAR", "VET", "QNT", "MKR", "GRT", "AAVE", "OP", "ALGO", "STX",
          "EGLD", "SAND", "EOS", "SNX", "IMX", "THETA", "XTZ", "APE"]
bot = TeleBot("6364335552:AAGoJp6Ah8dzpJwOn7j1VSKkf7Rv5QmGqkQ")


@bot.message_handler(func=lambda message: message.text == "Войти в сделку")
def rsi(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.add(*[types.InlineKeyboardButton(f"{i}USDT", callback_data=i + "USDT") for i in crypto])
    bot.send_message(message.chat.id, "Выберите пару", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "RSI < 30")
def rsi(message: types.Message):
    res = requests.get("http://127.0.0.1:5000/get").json()
    for k, v in res.items():
        if v['h1'] < 30:
            bot.send_message(message.chat.id, f"{k}: {v['h1']}")


@bot.message_handler(func=lambda message: message.text == "Активные сделки")
def rsi(message: types.Message):
    for i in main2.deals:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Выйти", callback_data="uuid:" + i['uuid']))
        bot.send_message(message.chat.id, f"Монета: {i['coin']}\n"
                                          f"Количество: {i['quantity']}\n"
                                          f"PNL: {i['pnl']}%", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: "uuid:" in call.data)
def usdt(call: types.CallbackQuery):
    item = {}
    for i in main2.deals:
        if i['uuid'] == call.data:
            item = i
    place_order("SELL", item['quantity'], item['coin'])
    main2.deals.remove(item)
    bot.send_message(call.from_user.id, "Успешно")


def place_order(side, quantity, coin):
    client = Client("token", "token")
    return client.create_order(symbol=coin, quantity=quantity, side=side, type="MARKET")


def buy(message, coin):
    try:
        place_order("BUY", quantity=message.text, coin=coin)
        key = f"https://api.binance.com/api/v3/ticker/price?symbol={coin}"
        data = requests.get(key).json()
        price = float(data['price'])
        main2.deals.append({
            "uuid": uuid.uuid4(),
            "take profit": price * 1.04,
            "stop loss": price * 0.97,
            "quantity": float(message.text),
            "dollars": float(message.text) * price,
            "start price": price,
            "pnl": 0,
            "coin": coin
        })
        threading.Thread(target=main2.check_order, args=[price * 1.04, price * 0.97, float(message.text), coin, main2.deals[-1],
                                                         len(main2.deals) - 1]).start()
        bot.send_message(message.chat.id, f"Вы успешно купили {coin} на {message.text}")
    except Exception:
        bot.send_message(message.chat.id, "Ошибка")


@bot.callback_query_handler(func=lambda call: "USDT" in call.data)
def usdt(call: types.CallbackQuery):
    key = f"https://api.binance.com/api/v3/ticker/price?symbol={call.data}"
    data = requests.get(key).json()
    bot.send_message(call.from_user.id, f"Текущая цена - {round(float(data['price']), 4)}")
    bot.send_message(call.from_user.id, f"Введите количество в {call.data.replace('USDT', '')}")
    bot.register_next_step_handler(call.message, buy, *[call.data])


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    items = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    items.add(*[types.KeyboardButton("Войти в сделку"), types.KeyboardButton("Активные сделки"), types.KeyboardButton("RSI < 30"), types.KeyboardButton("Главное меню")])
    bot.send_message(message.chat.id, "Выберите действие", reply_markup=items)


@bot.message_handler(func=lambda message: message.text == "Главное меню")
def start(message: types.Message):
    items = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    items.add(*[types.KeyboardButton("Войти в сделку"), types.KeyboardButton("Активные сделки"), types.KeyboardButton("RSI < 30"), types.KeyboardButton("Главное меню")])
    bot.send_message(message.chat.id, "Выберите действие", reply_markup=items)


if __name__ == '__main__':
    threading.Thread(target=main2.tracking).start()
    bot.infinity_polling()

