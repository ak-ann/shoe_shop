from flask import g, current_app
import psycopg2
from psycopg2.extras import DictCursor


def get_db():
    """Получить соединение с базой данных"""
    if 'db' not in g:
        g.db = psycopg2.connect(
            host=current_app.config['DB_HOST'],
            database=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            port=current_app.config['DB_PORT']
        )
    return g.db


def get_cursor():
    """Получить курсор для выполнения запросов"""
    return get_db().cursor(cursor_factory=DictCursor)


def close_db(e=None):
    """Закрыть соединение с базой"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def get_db_connection():
    """Создать новое соединение с БД (для использования вне запроса)"""
    return psycopg2.connect(
        host=current_app.config['DB_HOST'],
        database=current_app.config['DB_NAME'],
        user=current_app.config['DB_USER'],
        password=current_app.config['DB_PASSWORD'],
        port=current_app.config['DB_PORT']
    )


def safe_fetchall(cursor, sql, params=None):
    """Безопасное выполнение запроса"""
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchall()
    except Exception as e:
        print(f"SQL Error: {e}")
        return []


def safe_fetchone(cursor, sql, params=None):
    """Безопасное выполнение запроса"""
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchone()
    except Exception as e:
        print(f"SQL Error: {e}")
        return None
