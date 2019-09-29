#!/usr/bin/python
# -*- coding: utf-8 -*-

import demjson
import requests
import datetime
import time
import numpy as np
import cPickle
import os.path
#from scipy.spatial.distance import mahalanobis
import logging

max_list_cnt = 60 / 5 * 168 
pickle_base = '/home/myall1977_2/cryptocurrency/save/'
coinone_api = 'https://api.coinone.co.kr/ticker/?currency=all&format=json'
telegram_api = 'https://api.telegram.org/bot7:xxx/sendMessage?chat_id=&text='
#interested_currencies = ['eth','bch','btc']
interested_currencies = ['eth','eos']
mahalanobis_distance_threshold = 2.5
log_file = '/home/myall1977_2/cryptocurrency/log/coinone_alert_test.log'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler(log_file)
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

class get_currency:
	def __init__(self, _api_url):
		_currency_req = requests.get(_api_url)
		self._currency_json = demjson.decode(_currency_req.content)
	def values(self, _currency_name, _value_name):
		# Possible value names : volume, last, yesterday_last, yesterday_low, high, currency, low, yesterday_first, yesterday_volume, yesterday_high, first
		# Possible currency name : bch, qtum, ltc, etc, btc, eth, xrp,
		return self._currency_json[_currency_name][_value_name]
	def timestamp(self):
                print self._currency_json            
		datetime.datetime.fromtimestamp(int(self._currency_json["timestamp"])+32400).strftime('%Y-%m-%d %H:%M:%S')
		return datetime.datetime.fromtimestamp(int(self._currency_json["timestamp"])+32400).strftime('%Y-%m-%d %H:%M:%S')

class control_currency:
	def __init__(self, _currency_name):
		# pickle로 저장하는 dump file의 이름을 정의함 (ex eth_save.p)
		self._currency_name = pickle_base + _currency_name + "_1_save.p"
	# 기존 리스트를 Load한 이후 최신 값을 append 시킴.
	def load_values(self,_last_curr):
		# 파일의 존재 유무를 확인해서 존재하면 파일을 load한후 append하고 없을 경우 last_curr로 리스트 생성함.
		if os.path.isfile(self._currency_name):
			self._list_dump = cPickle.load(open(self._currency_name, 'rb'))
			self._original_list_dump = cPickle.load(open(self._currency_name, 'rb'))
			# max_list_cnt로 정의된 숫자만큼만 리스트에 유지함. 초과하면 FIFO로 삭제됨.

			while len(self._list_dump) > max_list_cnt:
				self._list_dump.pop()
			self._list_dump.insert(0,int(_last_curr))
		else:
			self._list_dump = [int(_last_curr)]
			self._original_list_dump = self._list_dump
		return self._list_dump
	# 파일에 업데이트된 list를 save
	def dump_to_file(self):
		cPickle.dump(self._list_dump, open(self._currency_name, 'wb'))
	def mahalanobis_breakthrough(self):
		arr = np.array(self._original_list_dump)
		last = self._list_dump[0] # 현재값
		mean = np.mean(arr) # 평균값
		std = np.std(arr) # 표준편차
		min = np.min(arr) # Minimums
		max = np.max(arr) # Maximum
		maha = abs(last-mean)/std # mahalanobis distance
		logger.info("%s %f %f %d %d"%(self._currency_name,mean,std,min,max))
		# 이전 고점, 저점 돌파
		if max < last:
			alert = [ 3, max ]
		elif last < min:
			alert = [ 2, min ]
		elif maha > mahalanobis_distance_threshold:
			alert = [ 1, maha ]
		else:
			alert = [ 0, maha ]
		return alert

	def gap_value(self):
		if len(self._list_dump) > 1:
			_gap = int(self._list_dump[0]) - int(self._list_dump[1])
			_percent = float(_gap) / int(self._list_dump[0]) * 100
		else:
			_gap = 0
			_percent = 0
		return [_gap,_percent]

def build_message(_timestamp,_currency_name,_currency_value,_reason,_gap):
	_build_msg = 'Current time : %s'%(_timestamp)
	_build_msg = _build_msg + "\n%s : %s (%s, %d %f)"%(_currency_name,_currency_value,_reason,_gap[0],_gap[1])
	return _build_msg

def send_message(_message):
	_push_url = telegram_api + '%s'%(_message)
	push_req = requests.get(_push_url)
	return push_req.status_code


if __name__   == "__main__":
	cd = get_currency(coinone_api)
	now = cd.timestamp()
	for currency_name in interested_currencies:
		currency_last = cd.values(currency_name,"last")
		cl = control_currency(currency_name)
		# 파일에서 최근 value를 load함.
		cl.load_values(currency_last)
		value_gap = cl.gap_value()
		alert_reason = cl.mahalanobis_breakthrough()
		logger.info('%s %s %s %d %f'%(currency_name,currency_last,alert_reason,value_gap[0],value_gap[1]))
		cl.dump_to_file()
		logger.debug("%s - dump completed"%currency_name)
		if alert_reason[0] > 0:
			if alert_reason[0] == 3:
				messages = build_message(now,currency_name,currency_last,"over MAX",value_gap)
				result = send_message(messages)
				logger.info(result)
			if alert_reason[0] == 2:
				messages = build_message(now,currency_name,currency_last,"below MIN",value_gap)
				result = send_message(messages)
				logger.info(result)
			if alert_reason[0] == 1 and abs(value_gap[1]) > 0.8 :
				messages = build_message(now,currency_name,currency_last,"over Mahalanobis",value_gap)
				result = send_message(messages)
				logger.info(result)
