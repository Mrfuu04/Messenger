import os
from datetime import datetime
import sys
sys.path.append('..')

from sqlalchemy import Column, Integer, String, create_engine, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from common.variables import DB_NAME, DB_PATH


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

    class UsersMessagesStatistics(Base):
        """
        Таблица статистики сообщений.
        Хранит в себе пользователя и кол-во
        отправленных и полученных сообщений.
        """
        __tablename__ = 'users_messages_statistics'
        id = Column(Integer, primary_key=True)
        user = Column(String, ForeignKey('users.id'), unique=True)
        accept = Column(Integer, default=0)
        send = Column(Integer, default=0)

        def __init__(self, user, accept, send):
            self.user = user
            self.accept = accept
            self.send = send

    class UserContacts(Base):
        """
        Контакты пользователя
        """
        __tablename__ = 'user_contacts'
        id = Column(Integer, primary_key=True)
        user_id = Column(String, ForeignKey('users.id'))
        contact_id = Column(String, ForeignKey('users.id'))

        user = relationship('Users', foreign_keys=[user_id])
        contact = relationship('Users', foreign_keys=[contact_id])

        def __init__(self, user, contact):
            self.user= user
            self.contact = contact

    def __init__(self, config):
        db_name = config['SETTINGS'].get('database_name') or DB_NAME
        db_dir = config['SETTINGS'].get('database_dir')
        if db_dir:
            db_dir += '/'
        else:
            db_dir = DB_PATH
        db_path = os.path.join(db_dir, db_name)
        engine = create_engine(
            f'sqlite:///{db_path}.db3?check_same_thread=False',
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
            new_msg_cnt_history = self.UsersMessagesStatistics(
                user=user.id,
                send=0,
                accept=0,
            )
            self.session.add(new_msg_cnt_history)

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
            self.ActiveUsers.port,
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

    def update_user_msg_counts(self, sender, recipient):
        """
        Обновляет информацию о кол-ве отправленных и
        полученных сообщений у пользователя.
        """
        sender_id = self.session.query(
            self.Users,
        ).filter_by(
            login=sender,
        ).first().id

        recipient_id = self.session.query(
            self.Users,
        ).filter_by(
            login=recipient,
        ).first().id

        sender_row = self.session.query(
            self.UsersMessagesStatistics
        ).filter_by(user=sender_id).first()
        sender_row.send += 1

        recipient_row = self.session.query(
            self.UsersMessagesStatistics
        ).filter_by(user=recipient_id).first()
        recipient_row.accept += 1

        self.session.commit()


    def get_user_msg_counts(self):
        """
        Возвращает пользователя и кол-во
        отправленных и полученных сообщений.
        """
        history = self.session.query(
            self.Users.login,
            self.UsersMessagesStatistics.send,
            self.UsersMessagesStatistics.accept,
            self.Users.last_login,
        ).join(
            self.Users,
        ).all()

        return history

    def get_user_contacts(self, username):
        """
        Возвращает список контактов пользователя
        """
        result = []
        user = self.session.query(
            self.Users
        ).filter_by(
            login=username,
        ).first()

        if user:
            contacts = self.session.query(
                self.UserContacts,
                self.Users.login,
            ).filter_by(
                user_id=user.id,
            ).join(
                self.UserContacts.contact,
            ).distinct().all()

            result = [x[1] for x in contacts]

        return result

    def add_contact(self, sender, recipient):
        """
        Добавляет пользователя в список контактов
        """
        sender = self.session.query(
            self.Users
        ).filter_by(
            login=sender,
        ).first()

        recipient = self.session.query(
            self.Users,
        ).filter_by(
            login=recipient
        ).first()

        if sender and recipient:
            is_exists = self.session.query(
                self.UserContacts,
            ).filter_by(
                user_id=sender.id,
                contact_id=recipient.id,
            ).all()
            if not is_exists:
                new_contact = self.UserContacts(
                    user=sender,
                    contact=recipient,
                )
                self.session.add(new_contact)
                self.session.commit()

            return True
        return False

    def del_contact(self, sender, recipient):
        """
        Удаляет пользователя из списка контактов
        """
        sender = self.session.query(
            self.Users
        ).filter_by(
            login=sender,
        ).first()

        recipient = self.session.query(
            self.Users,
        ).filter_by(
            login=recipient
        ).first()

        if sender and recipient:
            contacts = self.session.query(
                self.UserContacts,
            ).filter_by(
                user_id=sender.id,
                contact_id=recipient.id,
            )
            if contacts.all():
                contacts.delete()
                self.session.commit()

                return True
        return False
