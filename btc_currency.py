#!/usr/bin/python
  
import json
import requests
import datetime
import time

BTC_API = 'https://api.bithumb.com/public/ticker/ALL'
Telegram_API = 'https://api.telegram.org/bot7:xxxx/sendMessage?chat_id=&text='
interested_currencies = ['BTC','ETH','EOS','XRP','ADA']

def get_currency(url):
        currency_req = requests.get(url)
        currency_json = json.loads(currency_req.content)
        return currency_json

def message_builder(interesting_list):
        currency_data = get_currency(BTC_API)
        now = datetime.datetime.fromtimestamp(int(currency_data['data']['date'])/1000+32400).strftime('%Y-%m-%d %H:%M:%S')
        build_msg = 'Bithumb Price data\nCurrent time : %s'%(now)
        for cur in interesting_list:
                c_last = currency_data['data'][cur]['closing_price']
                build_msg = build_msg + "\n%s : %s"%(cur,c_last)
        return build_msg

def push_message(p_mesg):
        Message_URL = Telegram_API + '%s'%(p_mesg)
        push_req = requests.get(Message_URL)


if __name__   == "__main__":
        final_msg = message_builder(interested_currencies)
        push_message(final_msg)
