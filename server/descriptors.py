class Port:
    """Дескриптор порта"""
    DEFAULT_PORT = 7777

    def __set__(self, instance, value):
        value = int(value)
        if value < 0 or value >= 65535:
            print(f'Недопустимое значение для порта - {value}\n'
                  f'Присваиваю стандартное значение - {self.DEFAULT_PORT}')
            instance.__dict__[self.name] = self.DEFAULT_PORT
        else:
            instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
