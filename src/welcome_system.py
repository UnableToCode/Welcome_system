from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from multiprocessing import Process, Pipe
from src.get_weather import get_weather
from src.video import face_regcon
import sys
import json
import datetime
import time
import threading
import os

log_file = "../log.txt"
out_mode = 0


def Log(*msg):
    now = datetime.datetime.now()
    if out_mode == 0:
        print(now, ": ", *msg)
    elif out_mode == 1:
        with open(log_file, 'a+') as write_log:
            logmsg = str(now) + ": "
            for i in msg:
                logmsg += str(i)
            logmsg += '\n'
            write_log.write(logmsg)


class Welcome_system(QMainWindow):
    def __init__(self):
        # noinspection PyArgumentList
        super().__init__()
        self.people = {}
        self.event = {}
        self.weather_info = {}
        self.speech_info = {}
        self.people_file = "../data/people.json"
        self.event_file = "../data/events.json"
        self.weather_file = "../data/cur_weather.json"
        self.speech_file = "../data/speech_info.json"
        self.father_weather, self.weather = Pipe()
        self.father_face, self.face = Pipe()
        self.run_time = datetime.timedelta()
        self.now_time = datetime.datetime.now()
        self.face_detect = False

        self.weather_l = Weather_win(self, 1200, 200, 240, 400)
        self.time_l = QLCDNumber(self)
        self.people_l = QLabel(self)
        self.event_l = QLabel(self)
        self.speech_l = Speech_win(self, 750, 100, 400, 600)

        self.run_timer = threading.Timer(0, self.count_runtime)
        self.run_timer.setDaemon(True)
        self.face_timer = threading.Timer(0, self.face_thread)
        self.face_timer.setDaemon(True)
        self.speech_timer = threading.Timer(0, self.speech_thread)
        self.speech_timer.setDaemon(True)
        self.now_timer = threading.Timer(0, self.now_thread)
        self.now_timer.setDaemon(True)

        self.p_weather = Process(target=get_weather, args=(self.weather,))
        self.p_face = Process(target=face_regcon, args=(self.face,))

        self.init_config()
        self.initUI()

    def initUI(self):
        # 设置窗口的位置和大小
        self.setGeometry(100, 80, 1440, 900)
        self.setFixedSize(1440, 900)
        # 设置窗口的标题
        self.setWindowTitle('Welcome System')
        # 设置窗口的图标，引用当前目录下的web.png图片
        # self.setWindowIcon(QIcon('web.png'))

        # 设置窗口的背景图片，引用资源目录下的图片
        # palette = QPalette()
        # palette.setBrush(QPalette.Background, QBrush(QPixmap("../res/background.jpg")))
        # self.setPalette(palette)
        self.setStyleSheet("background: rgb(234, 237, 247);")

        self.weather_l.set_info(self.weather_info)
        self.weather_l.raise_()
        self.weather_l.show()

        # 每小时更新一次
        next_hour = datetime.datetime.now() + datetime.timedelta(hours=1)
        next_hour = next_hour.replace(minute=0, second=0, microsecond=0)
        interval = (next_hour - datetime.datetime.now()).total_seconds()
        self.hour_timer = threading.Timer(interval, self.renewal_cur_weather)
        self.hour_timer.start()

        self.people_l.setGeometry(0, 200, 1440, 300)
        self.event_l.setGeometry(0, 200, 1440, 300)
        self.time_l.setGeometry(1020, 5, 400, 80)
        self.time_l.setDigitCount(19)
        self.time_l.setMode(QLCDNumber.Dec)
        self.time_l.setSegmentStyle(QLCDNumber.Flat)
        self.time_l.setStyleSheet("border-style:outset; border-width:4px; border-radius:10px; border-color:rgb(255, 255, 255, 200);"
                                    "color: solid black; background: rgb(192, 192, 192, 50);")
        self.time_l.display(self.now_time.strftime("%Y-%m-%d %H:%M:%S"))

        self.speech_timer.start()
        self.now_timer.start()

        # 显示窗口
        self.show()

    def init_config(self):
        self.read_event_list()
        self.read_people_list()
        self.read_speech_lsit()

        self.p_weather.start()
        self.p_face.start()

        self.renewal_today_weather(repeat=False)
        # self.father_weather.send(1)
        # if self.father_weather.recv() == -1:
        #     Log("renewal today weather failed!")
        #     exit(-1)
        # else:
        #     Log("renewal today weather info success")

        self.renewal_cur_weather(repeat=False)

        # self.father_weather.send(2)
        # if self.father_weather.recv() == -1:
        #     Log("renewal cur weather failed!")
        #     exit(-1)
        # else:
        #     Log("renewal cur weather info success")

        # 获取明天时间
        next_day = datetime.datetime.now() + datetime.timedelta(days=1)

        # 获取明天0点时间
        next_day = next_day.replace(hour=0, minute=0, second=0, microsecond=0)

        # 获取距离明天0点时间，单位为秒
        timer_start_time = (next_day - datetime.datetime.now()).total_seconds()
        # print(timer_start_time)

        # 定时器,参数为(多少时间后执行，单位为秒，执行的方法)
        self.day_timer = threading.Timer(timer_start_time, self.renewal_today_weather)
        self.day_timer.start()
        self.run_timer.start()
        self.face_timer.start()

        Log("init config success.")

    def read_people_list(self):
        with open(self.people_file, 'r') as load_f:
            readin = json.load(load_f)
            for i in readin["people"]:
                # print(i)
                self.people[i['id']] = Person(i)
        load_f.close()
        Log("read people list success.")

    def read_event_list(self):
        with open(self.event_file, 'r') as load_f:
            self.event = json.load(load_f)
            # print(self.event)
        load_f.close()
        Log("read events list success.")

    def read_speech_lsit(self):
        with open(self.speech_file, 'r', encoding='UTF-8') as load_f:
           self.speech_info = json.load(load_f)
        load_f.close()
        Log("read speech list success.")

    def stages(self):
        # Log("stage1")
        if self.face_detect is True:
            # Log("stage1 to stage2")
            face_queue = []
            ret = self.father_face.recv()
            # print("recv")
            # print(ret)

            if ret != -1:
                face_queue = ret

            for id in face_queue:
                # print(id)
                if id != -1:
                    Log("stage1 to stage2!")
                    self.people_l.setText(self.people[id].name)
                    self.people_l.setFont(QFont("黑体", 16))
                    self.people_l.setStyleSheet("border: 2px solid black; color: black; background: rgb(192, 192, 192, 50);")
                    self.people_l.raise_()
                    self.people_l.show()
                    people_timer = threading.Timer(3, self.people_l.hide)
                    people_timer.start()

                    event_id = self.check_event(id)
                    if event_id == '-1':
                        Log("No event,back to stage1")
                        continue
                    cur_event = self.event[event_id]
                    Log("stage2 to stage3")
                    Log(cur_event)
                    self.event_l.setText(cur_event)
                    self.event_l.setFont(QFont("黑体", 16))
                    self.event_l.setStyleSheet("border: 2px solid black; color: black; background: rgb(255, 241, 67, 50);")
                    self.event_l.raise_()
                    self.event_l.show()
                    event_timer = threading.Timer(2, self.event_l.hide)
                    event_timer.start()

                    Log("stage3 to stage1")
                else:
                    Log("No check!")
        self.face_detect = False

    def check_event(self, person_id):
        return self.people[str(person_id)].event

    def renewal_today_weather(self, repeat=True):
        self.father_weather.send(1)
        if self.father_weather.recv() == -1:
            Log("renewal today weather failed!")
            exit(-1)
        else:
            Log("renewal today weather info success")

        if repeat is True:
            self.day_timer = threading.Timer(86400, self.renewal_today_weather)
            self.day_timer.setDaemon(True)
            self.day_timer.start()

    def renewal_cur_weather(self, repeat=True):
        self.father_weather.send(2)
        if self.father_weather.recv() == -1:
            Log("renewal cur weather failed!")
            exit(-1)
        else:
            Log("renewal cur weather info success")
            with open(self.weather_file, 'r') as load_f:
                self.weather_info = json.load(load_f)
            # print(self.event)
            load_f.close()
            Log("read weather info success.")

        if repeat is True:
            self.weather_l.set_info(self.weather_info)
            self.weather_l.raise_()
            self.weather_l.show()

            self.hour_timer = threading.Timer(3600, self.renewal_cur_weather)
            self.hour_timer.setDaemon(True)
            self.hour_timer.start()

    def count_runtime(self):
        self.run_time += datetime.timedelta(seconds=1)
        print("system has run for ", self.run_time)

        self.run_timer = threading.Timer(1, self.count_runtime)
        self.run_timer.setDaemon(True)
        self.run_timer.start()

    def face_thread(self):
        if self.face_detect is False:
            self.face_detect = True
            self.stages()

        self.face_timer = threading.Timer(4, self.face_thread)
        self.face_timer.setDaemon(True)
        self.face_timer.start()

    def now_thread(self):
        self.now_time = datetime.datetime.now()
        # Log("Now time is ", self.now_time)
        self.time_l.display(self.now_time.strftime("%Y-%m-%d %H:%M:%S"))

        self.now_timer = threading.Timer(1, self.now_thread)
        self.now_timer.setDaemon(True)
        self.now_timer.start()

    def speech_thread(self):
        for i in self.speech_info['data']:
            self.speech_l.set_info(i)
            self.speech_l.raise_()
            self.speech_l.show()
            time.sleep(10)

        self.speech_timer = threading.Timer(10, self.speech_thread)
        self.speech_timer.setDaemon(True)
        self.speech_timer.start()

    def closeEvent(self, event):
        """
        对MainWindow的函数closeEvent进行重构
        退出软件时结束所有进程
        :param event:
        :return:
        """
        reply = QMessageBox.question(self,
                                     'Exit',
                                     "Quit？",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            self.p_face.terminate()
            self.p_weather.terminate()
            os._exit(0)
        else:
            event.ignore()


class Person:
    def __init__(self, person):
        self.id = person["id"]
        self.name = person["name"]
        self.birth = person["birth"]
        self.event = person["event"]
        self.rank = person["rank"]


class Speech_win(QWidget):
    def __init__(self, father, x, y, w, h):
        super().__init__(parent=father)
        self.setGeometry(x, y, w, h)
        self.title = QLabel(self)
        self.title.setGeometry(0, 0, w, 0.05 * h)
        self.person = QLabel(self)
        self.person.setGeometry(0, 0.07 * h, w, 0.05 * h)
        self.pic = QLabel(self)
        self.pic.setGeometry(0, 0.14 * h, 0.50 * w, 0.50 * h)
        self.date = QLabel(self)
        self.date.setGeometry(0, 0.66 * h, w, 0.05 * h)
        self.info = QLabel(self)
        self.info.setGeometry(0, 0.75 * h, w, 0.25 * h)

    def set_info(self, info):
        self.title.setText(info['title'])
        self.title.setFont(QFont("黑体", 20))
        self.title.raise_()
        self.title.show()

        self.person.setText(info['person'])
        self.person.setFont(QFont("黑体", 20))
        self.person.raise_()
        self.person.show()

        self.pic.setStyleSheet("border: 2px solid black;")

        self.date.setText(info['date'])
        self.date.setFont(QFont("黑体", 20))
        self.date.raise_()
        self.date.show()

        self.info.setText(info['info'])
        self.info.setFont(QFont("黑体", 18))
        self.info.setStyleSheet("border-style:outset; border-width:4px; border-radius:10px; border-color:rgb(255, 255, 255, 30);"
                                "color: black; background: rgb(141, 168, 237, 30);")
        self.info.raise_()
        self.info.show()

        self.pic.setPixmap(QPixmap("../res/speech_image/" + info['image']))
        self.pic.setScaledContents(True)
        self.pic.raise_()
        self.pic.show()


class Weather_win(QWidget):
    def __init__(self, father, x, y, w, h):
        super(Weather_win, self).__init__(parent=father)
        self.setGeometry(x, y, w, h)
        self.pic = QLabel(self)
        self.pic.setGeometry(0, 0, w - 3, 0.3 * h)
        self.city = QTextBrowser(self)
        self.city.setGeometry(0, 0.3 * h + 2, w - 3, 0.1 * h)
        self.wea = QTextBrowser(self)
        self.wea.setGeometry(0, 0.4 * h + 4, w - 3, 0.1 * h)
        self.tem = QTextBrowser(self)
        self.tem.setGeometry(0, 0.5 * h + 6, w - 3, 0.1 * h)
        self.wind = QTextBrowser(self)
        self.wind.setGeometry(0, 0.6 * h + 8, w - 3, 0.1 * h)
        self.humidity = QTextBrowser(self)
        self.humidity.setGeometry(0, 0.7 * h + 10, w - 3, 0.1 * h)
        self.air = QTextBrowser(self)
        self.air.setGeometry(0, 0.8 * h + 12, w - 3, 0.1 * h)

    def set_info(self, info):
        self.pic.setPixmap(QPixmap("../res/weather_image/" + info['data'][0]['hours'][0]['wea'] + ".png"))
        self.pic.setAlignment(Qt.AlignCenter)
        self.pic.raise_()
        self.pic.show()

        self.city.setText(info['city'])
        self.city.setFont(QFont("黑体", 14))
        self.city.setStyleSheet("border-style:outset; border-width:4px; border-radius:10px; border-color:rgb(255, 255, 255, 30);"
                                "color: black; background: rgb(227, 202, 185, 100);")
        self.city.raise_()
        self.city.show()

        self.wea.setText(info['data'][0]['hours'][0]['wea'])
        self.wea.setFont(QFont("黑体", 14))
        self.wea.setStyleSheet("border-style:outset; border-width:4px; border-radius:10px; border-color:rgb(255, 255, 255, 30);"
                                "color: black; background: rgb(227, 202, 185, 100);")
        self.wea.raise_()
        self.wea.show()

        self.tem.setText(
            "气温:" + info['data'][0]['hours'][0]['tem'] + "  " + info['data'][0]['tem1'] + "/" + info['data'][0][
                'tem2'])
        self.tem.setFont(QFont("黑体", 14))
        self.tem.setStyleSheet("border-style:outset; border-width:4px; border-radius:10px; border-color:rgb(255, 255, 255, 30);"
                                "color: black; background: rgb(227, 202, 185, 100);")
        self.tem.raise_()
        self.tem.show()

        self.wind.setText("风力:" + info['data'][0]['hours'][0]['win'] + "  " + info['data'][0]['hours'][0]['win_speed'])
        self.wind.setFont(QFont("黑体", 14))
        self.wind.setStyleSheet("border-style:outset; border-width:4px; border-radius:10px; border-color:rgb(255, 255, 255, 30);"
                                "color: black; background: rgb(227, 202, 185, 100);")
        self.wind.raise_()
        self.wind.show()

        self.humidity.setText("湿度:" + str(info['data'][0]['humidity']))
        self.humidity.setFont(QFont("黑体", 14))
        self.humidity.setStyleSheet("border-style:outset; border-width:4px; border-radius:10px; border-color:rgb(255, 255, 255, 30);"
                                "color: black; background: rgb(227, 202, 185, 100);")
        self.humidity.raise_()
        self.humidity.show()

        self.air.setText("空气指数:" + str(info['data'][0]['air']) + "  " + info['data'][0]['air_level'])
        self.air.setFont(QFont("黑体", 14))
        self.air.setStyleSheet("border-style:outset; border-width:4px; border-radius:10px; border-color:rgb(255, 255, 255, 30);"
                                "color: black; background: rgb(227, 202, 185, 100);")
        self.air.raise_()
        self.air.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    win = Welcome_system()

    sys.exit(app.exec_())

