import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, text
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
    birthdate = Column(String)  # Дата рождения в формате YYYY-MM-DD
    interests = Column(Text)  # Интересы пользователя для AI и друзей
    created_at = Column(DateTime, default=datetime.utcnow)

class ClosePerson(Base):
    __tablename__ = 'close_people'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(String, nullable=False)
    person_id = Column(String)
    name = Column(String, nullable=False)
    relation = Column(String)  # Кто это: папа, мама, друг и т.д.
    gender = Column(String)
    birthdate = Column(String)
    interests = Column(Text)
    age = Column(Integer)  # Оставляем для совместимости
    created_at = Column(DateTime, default=datetime.utcnow)

class Invitation(Base):
    __tablename__ = 'invitations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(String, nullable=False)
    invited_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class WishlistItem(Base):
    __tablename__ = 'wishlist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)  # Название подарка
    description = Column(Text)  # Описание
    price = Column(String)  # Цена
    url = Column(String)  # Ссылка на товар
    image_url = Column(String)  # URL картинки
    created_at = Column(DateTime, default=datetime.utcnow)

class GiftBooking(Base):
    __tablename__ = 'gift_bookings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, nullable=False)  # ID товара из wishlist
    booked_by = Column(String, nullable=False)  # User ID кто забронировал
    created_at = Column(DateTime, default=datetime.utcnow)

class PersonalGiftIdea(Base):
    __tablename__ = 'personal_gift_ideas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(String, nullable=False)  # User ID кто создал идею
    for_person_id = Column(String, nullable=False)  # Для кого эта идея (person_id из close_people)
    title = Column(String, nullable=False)  # Название подарка
    description = Column(Text)  # Описание
    price = Column(String)  # Цена
    url = Column(String)  # Ссылка на товар
    image_url = Column(String)  # URL картинки
    created_at = Column(DateTime, default=datetime.utcnow)

