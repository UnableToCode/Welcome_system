
from multiprocessing import Pipe
import requests
import json
import time


cur_file = "../data/cur_weather.json"
today_file = "../data/today_weather.json"


def write2file(data, json_file):
    with open(json_file, 'w') as f:
        f.write(json.dumps(data))
    f.close()


# class Weather(object):
#     def __init__(self, time, week, weath, temper, now_weather):
#         self.time = time
#         self.week = week
#         self.weath = weath
#         self.temper = temper
#         self.now_weather = now_weather
#
#
#     def show(self):
#         print("日期：" + self.time + " " + self.week)
#         print("气候：" + self.weath)
#         print("气温：" + self.temper)
#
#     def write2file(self, filename):
#         objectdumps2file(self, filename)


def get_weather_info(mode):

    url = 'https://www.tianqiapi.com/api/'
    headers = {'User-Agent': 'Mozilla/5.0'}

    version = ''
    if mode == 1:

        version = 'v1'

    if mode == 2:
        version = 'v6'

    params = {
        'version': version,
        'appid': '18833238',
        'appsecret': 'PM9hiniT',
    }

    res = requests.get(url, params=params, headers=headers)
    res.encoding = 'utf-8'

    weather = json.loads(res.text)

    return weather


def get_weather(argspipe):
    # city_name = args.city_name
    while True:
        recv_val = argspipe.recv()
        if recv_val == 1:
            cur_weather = get_weather_info(1)

            if cur_weather is None:
                argspipe.send(-1)
            else:
                write2file(cur_weather, cur_file)
                argspipe.send(1)

        elif recv_val == 2:
            today_weather = get_weather_info(2)

            if today_weather is None:
                argspipe.send(-1)

            else:
                write2file(today_weather, today_file)
                argspipe.send(1)
        else:
            argspipe.send(-1)

        time.sleep(1)


# def parse_arguments(argv):
#     parser = argparse.ArgumentParser()
#     parser.add_argument('model', type=int, help='1 for get now weather, 2 for get today weather')
#     return parser.parse_args(argv)


if __name__ == '__main__':
    cur_weather = get_weather_info(1)

    if cur_weather is None:
        print("-1")
    else:
        write2file(cur_weather, cur_file)
        print("0")

