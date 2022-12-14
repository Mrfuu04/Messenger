import json
import sys
import threading
import time

sys.path.append('..')
from logging import getLogger
import logs.log_config
from common.utils import (
    MessageCreator,
    get_message,
    send_message,
)
from common.variables import (
    DESTINATION,
    MESSAGE_TEXT,
    RESPONSE,
    RESPONSE_200, 
    SENDER,
    SERVER,
)
from db.client_db import ClientStorage
from PyQt5.QtCore import (
    QObject, 
    pyqtSignal,
)


class Transport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, client_sock, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.running = True
        self.socket_lock = threading.Lock()

        self.logger = getLogger('client')
        self.client_storage = ClientStorage(username)
        self.message_creator = MessageCreator()
        self.client_sock = client_sock
        self.username = username

    def get_contact_list(self):
        """Запрос на получение списка контактов"""
        with self.socket_lock:
            message = self.message_creator.create_contacts_request(self.username)
            send_message(self.client_sock, message)
            response = get_message(self.client_sock)
            if response[RESPONSE] != RESPONSE_200:
                return None
            return response

    def add_contact(self, recipient):
        """Запрос на добавление контакта"""
        with self.socket_lock:
            message = self.message_creator.create_add_contact_request(
                self.username,
                recipient,
            )
            send_message(self.client_sock, message)
            response = get_message(self.client_sock)

            return response[MESSAGE_TEXT]

    def del_contact(self, recipient):
        with self.socket_lock:
            message = self.message_creator.create_del_contact_request(
                self.username,
                recipient,
            )
            send_message(self.client_sock, message)
            response = get_message(self.client_sock)

            return response[MESSAGE_TEXT]

    def send_message(self, recipient, msg_text):
        """Отправка сообщения"""
        with self.socket_lock:
            message = self.message_creator.create_message(
                self.username,
                recipient,
                msg_text=msg_text,
            )

            send_message(self.client_sock, message)

            self.client_storage.add_message(
                self.username,
                recipient,
                msg_text,
            )

    def send_exit_message(self):
        """Отправка сообщения о выходе"""
        with self.socket_lock:
            message = self.message_creator.create_exit_message(self.username)
            send_message(self.client_sock, message)
            self.logger.info(
                'Самостоятельное отключение клиента от сервера'
            )

    def get_chat_history(self, chat_with):
        """Запрос на получение истории сообщений"""
        messages = self.client_storage.get_chat_history(self.username, chat_with)
        return self.username, messages

    def process_message(self, message):
        """Обработка сообщения и добавление его в БД"""
        sender = message[SENDER]
        if sender == SERVER:
            pass
        else:
            recipient = message[DESTINATION]
            msg_text = message[MESSAGE_TEXT]
            self.client_storage.add_message(
                sender,
                recipient,
                msg_text,
            )
            self.new_message.emit(sender)

    def run(self) -> None:
        """Основной метод потока приема сообщений"""
        while self.running:
            # если не сделать тут задержку, то отправка может
            # достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with self.socket_lock:
                try:
                    self.client_sock.settimeout(0.5)
                    message = get_message(self.client_sock)
                except OSError as err:
                    if err.errno:
                        self.logger.warning(
                            'Потеряно соединение с сервером'
                        )
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (
                        ConnectionError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError,
                        TypeError,
                ):
                    self.logger.warning(
                        'Потеряно соединение с сервером'
                    )
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    if not message[SENDER] == SERVER:
                        self.process_message(message)
                finally:
                    self.client_sock.settimeout(5)
