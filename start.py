#!/usr/bin/env python3
from apprise import Apprise
from binance.client import Client
from os import environ    

def notify(message):
    print("-- Sending notification --")

    apobj = Apprise()
    apobj.add('pover://' + pushover_api_user + '@' + pushover_api_app + '')

    apobj.notify(
        body=message,         title='BinanceTrader',     )
    print(message)

if __name__ == "__main__":

    # API config
    binance_api_key      = environ['BINANCE_API_KEY']
    binance_api_secret   = environ['BINANCE_API_SECRET']
    pushover_api_app     = environ['NOTIFIER_API_APP']
    pushover_api_user    = environ['NOTIFIER_API_USER']

    print("-- Converting dust --")
    binanceClient = Client(binance_api_key, binance_api_secret)
    account = binanceClient.get_account()["balances"]
    balances = []
    for balance in account:
        if float(balance["free"]) > float(0):
            balances.append(balance)

    dusts = []
    # kline_dict['Date']      = kline[0]
    # kline_dict['Open']      = kline[1]
    # kline_dict['High']      = kline[2]
    # kline_dict['Low']       = kline[3]
    # kline_dict['Close']     = kline[4]
    # kline_dict['Adj Close'] = kline[4]
    # kline_dict['Volume']    = kline[5]
    for balance in balances:
        try:
            price = binanceClient.get_historical_klines(balance["asset"] + "BTC", Client.KLINE_INTERVAL_1MINUTE, "1 minute ago")[-1][4]
            price = float(price)
        except:
            price = binanceClient.get_historical_klines("BTC" + balance["asset"], Client.KLINE_INTERVAL_1MINUTE, "1 minute ago")[-1][4]
            price = 1/float(price)
        value = float(price)*float(balance["free"])
        dusts.append({"asset":balance["asset"],"balance":balance["free"],"btc_price":float(price),"btc_balance":value})

    bnb = []
    to_dust = []
    for dust in dusts:
        if dust["asset"] != "BNB":
            if dust["btc_balance"] < 0.0012:
                to_dust.append(dust["asset"])
                print("Found " + dust["asset"] + ": Will convert")
            else:
                print("Found " + dust["asset"] + ": Will leave alone")
        else:
            bnb.append(dust)
            print("Found " + dust["asset"] + ": Will leave alone")
    bnb = bnb[0]

    string = ",".join(to_dust)
    if string == "":
        print("Nothing to convert!")
    else:
        notify("Converting dust for tokens: " + string)
        result = binanceClient.transfer_dust(asset=string)
        print(result)

    print("-- Balancing BNB and USDT --")
    print("Making sure high BNB balance is not being unnecessarily kept in account\nWill keep minimum balance of $10USDT worth of BNB in account to cover trades\nTrade will be executed if over $10USDT excess is detected")

    bnbusdt_price = binanceClient.get_historical_klines("BNBUSDT", Client.KLINE_INTERVAL_1MINUTE, "1 minute ago")[-1][4]
    bnb["usdt_price"] = float(bnbusdt_price)
    bnb["usdt_balance"] = float(bnb["usdt_price"])*float(bnb["balance"])
    if float(bnb["usdt_balance"]) > float(10):
        adjust = float(bnb["usdt_balance"]) - float(10)
        trade_amount = round(float(adjust*1/float(bnb["usdt_price"])),3)
        notify("Should reduce BNB by " + str(round(adjust,2)) + "USD / " + str(trade_amount))
        if adjust > float(10):
            notify("Submitting trade")
            order = binanceClient.create_order(symbol="BNBUSDT",
                                               side="sell",
                                               type="market",
                                               quantity=trade_amount,
                                               recvWindow=1000)
            print(order)
        else:
            notify("Below minimum trade of $10USD")
    else:
        print("BNB Balance is below $10USDT")


















