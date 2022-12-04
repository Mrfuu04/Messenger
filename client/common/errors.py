class SendMessageNoDictError(Exception):

    def __str__(self):
        return 'Аргументом для отправки сообщения может быть только словарь'


class GetMessageNoDictError(Exception):

    def __str__(self):
        return 'Получено письмо не ввиде словаря'


class IncorrectDataRecievedError(Exception):

    def __str__(self):
        return 'Невозможно декодировать строку'
