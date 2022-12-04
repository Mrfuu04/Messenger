import sys
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from time import sleep, time

from descriptors import Port
from common.variables import SENDER, MESSAGE_TEXT, ACTION, PRESENCE, TIME, MESSAGE, DESTINATION, \
    EXIT, SERVER, RESPONSE_201
from common.metaclasses import ClientVerifier
from common.utils import get_host_port, get_message, send_message


class Client(metaclass=ClientVerifier):
    port = Port()

    def __init__(self):
        self.host, self.port = get_host_port()

    def run(self):
        client_sock = socket(AF_INET, SOCK_STREAM)
        try:
            client_sock.connect((self.host, self.port))
        except ConnectionRefusedError:
            sys.exit(1)
        except OSError:
            print('Подключение уже установлено')

        self.login(client_sock)

        user_interface_thread = Thread(
            target=self.user_interface, args=(client_sock,), daemon=True)
        reciever_interface_thread = Thread(
            target=self.reciever_interface, args=(client_sock,), daemon=True)
        user_interface_thread.start()
        reciever_interface_thread.start()
        while True:
            sleep(1)
            if user_interface_thread.is_alive() and \
                    reciever_interface_thread.is_alive():
                continue
            break

    def reciever_interface(self, sock):
        """Интерфейс получения сообщения"""
        while True:
            try:
                message = get_message(sock)
                print(f'{message[SENDER]}: {message[MESSAGE_TEXT]}')
            except:
                break

    def user_interface(self, sock):
        """Интерфейс пользовательского ввода"""
        print('*** Для вывода всех доступных команд введите help ***')
        while True:
            command = input('Введите команду: ')
            if command == 'help':
                self.get_help_message()
            elif command == 'message':
                destination = input('Введите имя получателя: ')
                message = self.create_message(self.username, destination)
                send_message(sock, message)
            elif command == 'exit':
                message = self.create_exit_message(self.username)
                send_message(sock, message)
                sleep(1)
                break

    def login(self, sock):
        while True:
            self.username = input('Введите имя пользователя: ')
            presence = self.create_presence(self.username)
            send_message(sock, presence)
            presence_response = get_message(sock)
            if presence_response == RESPONSE_201:
                print(presence_response[MESSAGE_TEXT])
            else:
                print(presence_response[MESSAGE_TEXT])
                break

    def create_presence(self, username):
        """Создает словарь представение клиента"""
        message = {
            ACTION: PRESENCE,
            TIME: time(),
            SENDER: username,
            DESTINATION: SERVER,
        }
        return message

    def create_message(self, sender, destination):
        """Создает словарь сообщение клиент-клиент"""
        msg_text = input('Введите сообщение: ')
        message = {
            ACTION: MESSAGE,
            TIME: time(),
            SENDER: sender,
            DESTINATION: destination,
            MESSAGE_TEXT: msg_text,
        }
        return message

    def create_exit_message(self, username):
        """Создает словарь выхода из мессенджеа"""
        message = {
            ACTION: EXIT,
            TIME: time(),
            SENDER: username,
            DESTINATION: SERVER,
        }

        return message

    def get_help_message(self):
        print(
            "help - вывод всех доступных комманд\n"
            "message - написать сообщение пользователю\n"
            "exit - выйти из программы\n"
        )


if __name__ == '__main__':
    client = Client()
    client.run()
