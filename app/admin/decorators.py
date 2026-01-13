from functools import wraps
from flask import flash, redirect, url_for, current_app
from flask_login import current_user


def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff:
            flash('Доступ только для администраторов', 'danger')
            return redirect(url_for('pages.home'))
        return f(*args, **kwargs)
    return decorated_function