# Database класс
class Database:
    def __init__(self):
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Создаём движок с настройками пула соединений
        self.engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        
        # Создаём таблицы
        Base.metadata.create_all(self.engine)
        
        # Добавляем колонку relation если её нет (миграция)
        self._migrate_add_relation_column()
        
        # Создаём фабрику сессий
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
    
    def _migrate_add_relation_column(self):
        """Добавляем колонки если их нет"""
        try:
            with self.engine.connect() as conn:
                # Добавляем relation в close_people
                try:
                    conn.execute(text("ALTER TABLE close_people ADD COLUMN IF NOT EXISTS relation VARCHAR"))
                except Exception as e:
                    print(f"Migration: close_people.relation - {e}")

                # Добавляем birthdate в users
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS birthdate VARCHAR"))
                except Exception as e:
                    print(f"Migration: users.birthdate - {e}")

                # Добавляем interests в users
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS interests TEXT"))
                except Exception as e:
                    print(f"Migration: users.interests - {e}")

                conn.commit()
        except Exception as e:
            print(f"Migration general error: {e}")
    
    def get_session(self):
        return self.Session()
    
    def safe_commit(self, session):
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    
    def add_user(self, user_id, username=None, first_name=None):
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
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            if user:
                return {
                    'user_id': user.user_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'birthdate': user.birthdate,
                    'interests': user.interests,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
            return None
        finally:
            session.close()

    def update_user_profile(self, user_id, birthdate=None, interests=None):
        """Обновить профиль пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            if user:
                if birthdate is not None:
                    user.birthdate = birthdate
                if interests is not None:
                    user.interests = interests
                self.safe_commit(session)
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_close_person(self, owner_id, name, person_id=None, relation='', gender='', birthdate='', interests='', age=None):
        session = self.get_session()
        try:
            person = ClosePerson(
                owner_id=str(owner_id),
                person_id=str(person_id) if person_id else None,
                name=name,
                relation=relation,
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
        session = self.get_session()
        try:
            people = session.query(ClosePerson).filter_by(owner_id=str(owner_id)).order_by(ClosePerson.created_at.desc()).all()
            
            return [{
                'id': p.id,
                'owner_id': p.owner_id,
                'person_id': p.person_id,
                'name': p.name,
                'relation': p.relation,
                'gender': p.gender,
                'birthdate': p.birthdate,
                'interests': p.interests,
                'age': p.age,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in people]
        finally:
            session.close()
    
    def update_close_person(self, person_db_id, **kwargs):
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

    # === WISHLIST МЕТОДЫ ===

    def add_wishlist_item(self, user_id, title, description='', price='', url='', image_url=''):
        """Добавить товар в wishlist"""
        session = self.get_session()
        try:
            item = WishlistItem(
                user_id=str(user_id),
                title=title,
                description=description,
                price=price,
                url=url,
                image_url=image_url
            )
            session.add(item)
            self.safe_commit(session)
            return item.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_wishlist(self, user_id):
        """Получить wishlist пользователя"""
        session = self.get_session()
        try:
            items = session.query(WishlistItem).filter_by(user_id=str(user_id)).order_by(WishlistItem.created_at.desc()).all()

            return [{
                'id': item.id,
                'user_id': item.user_id,
                'title': item.title,
                'description': item.description,
                'price': item.price,
                'url': item.url,
                'image_url': item.image_url,
                'created_at': item.created_at.isoformat() if item.created_at else None
            } for item in items]
        finally:
            session.close()

    def update_wishlist_item(self, item_id, **kwargs):
        """Обновить товар в wishlist"""
        session = self.get_session()
        try:
            item = session.query(WishlistItem).filter_by(id=item_id).first()
            if item:
                for key, value in kwargs.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                self.safe_commit(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_wishlist_item(self, item_id):
        """Удалить товар из wishlist"""
        session = self.get_session()
        try:
            item = session.query(WishlistItem).filter_by(id=item_id).first()
            if item:
                session.delete(item)
                self.safe_commit(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # === БРОНИРОВАНИЕ ПОДАРКОВ ===

    def book_gift(self, item_id, booked_by):
        """Забронировать подарок"""
        session = self.get_session()
        try:
            # Проверяем, не забронирован ли уже
            existing = session.query(GiftBooking).filter_by(item_id=item_id).first()
            if existing:
                return None  # Уже забронирован

            booking = GiftBooking(item_id=item_id, booked_by=str(booked_by))
            session.add(booking)
            self.safe_commit(session)
            return booking.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def unbook_gift(self, item_id, booked_by):
        """Отменить бронирование подарка"""
        session = self.get_session()
        try:
            booking = session.query(GiftBooking).filter_by(
                item_id=item_id,
                booked_by=str(booked_by)
            ).first()
            if booking:
                session.delete(booking)
                self.safe_commit(session)
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_wishlist_with_bookings(self, user_id, viewer_id):
        """Получить wishlist с информацией о бронированиях

        Args:
            user_id: ID владельца wishlist
            viewer_id: ID того, кто смотрит wishlist

        Returns:
            Список товаров с полями:
            - Если viewer_id == user_id: показываем счётчик забронированных
            - Если viewer_id != user_id: скрываем забронированные другими
        """
        session = self.get_session()
        try:
            items = session.query(WishlistItem).filter_by(user_id=str(user_id)).order_by(WishlistItem.created_at.desc()).all()

            result = []
            for item in items:
                booking = session.query(GiftBooking).filter_by(item_id=item.id).first()

                # Если смотрит владелец
                if str(viewer_id) == str(user_id):
                    result.append({
                        'id': item.id,
                        'user_id': item.user_id,
                        'title': item.title,
                        'description': item.description,
                        'price': item.price,
                        'url': item.url,
                        'image_url': item.image_url,
                        'created_at': item.created_at.isoformat() if item.created_at else None,
                        'is_booked': booking is not None,
                        'is_owner': True
                    })
                # Если смотрит другой пользователь
                else:
                    # Скрываем забронированные другими
                    if booking and booking.booked_by != str(viewer_id):
                        continue

                    result.append({
                        'id': item.id,
                        'user_id': item.user_id,
                        'title': item.title,
                        'description': item.description,
                        'price': item.price,
                        'url': item.url,
                        'image_url': item.image_url,
                        'created_at': item.created_at.isoformat() if item.created_at else None,
                        'is_booked': booking is not None and booking.booked_by == str(viewer_id),
                        'is_owner': False
                    })

            return result
        finally:
            session.close()

    def get_booked_count(self, user_id):
        """Получить количество забронированных подарков для пользователя"""
        session = self.get_session()
        try:
            items = session.query(WishlistItem).filter_by(user_id=str(user_id)).all()
            item_ids = [item.id for item in items]

            count = session.query(GiftBooking).filter(GiftBooking.item_id.in_(item_ids)).count()
            return count
        finally:
            session.close()

    # === ЛИЧНЫЕ ИДЕИ ПОДАРКОВ ===

    def add_personal_gift_idea(self, owner_id, for_person_id, title, description='', price='', url='', image_url=''):
        """Добавить личную идею подарка для близкого человека"""
        session = self.get_session()
        try:
            idea = PersonalGiftIdea(
                owner_id=str(owner_id),
                for_person_id=str(for_person_id),
                title=title,
                description=description,
                price=price,
                url=url,
                image_url=image_url
            )
            session.add(idea)
            self.safe_commit(session)
            return idea.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_personal_gift_ideas(self, owner_id, for_person_id):
        """Получить личные идеи подарков для конкретного близкого"""
        session = self.get_session()
        try:
            ideas = session.query(PersonalGiftIdea).filter_by(
                owner_id=str(owner_id),
                for_person_id=str(for_person_id)
            ).order_by(PersonalGiftIdea.created_at.desc()).all()

            return [{
                'id': idea.id,
                'owner_id': idea.owner_id,
                'for_person_id': idea.for_person_id,
                'title': idea.title,
                'description': idea.description,
                'price': idea.price,
                'url': idea.url,
                'image_url': idea.image_url,
                'created_at': idea.created_at.isoformat() if idea.created_at else None
            } for idea in ideas]
        finally:
            session.close()

    def update_personal_gift_idea(self, idea_id, **kwargs):
        """Обновить личную идею подарка"""
        session = self.get_session()
        try:
            idea = session.query(PersonalGiftIdea).filter_by(id=idea_id).first()
            if idea:
                for key, value in kwargs.items():
                    if hasattr(idea, key):
                        setattr(idea, key, value)
                self.safe_commit(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_personal_gift_idea(self, idea_id):
        """Удалить личную идею подарка"""
        session = self.get_session()
        try:
            idea = session.query(PersonalGiftIdea).filter_by(id=idea_id).first()
            if idea:
                session.delete(idea)
                self.safe_commit(session)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

# Создаём экземпляр базы данных
db = Database()