import json
import sys

# sys.path.append('..')
from time import sleep

from .errors import SendMessageNoDictError, GetMessageNoDictError
from .variables import HOST, PORT, ENCODING, MAX_PACKAGE_SIZE, MESSAGE_TEXT


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
    json_response = encoded_response.decode(ENCODING)
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise GetMessageNoDictError()
