import configparser
import os
from socket import socket, AF_INET, SOCK_STREAM
from select import select
from threading import Thread
from time import sleep

from descriptors import Port
from common.variables import ACTION, PRESENCE, RESPONSE_200, \
    SENDER, EXIT, MESSAGE, RESPONSE_400, DESTINATION, TIME, MESSAGE_TEXT, RESPONSE_201
from server_db.server_database import ServerStorage
from common.metaclasses import ServerVerifier
from common.utils import get_host_port, send_message, get_message
from common import variables


class Server(
    metaclass=ServerVerifier,
):
    port = Port()

    def __init__(self, config):
        self.server_storage = ServerStorage(config)
        self.host, self.port = get_host_port(config)
        self.client_sockets = []
        self.messages = []
        self.names = dict()

    def run(self):
        frontside = Thread(
            target=self._frontside, daemon=True,
        )
        backside = Thread(
            target=self._backside, daemon=True,
        )
        frontside.start()
        backside.start()

        while True:
            sleep(1)
            if frontside.is_alive() and backside.is_alive():
                continue
            break

    def _frontside(self):
        """
        Поток консольного управления.
        """
        print('*** Для вывода справки введите help ***')
        while True:
            command = input('Введите команду: ')
            if command == 'help':
                print(self.__print_help_message())
            elif command == 'userlist':
                print(self.get_userlist())
            elif command == 'online':
                print(self.get_online_users())
            elif command == 'history':
                print(self.get_loginhistory())
            elif command == 'exit':
                break

    def _backside(self):
        """
        Поток обработки сообщений.
        """
        with socket(AF_INET, SOCK_STREAM) as server_sock:
            server_sock.bind((self.host, self.port))
            server_sock.listen(variables.SERVER_MAX_LISTEN)
            server_sock.settimeout(variables.SERVER_SETTIMEOUT)

            while True:
                try:
                    client, addr = server_sock.accept()
                except TimeoutError:
                    pass
                else:
                    self.client_sockets.append(client)
                finally:
                    try:
                        writers_list, getters_list = [], []
                        writers_list, getters_list, _ = select(
                            self.client_sockets,
                            self.client_sockets,
                            [],
                            0,
                        )
                    except OSError:
                        pass
                    if writers_list:
                        for writer in writers_list:
                            try:
                                self.process_client_message(writer)
                            except Exception as e:
                                print(e)
                                self.client_sockets.remove(writer)
                                writer.close()
                    for message in self.messages:
                        try:
                            self.process_message(message, getters_list)
                        except ConnectionError:
                            try:
                                del self.names[message[DESTINATION]]
                            except KeyError:
                                pass
                            self.client_sockets.remove(self.names[message[DESTINATION]])
                    self.messages.clear()

    def process_message(self, message, getters_list):
        """
        Парсинг сообщения типа клиент-клиент
        """
        if message[DESTINATION] in self.names and self.names.get(message[DESTINATION]) in getters_list:
            send_message(self.names[message[DESTINATION]], message)
        elif message[DESTINATION] in self.names and self.names.get(DESTINATION) not in getters_list:
            raise ConnectionError
        else:
            response = RESPONSE_400
            response[MESSAGE_TEXT] = 'Пользователь не найден'
            send_message(self.names[message[SENDER]], response)

    def process_client_message(self, client_sock):
        """
        Парсит сообщение от клиентского
        сокета и возвращает ответ.
        В случае, если сообщение не вида клиент-клиент или оно
        некорректно, то отправляет ответ пользователю
        """
        message = get_message(client_sock)
        print(message)
        # Если сообщение представление, то отвечаем пользователю
        if message[ACTION] == PRESENCE:
            if message[SENDER] not in self.names.keys():
                self.names[message[SENDER]] = client_sock
                ip, port = client_sock.getpeername()
                self.server_storage.login(message[SENDER], ip, port)
                response = RESPONSE_200
                response[MESSAGE_TEXT] = 'Добро пожаловать!'
                send_message(client_sock, response)
            else:
                send_message(client_sock, RESPONSE_201)
        # Сообщение о выходе
        elif message[ACTION] == EXIT:
            response = RESPONSE_200
            response[MESSAGE_TEXT] = 'До свидания!'
            send_message(client_sock, response)
            self.server_storage.logout(message[SENDER])
            self.client_sockets.remove(self.names[message[SENDER]])
            client_sock.close()
            del self.names[message[SENDER]]
        # Сообщение клиент-клиент
        elif (message[ACTION] == MESSAGE and
              message[SENDER] and
              message[DESTINATION] and
              message[TIME]):
            self.messages.append(message)
        else:
            response = RESPONSE_400
            response[MESSAGE_TEXT] = 'Некорректный запрос'
            send_message(client_sock, response)

    def get_userlist(self):
        users = self.server_storage.get_userlist()
        out_msg = 'Список пользователей: \n'
        for user in users:
            login, _, _, date = user
            out_msg += f'{login}, последний логин: {date.strftime("%D %T")}\n'

        return out_msg

    def get_online_users(self):
        users = self.server_storage.get_online_users()
        out_msg = 'Список пользователей онлайн: \n'
        for user in users:
            login, ip, date = user
            out_msg += f'{login} {ip}, время подключения {date.strftime("%D %T")}\n'

        return out_msg

    def get_loginhistory(self):
        users = self.server_storage.get_loginhistory()
        out_msg = 'Список коннектов: \n'
        for user in users:
            login, ip, port, last_conn = user
            out_msg += f'{login} {ip}:{port} {last_conn}\n'

        return out_msg

    def __print_help_message(self):
        help_message = """Доступные команды: 
        userlist - список всех пользователей
        online - список подключённых пользователей
        history - история подключений
        exit - завершение работы сервера
        help - помощь"""

        return help_message


if __name__ == '__main__':
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.relpath(__file__))
    config_file_path = os.path.join(dir_path, 'conf.ini')
    config.read(config_file_path)
    server = Server(config=config)
    server.run()