import os
import sys
from hashlib import sha256

sys.path.append('..')

from socket import (
    AF_INET,
    SOCK_STREAM, 
    socket,
)

from common.utils import (
    MessageCreator,
    get_host_port,
    get_message,
    send_message,
)
from common.variables import MESSAGE_TEXT
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QDialog, 
    QMessageBox,
)

MAIN_FORM, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'register.ui'))


class ClientRegisterUI(QDialog, MAIN_FORM):

    def __init__(self):
        super(ClientRegisterUI, self).__init__()
        self.message_creator = MessageCreator()
        self.host, self.port = get_host_port()
        self.message_show = QMessageBox()

        self.setupUi(self)
        self.init_signals()

    def init_signals(self):
        self.cancelBtn.clicked.connect(self.close)
        self.registerBtn.clicked.connect(self._register_slot)

    def _register_slot(self):
        username = self.username.text()
        password = self.password.text()
        if not username or not password:
            return self.message_show.critical(
                self,
                'Внимание',
                'Все поля должны быть заполнены',
                self.message_show.Ok,
            )
        self.client_sock = socket(AF_INET, SOCK_STREAM)
        try:
            self.client_sock.connect((self.host, self.port))
        except ConnectionRefusedError:
            self.message_show.question(
                self,
                'Внимание',
                'Связь с сервером не установлена',
                self.message_show.Ok,
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
            self.message_show.critical(
                self,
                'Внимание',
                'Потеряна связь с сервером',
                self.message_show.Ok,
            )
        else:
            self.message_show.critical(
                self,
                '',
                f'{message[MESSAGE_TEXT]}',
                self.message_show.Ok,
            )
        finally:
            self.client_sock.close()
