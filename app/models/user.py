from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import string
from psycopg2.extras import DictCursor


class User(UserMixin):
    def __init__(self):
        self.id = None
        self.username = None
        self.email = None
        self.password_hash = None
        self.first_name = ''
        self.last_name = ''
        self.phone = ''
        self.address = ''
        self.is_staff = False
        self.is_admin = False
        self.created_at = None
        self.email_verified = False
        self.verification_token = None
        self.verification_sent_at = None


    @classmethod
    def from_dict(cls, user_data):
        """Создание объекта User из словаря данных"""
        user = cls()
        user.id = user_data['id']
        user.username = user_data['username']
        user.email = user_data['email']
        user.password_hash = user_data['password_hash']
        user.first_name = user_data.get('first_name', '')
        user.last_name = user_data.get('last_name', '')
        user.phone = user_data.get('phone', '')
        user.address = user_data.get('address', '')
        user.is_staff = user_data.get('is_admin', False)
        user.email_verified = user_data.get('email_verified', False)
        user.created_at = user_data.get('created_at')
        return user


    @classmethod
    def get_by_id(cls, user_id):
        """Получить пользователя по ID из базы данных"""
        from app.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)

        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()

        cursor.close()
        conn.close()

        if user_data:
            user = cls()
            user.id = user_data.get('id')
            user.username = user_data.get('username')
            user.email = user_data.get('email')
            user.password_hash = user_data.get('password_hash')
            user.first_name = user_data.get('first_name', '')
            user.last_name = user_data.get('last_name', '')
            user.phone = user_data.get('phone', '')
            user.address = user_data.get('address', '')

            is_admin_value = user_data.get('is_admin', False)
            if isinstance(is_admin_value, bool):
                user.is_admin = is_admin_value
            elif isinstance(is_admin_value, int):
                user.is_admin = is_admin_value == 1
            elif isinstance(is_admin_value, str):
                user.is_admin = is_admin_value.lower() in ['true', '1', 'yes', 't']
            else:
                user.is_admin = False

            user.is_staff = user.is_admin
            user.created_at = user_data.get('created_at')
            user.email_verified = user_data.get('email_verified', False)
            user.verification_token = user_data.get('verification_token')

            return user
        return None


    @staticmethod
    def generate_verification_token(length=32):
        """Генерация токена для подтверждения email"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def is_verification_token_valid(self, token, expiration_hours=24):
        """Проверка валидности токена и срока его действия"""
        if not self.verification_token or not self.verification_sent_at:
            return False

        if self.verification_token != token:
            return False

        expiration_time = self.verification_sent_at + timedelta(hours=expiration_hours)
        return datetime.utcnow() < expiration_time

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id) if self.id else None

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
