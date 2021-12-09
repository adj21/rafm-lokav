import websocket, json, pprint, talib, numpy
from binance.client import Client
from binance.enums import *

#Websocket sem er tengt við binance datastream sem les 10 min kline(clandlesticks) fyrir BTCUSDT parið
SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_10m"

#binance api lyklar sem þú notar til að tengjast við binance accountinn
API_KEY = 'binanceapikey'
API_SECRET = 'binanceapisecret'

#RSI er skoðað yfir seinustu 10 candlestick og gefur value frá 0 uppí 100 eftir því hvort margir eru að selja eða kaupa.
RSI_PERIOD = 10
#Setjum RSI overbought í 70 því þegar það er í 70 er yfirleitt talið að það séu of margir að kaupa sem þýðir að það er góður tími til að selja
RSI_OVERBOUGHT = 70
#Setjum RSI oversold í 30 því þegar RSI í 30 eru margir að selja sem er þá góður tími til að kaupa
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'BTCUSD'
#100$ virði af BTC
TRADE_QUANTITY = 0.002 

closes = []
in_position = False

client = Client(API_KEY, API_SECRET, tld='eu')

#þetta fall er talar við client og kaupir eða selur
def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True

    
def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

#tekur við candlestick upplýsingum frá websocketinu í json formati
def on_message(ws, message):
    global closes, in_position
    
    print('received message')
    json_message = json.loads(message)
    pprint.pprint(json_message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']

    #skoðar hvort candle sé lokað því við viljum bara gera trade þá.
    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print("closes")
        print(closes)

        #skoðar hvort closes fylkið sé orðið stærra en RSI_PERIOD og reiknar síðan RSI út frá upplýsingum closes fylkisins
        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("all rsis calculated so far")
            print(rsi)
            last_rsi = rsi[-1]
            print("the current rsi is {}".format(last_rsi))

            #Ef RSI bendir til að coininn sé overbought þá seljum við
            if last_rsi > RSI_OVERBOUGHT:
                if in_position:
                    print("Sell!")
                    # notum order fallið til að selja
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("you don't own the coin, can't sell")

            #Ef RSI bendir til að coininn sé oversold þá kaupum við
            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    print("you already own the coin, can't buy")
                else:
                    print("Buy!")
                    # notum order fallið til að kaupa
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True

#webwocket sem sendir constant data á terminalið                  
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()