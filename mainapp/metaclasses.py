from dis import get_instructions


class ServerVerifier(type):
    """Метакласс для сервера"""
    def __init__(cls, clsname, bases, clsdict):
        opnames = [
            'LOAD_GLOBAL',
            'LOAD_METHOD',
            'LOAD_ATTR',
        ]
        methods_and_args = set()
        for func in clsdict:
            try:
                res = get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in res:
                    if i.opname in opnames:
                        methods_and_args.add(i.argval)
        if 'connect' in methods_and_args:
            raise TypeError('Метод connect не допустим в классе Сервера')

        if not ('AF_INET' in methods_and_args and 'SOCK_STREAM' in methods_and_args):
            raise TypeError('Некорректная инициализация сокета')

        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    """Метакласс для клиента"""
    def __init__(cls, clsname, bases, clsdict):
        opnames = [
            'LOAD_GLOBAL',
            'LOAD_METHOD',
            'LOAD_ATTR',
        ]
        methods_and_args = set()
        for func in clsdict:
            try:
                res = get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in res:
                    if i.opname in opnames:
                        methods_and_args.add(i.argval)
        if 'accept' in methods_and_args or 'listen' in methods_and_args:
            raise TypeError('Методы accept и listen не допустимы в классе Клиента')

        if not ('AF_INET' in methods_and_args and 'SOCK_STREAM' in methods_and_args):
            raise TypeError('Некорректная инициализация сокета')

        super().__init__(clsname, bases, clsdict)
