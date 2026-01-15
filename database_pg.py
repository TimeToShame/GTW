import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime

# Получаем URL базы данных из переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')

# SQLAlchemy Base
Base = declarative_base()

# Модели
class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(String, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ClosePerson(Base):
    __tablename__ = 'close_people'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(String, nullable=False)
    person_id = Column(String)
    name = Column(String, nullable=False)
    gender = Column(String)
    birthdate = Column(String)
    interests = Column(Text)
    age = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Invitation(Base):
    __tablename__ = 'invitations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(String, nullable=False)
    invited_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database класс
class Database:
    def __init__(self):
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Создаём движок с настройками пула соединений
        self.engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Проверка соединения перед использованием
            pool_recycle=300,    # Переподключение каждые 5 минут
        )
        
        # Создаём таблицы
        Base.metadata.create_all(self.engine)
        
        # Создаём фабрику сессий
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
    
    def get_session(self):
        """Получить сессию с автоматическим rollback при ошибке"""
        return self.Session()
    
    def safe_commit(self, session):
        """Безопасный коммит с обработкой ошибок"""
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    
    def add_user(self, user_id, username=None, first_name=None):
        """Добавить пользователя"""
        session = self.get_session()
        try:
            existing = session.query(User).filter_by(user_id=str(user_id)).first()
            if not existing:
                user = User(user_id=str(user_id), username=username, first_name=first_name)
                session.add(user)
                self.safe_commit(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user(self, user_id):
        """Получить пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            if user:
                return {
                    'user_id': user.user_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
            return None
        finally:
            session.close()
    
    def add_close_person(self, owner_id, name, person_id=None, gender='', birthdate='', interests='', age=None):
        """Добавить близкого человека"""
        session = self.get_session()
        try:
            person = ClosePerson(
                owner_id=str(owner_id),
                person_id=str(person_id) if person_id else None,
                name=name,
                gender=gender,
                birthdate=birthdate,
                interests=interests,
                age=age
            )
            session.add(person)
            self.safe_commit(session)
            return person.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_close_people(self, owner_id):
        """Получить всех близких пользователя"""
        session = self.get_session()
        try:
            people = session.query(ClosePerson).filter_by(owner_id=str(owner_id)).order_by(ClosePerson.created_at.desc()).all()
            
            return [{
                'id': p.id,
                'owner_id': p.owner_id,
                'person_id': p.person_id,
                'name': p.name,
                'gender': p.gender,
                'birthdate': p.birthdate,
                'interests': p.interests,
                'age': p.age,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in people]
        finally:
            session.close()
    
    def update_close_person(self, person_db_id, **kwargs):
        """Обновить данные близкого человека"""
        session = self.get_session()
        try:
            person = session.query(ClosePerson).filter_by(id=person_db_id).first()
            if person:
                for key, value in kwargs.items():
                    if hasattr(person, key):
                        setattr(person, key, value)
                self.safe_commit(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_close_person(self, person_db_id):
        """Удалить близкого человека"""
        session = self.get_session()
        try:
            person = session.query(ClosePerson).filter_by(id=person_db_id).first()
            if person:
                session.delete(person)
                self.safe_commit(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_close_people(self, person_db_ids):
        """Удалить несколько близких людей"""
        session = self.get_session()
        try:
            session.query(ClosePerson).filter(ClosePerson.id.in_(person_db_ids)).delete(synchronize_session=False)
            self.safe_commit(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_invitation(self, inviter_id, invited_id):
        """Добавить приглашение"""
        session = self.get_session()
        try:
            existing = session.query(Invitation).filter_by(
                inviter_id=str(inviter_id),
                invited_id=str(invited_id)
            ).first()
            
            if not existing:
                invitation = Invitation(inviter_id=str(inviter_id), invited_id=str(invited_id))
                session.add(invitation)
                self.safe_commit(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def check_invitation(self, inviter_id, invited_id):
        """Проверить существует ли приглашение"""
        session = self.get_session()
        try:
            invitation = session.query(Invitation).filter_by(
                inviter_id=str(inviter_id),
                invited_id=str(invited_id)
            ).first()
            
            if invitation:
                return {
                    'id': invitation.id,
                    'inviter_id': invitation.inviter_id,
                    'invited_id': invitation.invited_id,
                    'created_at': invitation.created_at.isoformat() if invitation.created_at else None
                }
            return None
        finally:
            session.close()

# Создаём экземпляр базы данных
db = Database()