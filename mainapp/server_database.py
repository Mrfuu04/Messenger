from datetime import datetime

from sqlalchemy import Column, Integer, String, create_engine, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker


class ServerStorage:
    """Серверная сторона БД"""
    Base = declarative_base()

    class Users(Base):
        """
        Таблица пользователей.
        Хранит в себе всех пользователей, которые
        подключались к серверу.
        """
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        last_login = Column(DateTime)

        def __init__(self, login, last_login):
            self.login = login
            self.last_login = last_login

        def __repr__(self):
            return self.login

    class ActiveUsers(Base):
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('users.id'), unique=True)
        ip = Column(String)
        port = Column(Integer)
        time_conn = Column(DateTime)

        def __init__(self, user, ip, port, time_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.time_conn = time_conn

    class LoginHistory(Base):
        __tablename__ = 'login_history'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('users.id'))
        ip = Column(String)
        port = Column(Integer)
        last_conn = Column(DateTime)

        def __init__(self, user, ip, port, last_conn):
            self.user = user
            self.ip = ip
            self.port = port
            self.last_conn = last_conn

    def __init__(self):
        engine = create_engine(
            'sqlite:///server_database.db3?check_same_thread=False',
            echo=False,
            pool_recycle=7200,
        )
        self.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

        # При первом подключении очищаем активных клиентов
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def login(self, username, ip, port):
        """
        Фиксирует подключение пользователя к серверу.
        Запись в таблицу ActiveUsers.
        Также создает пользователя в Users или
        обновляет время его логина, если он уже существует
        """
        user = self.session.query(
            self.Users,
        ).filter_by(
            login=username,
        ).first()
        if user is not None:
            user.last_login = datetime.now()
        else:
            user = self.Users(
                login=username,
                last_login=datetime.now(),
            )
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUsers(
            user=user.id,
            ip=ip,
            port=port,
            time_conn=datetime.now(),
        )
        new_history = self.LoginHistory(
            user=user.id,
            ip=ip,
            port=port,
            last_conn=datetime.now(),
        )

        self.session.add_all((
            new_active_user,
            new_history,
        ))
        self.session.commit()

    def logout(self, username):
        """
        Фиксирует отключение пользователя от сервера.
        Удаляем пользователя из таблицы ActiveUsers.
        """
        user = self.session.query(
            self.Users,
        ).filter_by(
            login=username,
        ).first()
        if user:
            self.session.query(
                self.ActiveUsers,
            ).filter_by(
                user=user.id,
            ).delete()
            self.session.commit()

    def get_userlist(self):
        """
        Возвращает список всех пользователей.
        """
        users = self.session.query(
            self.Users.login,
            self.Users.last_login,
        ).all()

        return users

    def get_online_users(self):
        """
        Возвращает пользователей "В сети".
        """
        online_users = self.session.query(
            self.Users.login,
            self.ActiveUsers.ip,
            self.ActiveUsers.time_conn,
        ).join(
            self.Users,
        ).all()

        return online_users

    def get_loginhistory(self):
        """
        Возвращает историю всех входов.
        """
        users = self.session.query(
            self.Users.login,
            self.LoginHistory.ip,
            self.LoginHistory.port,
            self.LoginHistory.last_conn,
        ).join(
            self.Users,
        ).all()

        return users