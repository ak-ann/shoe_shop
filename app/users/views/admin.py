from flask import render_template, redirect, url_for, flash, request, g, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from app.models import User
from app.database import get_cursor


@login_required
def admin_panel_view():
    """Главная админ-панели"""
    if not current_user.is_staff:
        flash('Доступ только для администраторов', 'danger')
        return redirect(url_for('shop.index'))

    cur = get_cursor()

    try:
        stats = {}

        def safe_count(sql):
            cur.execute(sql)
            result = cur.fetchone()
            if result and result.get('count') is not None:
                return result['count']
            return 0

        stats['users'] = safe_count('SELECT COUNT(*) as count FROM users')
        stats['products'] = safe_count('SELECT COUNT(*) as count FROM products')
        stats['categories'] = safe_count('SELECT COUNT(*) as count FROM categories')
        stats['brands'] = safe_count('SELECT COUNT(*) as count FROM shop_brand')
        stats['reviews'] = safe_count('SELECT COUNT(*) as count FROM reviews')

        cur.execute('SELECT * FROM users ORDER BY created_at DESC LIMIT 5')
        last_users = cur.fetchall()

        cur.execute('SELECT * FROM products ORDER BY created_at DESC LIMIT 5')
        last_products = cur.fetchall()

        return render_template('admin/dashboard.html',
                               stats=stats,
                               last_users=last_users,
                               last_products=last_products)

    except Exception as e:
        current_app.logger.error(f'Ошибка загрузки админ-панели: {e}')
        flash('Ошибка загрузки данных', 'danger')
        return render_template('admin/dashboard.html',
                               stats={},
                               last_users=[],
                               last_products=[])

    finally:
        cur.close()


@login_required
def admin_users_view():
    """Управление пользователями"""
    if not current_user.is_staff:
        flash('Доступ только для администраторов', 'danger')
        return redirect(url_for('shop.index'))

    cur = get_cursor()

    try:
        cur.execute('SELECT * FROM users ORDER BY created_at DESC')
        users = cur.fetchall()
        return render_template('admin/users.html', users=users)

    except Exception as e:
        current_app.logger.error(f'Ошибка загрузки пользователей: {e}')
        flash('Ошибка загрузки данных', 'danger')
        return render_template('admin/users.html', users=[])

    finally:
        cur.close()


@login_required
def edit_user_view(user_id):
    """Редактирование пользователя (админ)"""
    if not current_user.is_staff:
        flash('Доступ только для администраторов', 'danger')
        return redirect(url_for('shop.index'))

    cur = get_cursor()

    try:
        cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user_data = cur.fetchone()

        if not user_data:
            flash('Пользователь не найден.', 'danger')
            return redirect(url_for('admin.users'))

        if user_id == current_user.id:
            flash('Для редактирования своего профиля используйте личный кабинет.', 'warning')
            return redirect(url_for('users.profile', username=current_user.username))

        if request.method == 'POST':
            username = request.form.get('username', user_data['username'])
            email = request.form.get('email', user_data['email'])
            first_name = request.form.get('first_name', user_data['first_name'] or '')
            last_name = request.form.get('last_name', user_data['last_name'] or '')
            phone = request.form.get('phone', user_data['phone'] or '')
            address = request.form.get('address', user_data['address'] or '')
            is_staff = 'is_staff' in request.form

            cur.execute("""
                UPDATE users SET
                username = %s, email = %s, first_name = %s, last_name = %s,
                phone = %s, address = %s, is_admin = %s
                WHERE id = %s
            """, (
                username, email, first_name, last_name,
                phone, address, is_staff, user_id
            ))

            new_password = request.form.get('new_password')
            if new_password and new_password.strip():
                password_hash = generate_password_hash(new_password)
                cur.execute('UPDATE users SET password_hash = %s WHERE id = %s',
                            (password_hash, user_id))

            g.db.commit()
            flash('Данные пользователя обновлены.', 'success')
            return redirect(url_for('admin.users'))

        user = User.from_dict(user_data)

        return render_template('admin/user_edit.html', user=user)

    except Exception as e:
        current_app.logger.error(f'Ошибка редактирования пользователя: {e}')
        flash('Ошибка обработки запроса', 'danger')
        return redirect(url_for('admin.users'))

    finally:
        cur.close()


@login_required
def delete_user_view(user_id):
    """Удаление пользователя (админ)"""
    if not current_user.is_staff:
        flash('Доступ только для администраторов', 'danger')
        return redirect(url_for('shop.index'))

    if user_id == current_user.id:
        flash('Нельзя удалить свой собственный аккаунт', 'danger')
        return redirect(url_for('admin.users'))

    cur = get_cursor()

    try:
        cur.execute('SELECT COUNT(*) as count FROM products WHERE seller_id = %s', (user_id,))
        result = cur.fetchone()

        if result and result['count'] > 0:
            product_count = result['count']
            flash(f'Нельзя удалить пользователя, у которого есть товары ({product_count} шт.)', 'danger')
            return redirect(url_for('admin.users'))

        cur.execute('SELECT COUNT(*) as count FROM reviews WHERE user_id = %s', (user_id,))
        result = cur.fetchone()

        if result and result['count'] > 0:
            cur.execute('DELETE FROM reviews WHERE user_id = %s', (user_id,))

        cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
        g.db.commit()

        flash('Пользователь успешно удален', 'success')

    except Exception as e:
        current_app.logger.error(f'Ошибка удаления пользователя: {e}')
        flash('Ошибка при удалении пользователя', 'danger')

    finally:
        cur.close()

    return redirect(url_for('admin.users'))
