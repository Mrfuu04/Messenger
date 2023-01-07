import json
from time import time

from .errors import (GetMessageNoDictError, IncorrectDataRecievedError,
                     SendMessageNoDictError)
from .variables import (ACTION, ADD_CONTACT, CONTACTS, DEL_CONTACT,
                        DESTINATION, ENCODING, EXIT, HOST, MAX_PACKAGE_SIZE,
                        MESSAGE, MESSAGE_TEXT, PORT, PRESENCE, REGISTER,
                        SENDER, SERVER, TIME)


def get_host_port():
    return HOST, PORT


def send_message(sock, message):
    """Функция отправки сообщения"""
    if not isinstance(message, dict):
        raise SendMessageNoDictError
    json_msg = json.dumps(message)
    encoded_msg = json_msg.encode(ENCODING)
    sock.send(encoded_msg)


def get_message(sock):
    """Функция приема сообщения."""
    encoded_response = sock.recv(MAX_PACKAGE_SIZE)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise GetMessageNoDictError
    else:
        raise IncorrectDataRecievedError


class MessageCreator:
    """Класс создатель сообщений"""

    def common_message(
            self,
            action=None,
            sender=None,
            destination=None,
            message_text=None,
    ):
        """Базовый метод создания сообщения"""
        message = {
            ACTION: action,
            TIME: time(),
            SENDER: sender,
            DESTINATION: destination,
            MESSAGE_TEXT: message_text,
        }

        return message

    def create_presence(self, username, password):
        """Создает словарь представение клиента"""
        message = self.common_message(
            action=PRESENCE, sender=username, destination=SERVER, message_text=password)

        return message

    def create_message(self, sender, destination, msg_text=None):
        """Создает словарь сообщение клиент-клиент"""
        if msg_text is None:
            msg_text = input('Введите сообщение: ')
        message = self.common_message(
            action=MESSAGE, sender=sender, destination=destination, message_text=msg_text
        )

        return message

    def create_exit_message(self, username):
        """Создает словарь выхода из мессенджеа"""
        message = self.common_message(
            action=EXIT, sender=username, destination=SERVER
        )

        return message

    def create_contacts_request(self, username):
        """Создает словарь запроса списка контактов"""
        message = self.common_message(
            action=CONTACTS, sender=username, destination=SERVER,
        )

        return message

    def create_add_contact_request(self, sender, recipient):
        """
        Создает словарь запроса на добавление
        пользователя в список контактов
        """
        message = self.common_message(
            action=ADD_CONTACT, sender=sender, destination=SERVER, message_text=recipient
        )

        return message

    def create_del_contact_request(self, username, recipient):
        """
        Создает словарь запроса на удаление
        пользователя из списка контактов
        """
        message = self.common_message(
            action=DEL_CONTACT, sender=username, destination=SERVER, message_text=recipient
        )

        return message

    def create_register_message(self, username, password):
        """
        Создает словарь запроса на регистрацию
        пользователя
        """
        message = self.common_message(
            action=REGISTER, sender=username, destination=SERVER, message_text=password
        )

        return message
