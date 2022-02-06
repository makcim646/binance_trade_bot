from binance.client import Client
from time import sleep
import json
import os
import sys
import subprocess
import tempfile
bot_path = os.path.expanduser('~') + '\\binance_bot\\'



def get_price(symbol:str):
    info = client.get_order_book(symbol=f'{symbol}', limit=400)

    max_coin_bids = [0,0]
    for b in info['bids']:
        if float(max_coin_bids[1]) < float(b[1]):
            max_coin_bids = b

    max_coin_asks = [0,0]
    for a in info['asks']:
        if float(max_coin_asks[1]) < float(a[1]):
            max_coin_asks = a


    candles = client.get_klines(symbol=f'{symbol}', interval=Client.KLINE_INTERVAL_5MINUTE, limit=300)
    day_min = []
    day_max = []
    for c in candles:
        day_min.append(float(c[3]))
        day_max.append(float(c[2]))
    day_max.sort()
    day_min.sort()

    max_sell = day_max[-1]
    max_buy = day_min[0]


    avg_day_min = (sum(day_min)  / len(day_min))
    avg_day_max = (sum(day_max)  / len(day_max))

    buy = round((float(max_coin_bids[0]) + (sum(day_min[0:50]) / 50)) / 2, 5)
    sell = round((float(max_coin_asks[0]) + (sum(day_max[-1:-50:-1]) / 50) ) / 2, 5)

    return {'buy':buy,  'sell':sell, 'symbol':symbol}


def tarde(symbol):
    tickers = client.get_ticker(symbol=f'{symbol}')
    lastPrice = float( tickers['lastPrice'])

    price = get_price(f'{symbol}')
    print(price, 'lastprice--', lastPrice,  end=' ')

    if price['buy'] >= price['sell']:
        coin_no_pump = False
    else:
       coin_no_pump = True



    with open(bot_path +"trade_coin_list.json", "r") as read_file:
        data_trade = json.load(read_file)


    with open(bot_path +"data_file.json", "r") as read_file:
        data = json.load(read_file)


    trade_status = data[symbol]['status']

    try:
        if lastPrice <= price['buy'] and  trade_status == 'buy' and coin_no_pump: # and (lastPrice < data[symbol]['price_to_sell'] or data[symbol]['price_to_sell'] == 0)
            money = data[symbol]['money']
            coin = coin_lot_size_buy(symbol, lastPrice, money)
            print(f'coin buy: {coin}', end=' ')

            order = client.order_market_buy(symbol=f'{symbol}', quantity=coin)
            print(order)


            data[symbol]['status'] = 'sell'
            data_trade[symbol]['status'] = 'sell'
            data[symbol]['money'] = 0
            data_trade[symbol]['money'] = 0

            price_buy = round(float(order['fills'][0]['price']), 4)

            data_trade[symbol]['price_to_buy'] = price_buy

            data[symbol]['coin'] = coin
            data[symbol]['price_to_buy'] = price_buy

            with open(bot_path +"data_file.json", "w") as write_file:
                json.dump(data, write_file, indent=4)

        if lastPrice > price['sell'] and trade_status == 'sell' and lastPrice > float(data[symbol]['price_to_buy']) * 1.02 :
            coin = coin_lot_size_sell(symbol)
            print(f'coin sell: {coin}', end=' ')

            order = client.order_market_sell(symbol=f'{symbol}', quantity=coin)
            print(order)

            data[symbol]['status'] = 'buy'
            data_trade[symbol]['status'] = 'buy'
            data[symbol]['coin'] = 0

            price_sell = round(float(order['fills'][0]['price']), 4)
            price_buy_order = data[symbol]['price_to_buy']


            if price_buy_order == 0:
                price_buy_order = lastPrice

            money_sell = coin * price_sell
            money_buy = coin * price_buy_order

            data[symbol]['money'] = 12
            data[symbol]['price_to_sell'] = price_sell
            data_trade[symbol]['money'] = 12
            data_trade[symbol]['price_to_sell'] = price_sell

            try:
                profit = data[symbol]['profit']
            except:
                profit = 0



            profit_order = money_sell - money_buy
            profit += profit_order
            data[symbol]['profit'] = round(profit, 3)


            with open(bot_path +"data_file.json", "w") as write_file:
                json.dump(data, write_file, indent=4)
    except Exception as e:
        print(e)

    with open(bot_path +"trade_coin_list.json", "w") as write_file:
        json.dump(data_trade, write_file, indent=4)

    out = ''
    out += symbol[:-4] + ' '
    out += trade_status + ' '
    if  trade_status == 'sell':
        out += str(price['sell'])
    else:
        out += str(price['buy'])
    out += ' lastPrice '
    out += str(lastPrice) + ' | '
    out += str(data[symbol]['price_to_buy'])
    out += '\n' + '\n'

    print(data[symbol])

    return out

