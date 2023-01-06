import os
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime, 
    Integer,
    String,
    create_engine, 
    or_,
)
from sqlalchemy.orm import (
    declarative_base, 
    sessionmaker,
)


class ClientStorage:
    """
    Клиентская сторона БД.
    Пока под каждого пользователя создается своя база,
    чтобы избежать дублирование сообщений.
    """
    Base = declarative_base()

    class ChatHistory(Base):
        __tablename__ = 'chat_history'
        id = Column(Integer, primary_key=True)
        date = Column(DateTime)
        sender = Column(String)
        recipient = Column(String)
        message = Column(String)

        def __init__(self, date, sender, recipient, message):
            self.date = date
            self.sender = sender
            self.recipient = recipient
            self.message = message

    def __init__(self, username):
        db_path_folder = os.path.join(
            os.path.dirname(__file__), 'dbs')
        if not os.path.exists(db_path_folder):
            os.mkdir(db_path_folder)
        db_path = os.path.join(db_path_folder, f'{username}.db3')
        
        engine = create_engine(
            f'sqlite:///{db_path}?check_same_thread=False',
            echo=False,
            pool_recycle=7200,
        )
        self.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def get_chat_history(self, username, chat_with):
        messages = self.session.query(
            self.ChatHistory,
        ).order_by(
                self.ChatHistory.date,
        ).filter(
            or_(
                self.ChatHistory.sender == username,
                self.ChatHistory.recipient == username,
            ),
            or_(
                self.ChatHistory.sender == chat_with,
                self.ChatHistory.recipient == chat_with,
            )
        ).all()

        return messages

    def add_message(self, sender, recipient, message):
        new_message = self.ChatHistory(
            date=datetime.now(),
            sender=sender,
            recipient=recipient,
            message=message,
        )

        self.session.add(new_message)
        self.session.commit()
