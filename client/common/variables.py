# ---- MAIN SETTINGS ---- #
HOST = 'localhost'
PORT = 8080
ENCODING = 'utf-8'
MAX_PACKAGE_SIZE = 1024

# ---- JIM VARIABLES ---- #
ACTION = 'action'
TIME = 'time'
USER = 'user'
SENDER = 'from'
DESTINATION = 'to'
MESSAGE = 'msg'
MESSAGE_TEXT = 'msg_text'

# ---- JIM+ VARIABLES ---- #
SERVER = 'server'
ACCOUNT_NAME = 'account_name'
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
EXIT = 'exit'

# ---- RESPONSES ---- #
RESPONSE_200 = {
    RESPONSE: '200',
    MESSAGE_TEXT: None,
    SENDER: SERVER,
}
RESPONSE_400 = {
    RESPONSE: '400',
    MESSAGE_TEXT: None,
    SENDER: SERVER,
}
RESPONSE_201 = {
    RESPONSE: '201',
    MESSAGE_TEXT: "Имя уже используется",
    SENDER: SERVER,
}
