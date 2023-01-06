import os
import sys
from hashlib import sha256
sys.path.append('..')

from socket import AF_INET, SOCK_STREAM, socket
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox
from common.utils import MessageCreator, send_message, get_message, get_host_port
from common.variables import MESSAGE_TEXT


MAIN_FORM, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'register.ui'))


class ClientRegisterUI(QDialog, MAIN_FORM):

    def __init__(self):
        super(ClientRegisterUI, self).__init__()
        self.message_creator = MessageCreator()
        self.host, self.port = get_host_port()

        self.setupUi(self)
        self.init_signals()

    def init_signals(self):
        self.cancelBtn.clicked.connect(self.close)
        self.registerBtn.clicked.connect(self._register_slot)

    def _register_slot(self):
        username = self.username.text()
        password = self.password.text()
        if not username or not password:
            return QMessageBox.critical(
                self,
                'Внимание',
                'Все поля должны быть заполнены',
                QMessageBox.Ok,
            )
        self.client_sock = socket(AF_INET, SOCK_STREAM)
        try:
            self.client_sock.connect((self.host, self.port))
        except ConnectionRefusedError:
            QMessageBox.question(
                self,
                'Внимание',
                'Связь с сервером не установлена',
                QMessageBox.Ok,
            )
            self.close()
        except OSError:
            pass
        password_hash = sha256(password.encode('utf-8')).hexdigest()
        message = self.message_creator.create_register_message(
            username, password_hash)

        self.client_sock.settimeout(10)
        try:
            send_message(self.client_sock, message)
            message = get_message(self.client_sock)
        except TimeoutError:
            QMessageBox.critical(
                self,
                'Внимание',
                'Потеряна связь с сервером',
                QMessageBox.Ok,
            )
        else:
            QMessageBox.critical(
                self,
                '',
                f'{message[MESSAGE_TEXT]}',
                QMessageBox.Ok,
            )
        finally:
            self.client_sock.close()
