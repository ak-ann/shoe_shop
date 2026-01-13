"""
Управление профилем пользователя
"""

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash
import os
from werkzeug.utils import secure_filename

from app.database import get_cursor
from app.forms import UserEditForm
from app.models import User


def profile_view(username):
    """Профиль пользователя"""
    cur = get_cursor()

    if not cur:
        flash('Ошибка подключения к базе данных.', 'danger')
        return redirect(url_for('shop.index'))

    cur.execute('SELECT * FROM users WHERE username = %s', (username,))
    user_data = cur.fetchone()

    if not user_data:
        cur.close()
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('shop.index'))

    user = User()
    if isinstance(user_data, dict):
        user.id = user_data['id']
        user.username = user_data['username']
        user.email = user_data['email']
        user.first_name = user_data['first_name'] or ''
        user.last_name = user_data['last_name'] or ''
        user.phone = user_data['phone'] or ''
        user.address = user_data['address'] or ''
        user.avatar = user_data.get('avatar') or ''
        user.created_at = user_data['created_at']
    else:
        user.id = user_data[0] if len(user_data) > 0 else None
        user.username = user_data[1] if len(user_data) > 1 else ''
        user.email = user_data[2] if len(user_data) > 2 else ''
        user.first_name = user_data[3] if len(user_data) > 3 else ''
        user.last_name = user_data[4] if len(user_data) > 4 else ''
        user.phone = user_data[5] if len(user_data) > 5 else ''
        user.address = user_data[6] if len(user_data) > 6 else ''
        user.avatar = user_data[7] if len(user_data) > 7 else ''

    if request.method == 'POST' and current_user.is_authenticated and current_user.id == user.id:
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    import time
                    filename = secure_filename(file.filename)
                    unique_filename = f"avatar_{user.id}_{int(time.time())}_{filename}"

                    upload_folder = 'static/uploads'
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)

                    filepath = os.path.join(upload_folder, unique_filename)
                    file.save(filepath)

                    avatar_url = f"/{filepath.replace('\\', '/')}"

                    try:
                        cur.execute(
                            'UPDATE users SET avatar = %s WHERE id = %s',
                            (avatar_url, user.id)
                        )
                        cur.connection.commit()

                        user.avatar = avatar_url

                        if current_user.id == user.id:
                            current_user.avatar = avatar_url

                        flash('Аватар успешно обновлен!', 'success')
                    except Exception as e:
                        cur.connection.rollback()
                        current_app.logger.error(f'Ошибка обновления аватара: {e}')
                        flash('Ошибка при обновлении аватара', 'danger')
                else:
                    flash('Неподдерживаемый формат файла. Разрешены: PNG, JPG, JPEG, GIF', 'danger')

    cur.execute("""
        SELECT p.*, c.name AS category_name, b.name AS brand_name,
            (SELECT image_url FROM product_images WHERE product_id = p.id AND is_main = TRUE LIMIT 1) as main_image
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN shop_brand b ON p.brand_id = b.id
        WHERE p.seller_id = %s AND p.is_published = true
        ORDER BY p.created_at DESC
        LIMIT 10
    """, (user.id,))

    products = cur.fetchall()
    cur.close()

    return render_template('shop/profile.html',
                           user=user,
                           products=products,
                           is_owner=current_user.is_authenticated and current_user.id == user.id)


def edit_profile_view():
    """Редактирование профиля"""
    form = UserEditForm()

    if form.validate_on_submit():
        cur = get_cursor()

        if not cur:
            flash('Ошибка подключения к базе данных.', 'danger')
            return render_template('users/profile_edit.html', form=form)

        cur.execute('SELECT password_hash FROM users WHERE id = %s', (current_user.id,))
        user_data = cur.fetchone()

        if not user_data:
            flash('Пользователь не найден.', 'danger')
            cur.close()
            return render_template('users/profile_edit.html', form=form)

        password_hash = user_data['password_hash'] if isinstance(user_data, dict) else user_data[0]

        if not check_password_hash(password_hash, form.current_password.data):
            flash('Неверный текущий пароль.', 'danger')
            cur.close()
            return render_template('users/profile_edit.html', form=form)

        try:
            if form.username.data != current_user.username:
                cur.execute(
                    'SELECT id FROM users WHERE username = %s AND id != %s',
                    (form.username.data, current_user.id)
                )
                existing_user = cur.fetchone()
                if existing_user:
                    flash('Это имя пользователя уже занято.', 'danger')
                    cur.close()
                    return render_template('users/profile_edit.html', form=form)
            
            if form.email.data != current_user.email:
                cur.execute(
                    'SELECT id FROM users WHERE email = %s AND id != %s',
                    (form.email.data, current_user.id)
                )
                existing_email = cur.fetchone()
                if existing_email:
                    flash('Этот email уже зарегистрирован.', 'danger')
                    cur.close()
                    return render_template('users/profile_edit.html', form=form)

            cur.execute("""
                UPDATE users SET
                first_name = %s, last_name = %s, username = %s, email = %s,
                phone = %s, address = %s
                WHERE id = %s
            """, (
                form.first_name.data or None,
                form.last_name.data or None,
                form.username.data,
                form.email.data,
                form.phone.data or None,
                form.address.data or None,
                current_user.id
            ))

            if form.new_password.data and form.new_password.data.strip():
                password_hash = generate_password_hash(form.new_password.data)
                cur.execute(
                    'UPDATE users SET password_hash = %s WHERE id = %s',
                    (password_hash, current_user.id)
                )

            cur.connection.commit()
            cur.close()

            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.phone = form.phone.data
            current_user.address = form.address.data

            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('users.profile', username=current_user.username))
            
        except Exception as e:
            if cur.connection:
                cur.connection.rollback()
            cur.close()
            current_app.logger.error(f'Ошибка обновления профиля: {e}')
            flash('Произошла ошибка при обновлении профиля', 'danger')
            return render_template('users/profile_edit.html', form=form)

    if request.method == 'GET':
        form.first_name.data = current_user.first_name or ''
        form.last_name.data = current_user.last_name or ''
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.phone.data = current_user.phone or ''
        form.address.data = current_user.address or ''

    return render_template('users/profile_edit.html', form=form)
