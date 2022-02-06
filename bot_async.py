from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from binance.client import Client
import json
import os

bot_path = os.path.expanduser('~') + '\\binance_bot\\'
with open(bot_path + 'config.json', 'r') as file_config:
    config = json.load(file_config)
    bot_token = config['bot_token']


bot = Bot(bot_token) #Telegram bot token
dp = Dispatcher(bot)


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



@dp.message_handler(commands='All')
async def send_welcome(msg: types.Message):
    with open(bot_path + "status.txt", "r") as file:
        text = file.readlines()
        out = ''
        for t in text:
            out += t

    await bot.send_message(msg.from_user.id, out)

@dp.message_handler(commands='Status')
async def send_welcome(msg: types.Message):
    with open(bot_path + "status.txt", "r") as file:
        text = file.readlines()
        out = ''
        for t in text:
            if t.split(' ')[0] != '\n' and t.split(' ')[1] == 'sell':
                out += t + '\n'

    await bot.send_message(msg.from_user.id, out)

@dp.message_handler(commands='Profit')
async def default(msg: types.Message):
    with open(bot_path +"data_file.json", "r") as read_file:
        data = json.load(read_file)

    profit = 0
    for d in data:
        try:
            profit += float(data[d]['profit'])
        except:pass
    await bot.send_message(msg.from_user.id, f'Профит: {profit}$')

@dp.message_handler()
async def echo_message(msg: types.Message):
    mess = msg.text.split(' ')
    if mess[0].upper() == 'POP':
        await bot.send_message(msg.from_user.id, pop_coin_list(mess[1]))


    elif mess[0].upper() == 'ADD':
        name = str(mess[1])
        status = str(mess[2])
        price = 0
        money = 12
        if status == 'sell':
            if len(mess) < 4:
                price = 0
            else:
                price = float(mess[3])
        await bot.send_message(msg.from_user.id, add_coin_list(name, status, money, price))

    else:
        await bot.send_message(msg.from_user.id,    'Для получения статистики отправь /status или /all\n\
/Status - Выводит информацию о монетах которые бот купил и сейчас продает.\n\
/All - Выводит информацию о всех добавленых монет на покупку и продажу.\n\
Для добвления монеты:\n\
add xrp buy - для начала старта покупки монеты.\n\
add xrp sell 1.5 - для начала старта продажи монеты, не меньше чем 1.5$\n\
add xrp sell - для начала старта продажи монеты, не меньше чем цена монеты на время отправления команды боту.\n\
Для удаления монеты:\n\
pop xrp - для удаления монеты из списка.\n\
Статистика обновляется раз в 10 мин.')

if __name__ == '__main__':
    executor.start_polling(dp)