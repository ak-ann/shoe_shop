"""
Управление пользователями
"""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from psycopg2 import Error

from ..decorators import admin_required
from app.database import get_cursor


def format_date(date_obj):
    """Форматирование даты для отображения"""
    if not date_obj:
        return ""
    return date_obj.strftime('%d.%m.%Y %H:%M')


@login_required
@admin_required
def users():
    """Список пользователей"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    username,
                    email,
                    created_at,
                    is_admin,
                    first_name,
                    last_name,
                    phone,
                    address,
                    (SELECT COUNT(*) FROM orders WHERE user_id = users.id) as order_count
                FROM users
                ORDER BY created_at DESC
            """)

            users_data = cur.fetchall()
            formatted_users = _format_users_data(users_data)

            return render_template('admin/users.html', users=formatted_users)

    except Error as e:
        print(f"SQL Error: {e}")  # Для отладки
        flash('Ошибка при загрузке пользователей', 'danger')
        return render_template('admin/users.html', users=[])


def _format_users_data(users_data):
    """Форматировать данные пользователей"""
    formatted = []
    for user in users_data:
        formatted.append({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': format_date(user['created_at']),
            'is_admin': user['is_admin'],
            'first_name': user['first_name'] or '',
            'last_name': user['last_name'] or '',
            'phone': user['phone'] or '',
            'address': user['address'] or '',
            'order_count': user['order_count']
        })
    return formatted


@login_required
@admin_required
def edit_user(user_id):
    """Редактирование пользователя"""
    if request.method == 'POST':
        return _handle_user_update(user_id)

    try:
        with get_cursor() as cur:
            user = _get_user_by_id(cur, user_id)
            if not user:
                flash('Пользователь не найден', 'danger')
                return redirect(url_for('admin.users'))

            return render_template('admin/user_edit.html', user=user)

    except Error:
        flash('Ошибка при загрузке пользователя', 'danger')
        return redirect(url_for('admin.users'))


def _handle_user_update(user_id):
    """Обработать обновление пользователя"""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    is_admin = 'is_admin' in request.form
    new_password = request.form.get('new_password', '').strip()

    if not username:
        flash('Имя пользователя обязательно', 'danger')
        return redirect(url_for('admin.edit_user', user_id=user_id))

    if not email:
        flash('Email обязателен', 'danger')
        return redirect(url_for('admin.edit_user', user_id=user_id))

    try:
        with get_cursor() as cur:
            cur.execute("""
                UPDATE users
                SET username = %s, email = %s, first_name = %s, last_name = %s,
                    phone = %s, address = %s, is_admin = %s
                WHERE id = %s
            """, (username, email, first_name, last_name, phone, address, is_admin, user_id))

            if new_password:
                if len(new_password) < 6:
                    flash('Пароль должен содержать минимум 6 символов', 'danger')
                    return redirect(url_for('admin.edit_user', user_id=user_id))

                password_hash = generate_password_hash(new_password)
                cur.execute("""
                    UPDATE users
                    SET password_hash = %s
                    WHERE id = %s
                """, (password_hash, user_id))

            cur.connection.commit()
            flash('Пользователь успешно обновлен!', 'success')
            return redirect(url_for('admin.users'))

    except Error:
        flash('Ошибка при обновлении пользователя', 'danger')
        return redirect(url_for('admin.edit_user', user_id=user_id))


def _get_user_by_id(cur, user_id):
    """Получить пользователя по ID"""
    cur.execute("""
        SELECT
            id,
            username,
            email,
            is_admin,
            first_name,
            last_name,
            phone,
            address,
            created_at
        FROM users
        WHERE id = %s
    """, (user_id,))

    user_row = cur.fetchone()
    if not user_row:
        return None

    return dict(user_row)


@login_required
@admin_required
def delete_user(user_id):
    """Удаление пользователя"""
    try:
        if user_id == current_user.id:
            flash('Нельзя удалить свой собственный аккаунт!', 'danger')
            return redirect(url_for('admin.users'))

        with get_cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM products WHERE seller_id = %s",
                (user_id,)
            )
            result = cur.fetchone()

            if result and result['cnt'] > 0:
                flash('Нельзя удалить пользователя с товарами', 'danger')
                return redirect(url_for('admin.users'))

            cur.execute("DELETE FROM reviews WHERE user_id = %s", (user_id,))
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            cur.connection.commit()

            flash('Пользователь успешно удален!', 'success')
            return redirect(url_for('admin.users'))

    except Error:
        flash('Ошибка при удалении пользователя', 'danger')
        return redirect(url_for('admin.users'))