def coin_lot_size_sell(symbol):
    symbol = symbol.upper()
    coin_info = client.get_symbol_info(symbol)
    step_size = float(coin_info['filters'][2]['stepSize'])
    info = client.get_account()
    coin_name = symbol.upper()[0:-4]
    for i in  info['balances']:
        if i['asset'] == coin_name:
            coin_size = float(i['free'])

    around = (1 / step_size)
    return ((coin_size // step_size) / around)

def coin_lot_size_buy(symbol, price, summ=12):
    symbol = symbol.upper()
    coin_info = client.get_symbol_info(symbol)
    step_size = float(coin_info['filters'][2]['stepSize'])
    coin_size = (summ / price)
    around = (1 / step_size)
    return round(((coin_size // step_size) / around), 5)


def get_ballance_all_coin():
    """выводит балансы монет котоые можно добавить для трейда """
    with open(bot_path +"data_file.json", "r") as read_file:
        data = json.load(read_file)

    info = client.get_account()

    for i in  info['balances']:
        if float(i['free']) > 0.0001:
            symbol = f'{i["asset"]}USDT'
            coin = float(i['free'])
            try:
                coin = coin_lot_size_sell(symbol)
                print(symbol, coin, data[symbol]['status'])
            except: pass

            if data.get(symbol) == None:               # добавляет монету в json если ее там нету
                data[symbol]= {'status': 'buy', 'money': 0, 'coin': coin, 'price_to_buy': 0, "price_to_sell": 0}

            if data[symbol]['status'] == 'sell':
                data[symbol]['coin'] = coin

    with open(bot_path +"data_file.json", "w") as write_file:
        json.dump(data, write_file, indent=4)



def add_coin_list(name:str, status:str, money:int, price_to_buy=0):
    with open(bot_path +'config.json', 'r') as file_config:
        config = json.load(file_config)
        api_key = config['api_key']
        api_secret = config['api_secret']


    client = Client(api_key, api_secret)
    name = name.upper()

    tickers = client.get_ticker(symbol=f'{name}USDT')
    lastPrice = float( tickers['lastPrice'])
    if status == 'sell':
        if price_to_buy == 0:
            price_to_buy = lastPrice

    with open(bot_path +"trade_coin_list.json", "r") as read_file:
        data = json.load(read_file)

    symbol = f'{name}USDT'
    data[symbol] = {'status': f'{status}', 'money': money, 'price_to_buy': price_to_buy, "price_to_sell": 0 }
    with open(bot_path +"trade_coin_list.json", "w") as write_file:
        json.dump(data, write_file, indent=4)

    return f"Монета {symbol} добавлена"

def get_coin_list():
    result_list = []

    with open(bot_path +"trade_coin_list.json", "r") as read_file:
        coin_list = json.load(read_file)

    with open(bot_path +"data_file.json", "r") as read_file:
        data = json.load(read_file)

    for coin in coin_list:
        result_list.append(coin)
        if data.get(coin) == None:
                data[coin]= {'status': coin_list[coin]['status'], 'money': coin_list[coin]['money'], 'coin': 0, 'price_to_buy': 0, "price_to_sell": 0}

        data[coin]['status'] = coin_list[coin]['status']
        data[coin]['money'] = coin_list[coin]['money']
        try:

            data[coin]['price_to_sell'] = coin_list[coin]['price_to_sell']
            data[coin]['price_to_buy'] = coin_list[coin]['price_to_buy']
        except: pass


    with open(bot_path +"data_file.json", "w") as write_file:
        json.dump(data, write_file, indent=4)


    return result_list


def pop_coin_list(name:str):
    with open(bot_path +"trade_coin_list.json", "r") as read_file:
        data = json.load(read_file)

    name = name.upper()
    symbol = f'{name}USDT'

    try:
        data.pop(symbol)
        with open(bot_path +"trade_coin_list.json", "w") as write_file:
            json.dump(data, write_file, indent=4)
        return 'Монета уделена'
    except:
        return 'Такой монеты нет в списке'


def check_config(update_config=False):
    check_folder = os.path.exists(os.path.expanduser('~') + '\\binance_bot')
    if check_folder == False:
        os.mkdir(os.path.expanduser('~') + '\\binance_bot')

    bot_path = os.path.expanduser('~') + '\\binance_bot\\'

    check_config = os.path.exists(bot_path +'config.json')
    check_data = os.path.exists(bot_path +'data_file.json')
    check_coin_list = os.path.exists(bot_path +'trade_coin_list.json')


    if check_data == False:
        data = {}
        with open(bot_path +'data_file.json', 'w') as file_config:
            json.dump(data, file_config, indent=4)


    if check_coin_list == False:
        coin_list = {}
        with open(bot_path +'trade_coin_list.json', 'w') as file_config:
            json.dump(coin_list, file_config, indent=4)


    if check_config == False:
        config = {}
        config['api_key'] = str(input('Введи binance api_key: '))
        config['api_secret'] = str(input('Введи binance api_secret: '))
        config['bot_token'] = str(input('Введи telegram bot token: '))

        with open(bot_path +'config.json', 'w') as file_config:
            json.dump(config, file_config, indent=4)

    if update_config == True:
        config = {}
        config['api_key'] = str(input('Введи binance api_key: '))
        config['api_secret'] = str(input('Введи binance api_secret: '))
        config['bot_token'] = str(input('Введи telegram bot token: '))

        with open(bot_path +'config.json', 'w') as file_config:
            json.dump(config, file_config, indent=4)

def bot_change_token():
    bot_path = os.path.expanduser('~') + '\\binance_bot\\'
    with open(bot_path +'config.json', 'r') as file_config:
        config = json.load(file_config)

    config['bot_token'] = str(input('Введи telegram bot token: '))

    with open(bot_path +'config.json', 'w') as file_config:
        json.dump(config, file_config, indent=4)



def get_config():
    bot_path = os.path.expanduser('~') + '\\binance_bot\\'
    with open(bot_path +'config.json', 'r') as file_config:
        config = json.load(file_config)
        api_key = config['api_key']
        api_secret = config['api_secret']
        bot_token = config['bot_token']
    return api_key, api_secret, bot_token


if __name__ == "__main__":
    #os.chdir(sys._MEIPASS)
    try:
        check_config()
        api_key, api_secret, bot_token = get_config()
        client = Client(api_key, api_secret)
        info = client.get_account()
        if bot_token == '':
            bot_change_token()

    except Exception as e:
        print(e)
        check_config(True)
        api_key, api_secret, bot_token= get_config()
        client = Client(api_key, api_secret)
        if bot_token == '':
            exit()

    bot_path = os.path.expanduser('~') + '\\binance_bot\\'


    os.system("w32tm /resync")
    proc = subprocess.Popen('bot_async.py')
    get_ballance_all_coin()
    while True:
        list_coin = get_coin_list()
        status = ''
        for coin in list_coin:
            try:
                status += tarde(coin)
            except Exception as e:
                print(e)


        print('\n')
        with open(bot_path + "status.txt", "w") as file:
            file.write(status)

        sleep(60 * 10)