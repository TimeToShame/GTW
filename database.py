import sqlite3
from datetime import datetime
import json

class Database:
    def __init__(self, db_path='gift_bot.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица близких людей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS close_people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                person_id TEXT,
                name TEXT NOT NULL,
                gender TEXT,
                birthdate TEXT,
                interests TEXT,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица приглашений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inviter_id TEXT NOT NULL,
                invited_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inviter_id) REFERENCES users(user_id),
                FOREIGN KEY (invited_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # === ПОЛЬЗОВАТЕЛИ ===
    
    def add_user(self, user_id, username=None, first_name=None):
        """Добавить пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        ''', (str(user_id), username, first_name))
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id):
        """Получить пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (str(user_id),))
        user = cursor.fetchone()
        
        conn.close()
        return dict(user) if user else None
    
    # === БЛИЗКИЕ ЛЮДИ ===
    
    def add_close_person(self, owner_id, name, person_id=None, gender='', birthdate='', interests='', age=None):
        """Добавить близкого человека"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO close_people (owner_id, person_id, name, gender, birthdate, interests, age)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(owner_id), str(person_id) if person_id else None, name, gender, birthdate, interests, age))
        
        person_db_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return person_db_id
    
    def get_close_people(self, owner_id):
        """Получить всех близких пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM close_people 
            WHERE owner_id = ? 
            ORDER BY created_at DESC
        ''', (str(owner_id),))
        
        people = cursor.fetchall()
        conn.close()
        
        return [dict(person) for person in people]
    
    def update_close_person(self, person_db_id, **kwargs):
        """Обновить данные близкого человека"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['name', 'gender', 'birthdate', 'interests', 'age']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            conn.close()
            return
        
        values.append(person_db_id)
        
        query = f"UPDATE close_people SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def delete_close_person(self, person_db_id):
        """Удалить близкого человека"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM close_people WHERE id = ?', (person_db_id,))
        
        conn.commit()
        conn.close()
    
    def delete_close_people(self, person_db_ids):
        """Удалить несколько близких людей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(person_db_ids))
        cursor.execute(f'DELETE FROM close_people WHERE id IN ({placeholders})', person_db_ids)
        
        conn.commit()
        conn.close()
    
    # === ПРИГЛАШЕНИЯ ===
    
    def add_invitation(self, inviter_id, invited_id):
        """Добавить приглашение"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, нет ли уже такого приглашения
        cursor.execute('''
            SELECT id FROM invitations 
            WHERE inviter_id = ? AND invited_id = ?
        ''', (str(inviter_id), str(invited_id)))
        
        existing = cursor.fetchone()
        
        if not existing:
            cursor.execute('''
                INSERT INTO invitations (inviter_id, invited_id)
                VALUES (?, ?)
            ''', (str(inviter_id), str(invited_id)))
            
            conn.commit()
        
        conn.close()
    
    def check_invitation(self, inviter_id, invited_id):
        """Проверить существует ли приглашение"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM invitations 
            WHERE inviter_id = ? AND invited_id = ?
        ''', (str(inviter_id), str(invited_id)))
        
        invitation = cursor.fetchone()
        conn.close()
        
        return dict(invitation) if invitation else None


# Создаём экземпляр базы данных
db = Database()
