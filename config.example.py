import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # Безопасность
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Отладка
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

    # База данных PostgreSQL (для raw SQL через psycopg2)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'shoe_shop')  # или shop_db если другая
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your-db-password')

    # Файлы
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = str(BASE_DIR / 'static' / 'uploads')
    MEDIA_URL = '/static/uploads/'

    # Email (файловый бэкенд для разработки)
    EMAIL_BACKEND = 'file'
    EMAIL_FILE_PATH = BASE_DIR / 'media' / 'sent_emails'

    # Пагинация
    POSTS_PER_PAGE = 10
    POSTS_ON_HOME_PAGE = 5

    # Пути
    LOGIN_URL = 'users.login'
    LOGIN_REDIRECT_URL = 'shop.index'
    LOGOUT_REDIRECT_URL = 'shop.index'

    # Allowed hosts для Flask
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

    # Настройки для отправки почты
    MAIL_SERVER = 'smtp.mail.ru'          # НЕ gmail.com!
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-email@mail.ru'  # ваш реальный email
    MAIL_PASSWORD = 'your-email-password' # ваш пароль от mail.ru
    MAIL_DEFAULT_SENDER = 'your-email@mail.ru'

    # Папка для чеков
    RECEIPTS_FOLDER = os.path.join(os.path.dirname(__file__), 'receipts')

    EXPORT_DIR = 'exports'
    IMPORT_DIR = 'imports'

    # Максимальный размер загружаемых файлов (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Максимальный размер для предпросмотра (2MB)
    MAX_PREVIEW_SIZE = 2 * 1024 * 1024
