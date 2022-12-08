import configparser
import os
import sys
from datetime import datetime

from PyQt5.QtCore import QTimer
from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication

sys.path.append('..')

from common.variables import DB_NAME, DB_PATH
from server_db.server_database import ServerStorage

MAIN_FORM, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'form.ui'))


class ServerGui(QMainWindow, MAIN_FORM):

    def __init__(self, config_file_path, server_storage):
        super(ServerGui, self).__init__()
        self.config_file_path = config_file_path
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file_path)
        self.server_storage = server_storage

        self.setupUi(self)

        self.init_users_table()
        self.init_users_stat()
        self.init_settings()
        self.configurate_actions()

    def init_settings(self):
        db_name = self.config['SETTINGS'].get('database_name') or DB_NAME
        db_dir = self.config['SETTINGS'].get('database_dir') or DB_PATH

        self.dbPath.setText(db_dir)
        self.dbName.setText(db_name)
        self.serverIp.setText(self.config['SETTINGS'].get('default_address'))
        self.serverPort.setText(self.config['SETTINGS'].get('default_port'))

    def configurate_actions(self):
        self.settingsSaveBtn.clicked.connect(self.__save_config)

    def init_users_table(self):
        self.table_users_online_headers = [
            'Клиент',
            'IP адрес',
            'Порт',
            'Подключен',
        ]
        self.table_users_online_model = QStandardItemModel()
        self.table_users_online_model.clear()
        self.table_users_online_model.setHorizontalHeaderLabels(
            self.table_users_online_headers)
        self.clientsTable.setModel(self.table_users_online_model)

        online_users = self.server_storage.get_online_users()
        for particle in online_users:
            login, ip, date, port = particle
            date = str(datetime.strftime(date, '%d-%Y-%m %H:%M:%S'))

            login = QStandardItem(login)
            ip = QStandardItem(ip)
            port = QStandardItem(str(port))
            date = QStandardItem(date)

            login.setEditable(False)
            ip.setEditable(False)
            port.setEditable(False)
            date.setEditable(False)

            self.table_users_online_model.appendRow((login, ip, port, date))

    def init_users_stat(self):
        self.table_users_stat_headers = [
            'Клиент',
            'Отправлено',
            'Получено',
            'Вход',
        ]
        self.table_users_stat_model = QStandardItemModel()
        self.table_users_stat_model.clear()
        self.table_users_stat_model.setHorizontalHeaderLabels(
            self.table_users_stat_headers
        )
        self.historyTable.setModel(self.table_users_stat_model)

        history = self.server_storage.get_user_msg_counts()
        for particle in history:
            login, send, accept, last_login = particle
            last_login = str(datetime.strftime(last_login, '%d-%Y-%m %H:%M:%S'))

            login = QStandardItem(login)
            send = QStandardItem(str(send))
            accept = QStandardItem(str(accept))
            last_login = QStandardItem(last_login)

            login.setEditable(False)
            send.setEditable(False)
            accept.setEditable(False)
            last_login.setEditable(False)

            self.table_users_stat_model.appendRow((login, send, accept, last_login))

    def set_timer(self, interval):
        self.__timer = QTimer()
        self.__timer.timeout.connect(self.__timer_tables_update)
        self.__timer.start(interval)

    def __timer_tables_update(self):
        self.init_users_table()
        self.init_users_stat()

    def __save_config(self):
        config = self.config

        db_dir = config['SETTINGS'].get('database_dir')
        if db_dir is not None:
            config['SETTINGS']['database_dir'] = self.dbPath.text()
        db_name = config['SETTINGS'].get('database_name')
        if db_name is not None:
            config['SETTINGS']['database_name'] = self.dbName.text()
        else:
            config['SETTINGS'].setdefault('database_name', self.dbName.text())
        db_port = config['SETTINGS'].get('default_port')
        if db_port is not None:
            config['SETTINGS']['default_port'] = self.serverPort.text()
        else:
            config['SETTINGS'].setdefault('default_port', self.serverPort.text())
        db_ip = config['SETTINGS'].get('default_address')
        if db_ip is not None:
            config['SETTINGS']['default_address'] = self.serverIp.text()
        else:
            config['SETTINGS'].setdefault('default_address', self.serverIp.text())

        with open(self.config_file_path, 'w', encoding='utf-8') as f:
            config.write(f)
