from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import json
import sys
import os
import threading
import datetime

class Admin_win(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(200, 100, 1440, 900)
        self.setFixedSize(1440, 900)
        self.setWindowTitle('Admin System')

        # 设置窗口的背景图片，引用资源目录下的图片
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(QPixmap("../res/background.jpg")))
        self.setPalette(palette)

        self.tab_win = QTabWidget(self)
        self.tab_win.setGeometry(0, 80, 1440, 800)

        self.now_time = datetime.datetime.now()

        self.time_l = QLCDNumber(self)
        self.time_l.setGeometry(1020, 24, 400, 70)
        self.time_l.setDigitCount(19)
        self.time_l.setMode(QLCDNumber.Dec)
        self.time_l.setSegmentStyle(QLCDNumber.Flat)
        self.time_l.setStyleSheet("border: 2px solid black; color: solid black; background: silver;")
        self.time_l.display(self.now_time.strftime("%Y-%m-%d %H:%M:%S"))

        self.now_timer = threading.Timer(0, self.now_thread)
        self.now_timer.setDaemon(True)
        self.now_timer.start()

        save_act = QAction('&Save', self)
        save_act.setToolTip("Save")
        save_act.setShortcut('Ctrl+S')
        save_act.setStatusTip('save infomation')
        save_act.triggered.connect(self.save_info)

        exit_act = QAction('&Quit', self)
        exit_act.setToolTip("Quit")
        exit_act.setShortcut('Ctrl+W')
        exit_act.setStatusTip('Exit application')
        exit_act.setFont(QFont("黑体", 10))
        exit_act.triggered.connect(qApp.quit)

        add_act = QAction('&Add', self)
        add_act.setToolTip("Add")
        add_act.setShortcut('Ctrl+A')
        add_act.setStatusTip('Add new')
        add_act.setFont(QFont("黑体", 10))
        add_act.triggered.connect(self.table_insert)

        edit_act = QAction('&Edit', self)
        edit_act.setToolTip("Edit")
        edit_act.setShortcut('Ctrl+E')
        edit_act.setStatusTip('Edit exist')
        edit_act.setFont(QFont("黑体", 10))
        edit_act.triggered.connect(self.table_edit)

        del_act = QAction('&Del', self)
        del_act.setToolTip("Del")
        del_act.setShortcut('Ctrl+D')
        del_act.setStatusTip('Delete selected')
        del_act.setFont(QFont("黑体", 10))
        del_act.triggered.connect(self.table_delete)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(save_act)
        file_menu.addAction(exit_act)

        edit_menu = menubar.addMenu('&Edit')
        edit_menu.addAction(add_act)
        edit_menu.addAction(edit_act)
        edit_menu.addAction(del_act)

        self.event_tab = Event_tabel()
        self.people_tab = People_tabel()
        self.speech_tab = Speech_tabel()

        self.tab_win.addTab(self.people_tab, "people")
        self.tab_win.addTab(self.speech_tab, "speech")
        self.tab_win.addTab(self.event_tab, "events")
        self.tab_win.setFont(QFont("黑体", 12))

        self.add_button = QPushButton(self)
        self.add_button.move(5, 30)
        self.add_button.setFixedWidth(100)
        self.add_button.setFixedHeight(40)
        self.add_button.clicked.connect(self.table_insert)
        self.add_button.setText("Add")
        self.add_button.setFont(QFont("黑体", 18))
        self.add_button.setStyleSheet("border: 2px solid black; color: black; background: silver;")

        self.edit_button = QPushButton(self)
        self.edit_button.move(115, 30)
        self.edit_button.setFixedWidth(100)
        self.edit_button.setFixedHeight(40)
        self.edit_button.clicked.connect(self.table_edit)
        self.edit_button.setText("Edit")
        self.edit_button.setFont(QFont("黑体", 18))
        self.edit_button.setStyleSheet("border: 2px solid black; color: black; background: silver;")

        self.del_button = QPushButton(self)
        self.del_button.move(225, 30)
        self.del_button.setFixedWidth(100)
        self.del_button.setFixedHeight(40)
        self.del_button.clicked.connect(self.table_delete)
        self.del_button.setText("Delete")
        self.del_button.setFont(QFont("黑体", 18))
        self.del_button.setStyleSheet("border: 2px solid black; color: black; background: silver;")

    def table_insert(self):
        self.tab_win.currentWidget().add_item()

    def table_delete(self):
        self.tab_win.currentWidget().del_item()

    def table_edit(self):
        self.tab_win.currentWidget().edit_item()

    def save_info(self):
        self.people_tab.save_info()
        self.speech_tab.save_info()
        self.event_tab.save_info()
        QMessageBox.question(self,
                             'Save',
                             "Save success",
                             QMessageBox.Yes)

    def now_thread(self):
        self.now_time = datetime.datetime.now()
        # Log("Now time is ", self.now_time)
        self.time_l.display(self.now_time.strftime("%Y-%m-%d %H:%M:%S"))

        self.now_timer = threading.Timer(1, self.now_thread)
        self.now_timer.setDaemon(True)
        self.now_timer.start()

    def closeEvent(self, event):
        reply = QMessageBox.question(self,
                                     'Exit',
                                     "Have you saved and sure to quit？",
                                     QMessageBox.Yes |QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            os._exit(0)
        else:
            event.ignore()


class People_tabel(QTableWidget):

    class EditDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setGeometry(600, 300, 400, 200)
            self.setFont(QFont("黑体", 12))
            self.setFixedSize(self.width(), self.height())
            self.setStyleSheet("background:white;")
            # 设置窗口的属性为ApplicationModal模态，用户只有关闭弹窗后，才能关闭主界面
            self.setWindowModality(Qt.ApplicationModal)

            self.ok = QPushButton("ok", self)
            self.ok.move(110, 170)
            self.cancel = QPushButton("cancel", self)
            self.cancel.move(210, 170)
            self.cancel.clicked.connect(self.close)

            self.id_lab = QLabel(self)
            self.id_lab.setGeometry(70, 20, 54, 20)
            self.id_lab.setText("ID:")
            self.id_line = QLineEdit(self)
            self.id_line.setGeometry(120, 20, 220, 20)
            self.name_lab = QLabel(self)
            self.name_lab.setGeometry(70, 50, 54, 20)
            self.name_lab.setText("Name:")
            self.name_line = QLineEdit(self)
            self.name_line.setGeometry(120, 50, 220, 20)
            self.birth_lab = QLabel(self)
            self.birth_lab.setGeometry(70, 80, 54, 20)
            self.birth_lab.setText("Birth:")
            self.birth_line = QLineEdit(self)
            self.birth_line.setGeometry(120, 80, 220, 20)
            self.event_lab = QLabel(self)
            self.event_lab.setGeometry(70, 110, 54, 20)
            self.event_lab.setText("Events:")
            self.event_line = QLineEdit(self)
            self.event_line.setGeometry(120, 110, 220, 20)
            self.rank_lab = QLabel(self)
            self.rank_lab.setGeometry(70, 140, 54, 20)
            self.rank_lab.setText("Rank:")
            self.rank_line = QLineEdit(self)
            self.rank_line.setGeometry(120, 140, 220, 20)

    def __init__(self):
        super().__init__()
        self.setColumnCount(5)
        self.setFont(QFont("黑体", 12))
        self.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置表格的选取方式是行选取
        self.setSelectionMode(QAbstractItemView.SingleSelection)  # 设置选取方式为单个选取
        self.setHorizontalHeaderLabels(["ID", "Name", "Birth", "Event", "Rank"])  # 设置行表头
        self.verticalHeader().setVisible(False) # 隐藏列表头
        self.setFocusPolicy(Qt.NoFocus)

        self.people = {}
        self.people_file = "../data/people.json"

        self.load_info()

    def load_info(self):
        with open(self.people_file, 'r') as load_f:
            self.people = json.load(load_f)
        load_f.close()

        self.setColumnCount(5)
        self.setRowCount(len(self.people['people']))

        for i, person in zip(range(len(self.people['people'])), self.people['people']):
            for j, col in zip(range(len(person)), person.values()):
                item = QTableWidgetItem(col)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.setItem(i, j, item)

    def save_info(self):
        with open(self.people_file, 'w') as load_f:
            json.dump(self.people, load_f)
        load_f.close()

    def add_item(self):
        self.input_win = self.EditDialog()
        self.input_win.setWindowTitle("Add")
        self.input_win.ok.clicked.connect(self.push_add_ok)
        self.input_win.exec_()

    def edit_item(self):
        row_select = self.selectedItems()
        if len(row_select) == 0:
            return

        self.input_win = self.EditDialog()
        self.input_win.setWindowTitle("Edit")
        self.input_win.ok.clicked.connect(self.push_edit_ok)

        self.input_win.id_line.setText(row_select[0].text())
        self.input_win.name_line.setText(row_select[1].text())
        self.input_win.birth_line.setText(row_select[2].text())
        self.input_win.event_line.setText(row_select[3].text())
        self.input_win.rank_line.setText(row_select[4].text())

        self.input_win.exec_()

    def del_item(self):
        row_select = self.selectedItems()
        if len(row_select) == 0:
            return

        ID = row_select[0].text()

        self.people['people'] = [i for i in self.people['people'] if i['id'] != ID]

        rowidx = self.row(row_select[0])
        self.removeRow(rowidx)

    def push_add_ok(self):
        temp = {}
        temp['id'] = self.input_win.id_line.text()
        temp['name'] = self.input_win.name_line.text()
        temp['birth'] = self.input_win.birth_line.text()
        temp['event'] = self.input_win.event_line.text()
        temp['rank'] = self.input_win.rank_line.text()

        new_id = temp['id']

        id_exist = False

        for person in self.people['people']:
            if new_id == person['id']:
                id_exist = True
                wrong_dialog = QDialog()
                wrong_dialog.setWindowTitle("Error")
                wrong_dialog.setGeometry(700, 350, 200, 100)
                wrong_dialog.info = QLabel(wrong_dialog)
                wrong_dialog.info.setGeometry(50, 30, 100, 20)
                wrong_dialog.info.setText("Error: ID exist!")
                wrong_dialog.ok = QPushButton("ok", wrong_dialog)
                wrong_dialog.ok.move(65, 65)
                wrong_dialog.ok.clicked.connect(wrong_dialog.close)
                wrong_dialog.exec_()
                break

        if id_exist is False:
            self.people['people'].append(temp)

            rowcnt = self.rowCount()
            self.insertRow(rowcnt)

            for i, col in zip(range(len(temp)), temp.values()):
                item = QTableWidgetItem(col)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.setItem(rowcnt, i, item)


            self.input_win.close()

    def push_edit_ok(self):
        row_select = self.selectedItems()

        origin ={}
        origin['id'] = row_select[0].text()
        origin['name'] = row_select[1].text()
        origin['birth'] = row_select[2].text()
        origin['event'] = row_select[3].text()
        origin['rank'] = row_select[4].text()

        temp = {}
        temp['id'] = self.input_win.id_line.text()
        temp['name'] = self.input_win.name_line.text()
        temp['birth'] = self.input_win.birth_line.text()
        temp['event'] = self.input_win.event_line.text()
        temp['rank'] = self.input_win.rank_line.text()

        new_id = temp['id']

        id_exist = False

        for person in self.people['people']:
            if new_id == person['id'] and new_id != origin['id']:
                id_exist = True
                wrong_dialog = QDialog()
                wrong_dialog.setWindowTitle("Error")
                wrong_dialog.setGeometry(700, 350, 200, 100)
                wrong_dialog.info = QLabel(wrong_dialog)
                wrong_dialog.info.setGeometry(50, 30, 100, 20)
                wrong_dialog.info.setText("Error: ID exist!")
                wrong_dialog.ok = QPushButton("ok", wrong_dialog)
                wrong_dialog.ok.move(65, 65)
                wrong_dialog.ok.clicked.connect(wrong_dialog.close)
                wrong_dialog.exec_()
                break

        if id_exist is False:
            idx = self.people['people'].index(origin)
            self.people['people'][idx] = temp

            rowidx = self.row(row_select[0])

            for i, col in zip(range(len(temp)), temp.values()):
                item = QTableWidgetItem(col)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.setItem(rowidx, i, item)

            self.input_win.close()

class Event_tabel(QTableWidget):

    class EditDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setGeometry(600, 300, 400, 200)
            self.setFont(QFont("黑体", 12))
            self.setFixedSize(self.width(), self.height())
            self.setStyleSheet("background:white;")
            # 设置窗口的属性为ApplicationModal模态，用户只有关闭弹窗后，才能关闭主界面
            self.setWindowModality(Qt.ApplicationModal)

            self.ok = QPushButton("ok", self)
            self.ok.move(110, 170)
            self.cancel = QPushButton("cancel", self)
            self.cancel.move(210, 170)
            self.cancel.clicked.connect(self.close)

            self.id_lab = QLabel(self)
            self.id_lab.setGeometry(70, 50, 54, 20)
            self.id_lab.setText("ID:")
            self.id_line = QLineEdit(self)
            self.id_line.setGeometry(120, 50, 220, 20)
            self.event_lab = QLabel(self)
            self.event_lab.setGeometry(70, 80, 54, 20)
            self.event_lab.setText("Event:")
            self.event_line = QLineEdit(self)
            self.event_line.setGeometry(120, 80, 220, 20)

    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self.setFont(QFont("黑体", 12))
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setHorizontalHeaderLabels(["ID", "Event"])
        self.verticalHeader().setVisible(False)

        self.events = {}
        self.event_file = "../data/events.json"

        self.load_info()

    def load_info(self):
        with open(self.event_file, 'r') as load_f:
            self.events = json.load(load_f)
        load_f.close()

        self.setColumnCount(2)
        self.setRowCount(len(self.events))

        for i, id, event in zip(range(len(self.events)), self.events, self.events.values()):
            item_0 = QTableWidgetItem(id)
            item_0.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item_1 = QTableWidgetItem(event)
            item_1.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.setItem(i, 0, item_0)
            self.setItem(i, 1, item_1)

    def save_info(self):
        with open(self.event_file, 'w') as load_f:
            json.dump(self.events, load_f)
        load_f.close()

    def add_item(self):
        self.input_win = self.EditDialog()
        self.input_win.setWindowTitle("Add")
        self.input_win.ok.clicked.connect(self.push_add_ok)
        self.input_win.exec_()

    def edit_item(self):
        row_select = self.selectedItems()
        if len(row_select) == 0:
            return

        self.input_win = self.EditDialog()
        self.input_win.setWindowTitle("Edit")
        self.input_win.ok.clicked.connect(self.push_edit_ok)

        self.input_win.id_line.setText(row_select[0].text())
        self.input_win.event_line.setText(row_select[1].text())

        self.input_win.exec_()

    def del_item(self):
        row_select = self.selectedItems()
        if len(row_select) == 0:
            return
        ID = row_select[0].text()
        self.events.pop(ID)
        rowidx = self.row(row_select[0])
        self.removeRow(rowidx)

    def push_add_ok(self):
        id = self.input_win.id_line.text()
        if id in self.events:
            wrong_dialog = QDialog()
            wrong_dialog.setWindowTitle("Error")
            wrong_dialog.setGeometry(700, 350, 200, 100)
            wrong_dialog.info = QLabel(wrong_dialog)
            wrong_dialog.info.setGeometry(50, 30, 100, 20)
            wrong_dialog.info.setText("Error: ID exist!")
            wrong_dialog.ok = QPushButton("ok", wrong_dialog)
            wrong_dialog.ok.move(65, 65)
            wrong_dialog.ok.clicked.connect(wrong_dialog.close)
            wrong_dialog.exec_()
        else:
            self.events[self.input_win.id_line.text()] = self.input_win.event_line.text()

            rowcnt = self.rowCount()
            self.insertRow(rowcnt)

            item0 = QTableWidgetItem(self.input_win.id_line.text())
            item0.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item1 = QTableWidgetItem(self.input_win.event_line.text())
            item1.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.setItem(rowcnt, 0, item0)
            self.setItem(rowcnt, 1, item1)

            self.input_win.close()

    def push_edit_ok(self):
        row_select = self.selectedItems()

        id = self.input_win.id_line.text()
        orign_id = row_select[0].text()

        if id in self.events and id != orign_id:
            wrong_dialog = QDialog()
            wrong_dialog.setWindowTitle("Error")
            wrong_dialog.setGeometry(700, 350, 200, 100)
            wrong_dialog.info = QLabel(wrong_dialog)
            wrong_dialog.info.setGeometry(50, 30, 100, 20)
            wrong_dialog.info.setText("Error: ID exist!")
            wrong_dialog.ok = QPushButton("ok", wrong_dialog)
            wrong_dialog.ok.move(65, 65)
            wrong_dialog.ok.clicked.connect(wrong_dialog.close)
            wrong_dialog.exec_()
        else:
            self.events.pop(orign_id)
            self.events[self.input_win.id_line.text()] = self.input_win.event_line.text()

            row = self.row(row_select[0])

            item0 = QTableWidgetItem(self.input_win.id_line.text())
            item0.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item1 = QTableWidgetItem(self.input_win.event_line.text())
            item1.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.setItem(row, 0, item0)
            self.setItem(row, 1, item1)

            self.input_win.close()


class Speech_tabel(QTableWidget):

    class EditDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setGeometry(600, 300, 400, 300)
            self.setFixedSize(self.width(), self.height())
            self.setFont(QFont("黑体", 12))
            self.setStyleSheet("background:white;")
            # 设置窗口的属性为ApplicationModal模态，用户只有关闭弹窗后，才能关闭主界面
            self.setWindowModality(Qt.ApplicationModal)

            self.ok = QPushButton("ok", self)
            self.ok.move(110, 270)
            self.cancel = QPushButton("cancel", self)
            self.cancel.move(210, 270)
            self.cancel.clicked.connect(self.close)

            self.title_lab = QLabel(self)
            self.title_lab.setGeometry(70, 20, 54, 20)
            self.title_lab.setText("Title:")
            self.title_line = QLineEdit(self)
            self.title_line.setGeometry(120, 20, 220, 20)
            self.person_lab = QLabel(self)
            self.person_lab.setGeometry(70, 50, 54, 20)
            self.person_lab.setText("Person:")
            self.person_line = QLineEdit(self)
            self.person_line.setGeometry(120, 50, 220, 20)
            self.date_lab = QLabel(self)
            self.date_lab.setGeometry(70, 80, 54, 20)
            self.date_lab.setText("Date:")
            self.date_line = QLineEdit(self)
            self.date_line.setGeometry(120, 80, 220, 20)
            self.info_lab = QLabel(self)
            self.info_lab.setGeometry(70, 110, 54, 20)
            self.info_lab.setText("Info:")
            self.info_line = QTextEdit(self)
            self.info_line.setGeometry(120, 110, 220, 100)
            self.img_lab = QLabel(self)
            self.img_lab.setGeometry(70, 220, 54, 20)
            self.img_lab.setText("Image:")
            self.img_line = QLineEdit(self)
            self.img_line.setGeometry(120, 220, 220, 20)

    def __init__(self):
        super().__init__()
        self.setColumnCount(5)
        self.setFont(QFont("黑体", 12))
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setHorizontalHeaderLabels(["Title", "Person", "Date", "Info", "Image"])
        self.verticalHeader().setVisible(False)

        self.speech_info = {}
        self.speech_file = "../data/speech_info.json"

        self.load_info()

    def load_info(self):
        with open(self.speech_file, 'r', encoding='UTF-8') as load_f:
            self.speech_info = json.load(load_f)
        load_f.close()

        self.setColumnCount(5)
        self.setRowCount(len(self.speech_info['data']))
        self.setColumnWidth(0, 200)
        self.setColumnWidth(3, 400)

        for i, info in zip(range(len(self.speech_info['data'])), self.speech_info['data']):
            for j, col in zip(range(len(info)), info.values()):
                item = QTableWidgetItem(col)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.setItem(i, j, item)

    def save_info(self):
        with open(self.speech_file, 'w') as load_f:
            json.dump(self.speech_info, load_f)
        load_f.close()

    def add_item(self):
        self.input_win = self.EditDialog()
        self.input_win.setWindowTitle("Add")
        self.input_win.ok.clicked.connect(self.push_add_ok)
        self.input_win.exec_()

    def edit_item(self):
        row_select = self.selectedItems()
        if len(row_select) == 0:
            return

        self.input_win = self.EditDialog()
        self.input_win.setWindowTitle("Edit")
        self.input_win.ok.clicked.connect(self.push_edit_ok)

        self.input_win.title_line.setText(row_select[0].text())
        self.input_win.person_line.setText(row_select[1].text())
        self.input_win.date_line.setText(row_select[2].text())
        self.input_win.info_line.setPlainText(row_select[3].text())
        self.input_win.img_line.setText(row_select[4].text())

        self.input_win.exec_()

    def del_item(self):
        row_select = self.selectedItems()
        if len(row_select) == 0:
            return

        title = row_select[0].text()

        self.speech_info['data'] = [i for i in self.speech_info['data'] if i['title'] != title]

        rowidx = self.row(row_select[0])
        self.removeRow(rowidx)

    def push_add_ok(self):
        temp = {}
        temp['title'] = self.input_win.title_line.text()
        temp['person'] = self.input_win.person_line.text()
        temp['date'] = self.input_win.date_line.text()
        temp['info'] = self.input_win.info_line.toPlainText()
        temp['image'] = self.input_win.img_line.text()

        self.speech_info['data'].append(temp)

        rowcnt = self.rowCount()
        self.insertRow(rowcnt)

        for i, col in zip(range(len(temp)), temp.values()):
            item = QTableWidgetItem(col)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.setItem(rowcnt, i, item)

        self.input_win.close()

    def push_edit_ok(self):
        row_select = self.selectedItems()

        origin = {}
        origin['title'] = row_select[0].text()
        origin['person'] = row_select[1].text()
        origin['date'] = row_select[2].text()
        origin['info'] = row_select[3].text()
        origin['image'] = row_select[4].text()

        temp = {}
        temp['title'] = self.input_win.title_line.text()
        temp['person'] = self.input_win.person_line.text()
        temp['date'] = self.input_win.date_line.text()
        temp['info'] = self.input_win.info_line.toPlainText()
        temp['image'] = self.input_win.img_line.text()

        idx = self.speech_info['data'].index(origin)
        self.speech_info['data'][idx] = temp

        rowidx = self.row(row_select[0])

        for i, col in zip(range(len(temp)), temp.values()):
            item = QTableWidgetItem(col)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.setItem(rowidx, i, item)

        self.input_win.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    admin_win = Admin_win()

    admin_win.show()

    sys.exit(app.exec_())

