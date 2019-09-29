#!/usr/bin/python

import demjson
import requests
import datetime
import time

Coinone_API = 'https://api.coinone.co.kr/ticker/?currency=all&format=json'
Telegram_API = 'https://api.telegram.org/bot:xxx/sendMessage?chat_id=&text='
interested_currencies = ['eth','eos','btc','xrp','iota']

def get_currency(url):
	currency_req = requests.get(url)
	currency_json = demjson.decode(currency_req.content)
	return currency_json

def message_builder(interesting_list):
	now = datetime.datetime.fromtimestamp(time.time()+32400).strftime('%Y-%m-%d %H:%M:%S')
	currency_data = get_currency(Coinone_API)
	build_msg = 'Current time : %s'%(now)
	for cur in interesting_list:
		c_last = currency_data[cur]['last']
		build_msg = build_msg + "\n%s : %s"%(cur,c_last)
	return build_msg

def push_message(p_mesg):
	Message_URL = Telegram_API + '%s'%(p_mesg)
	push_req = requests.get(Message_URL)


if __name__   == "__main__":
	final_msg = message_builder(interested_currencies)
	push_message(final_msg)
