import json

from .errors import (
    GetMessageNoDictError, 
    IncorrectDataRecievedError,
    SendMessageNoDictError,
)
from .variables import (
    ENCODING, 
    MAX_PACKAGE_SIZE,
)


def get_host_port(config):
    host = config['SETTINGS'].get('default_address') or 'localhost'
    port = config['SETTINGS'].get('default_port') or '8080'
    return host, port


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
