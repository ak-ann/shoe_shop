from flask import render_template, redirect, url_for, flash, request, g, current_app
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse
from werkzeug.security import check_password_hash, generate_password_hash
import secrets

from app.forms import RegistrationForm, LoginForm
from app.database import get_cursor
from app.models import User


def register_view():
    """Регистрация пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        cur = get_cursor()

        cur.execute(
            'SELECT id FROM users WHERE username = %s OR email = %s',
            (form.username.data, form.email.data)
        )
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            flash('Пользователь с таким именем или email уже существует.', 'danger')
            return render_template('users/register.html', form=form)

        verification_token = secrets.token_urlsafe(32)

        password_hash = generate_password_hash(form.password.data)
        cur.execute("""
            INSERT INTO users (
                username, email, password_hash, first_name, last_name,
                email_verified, verification_token, verification_sent_at, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
        """, (
            form.username.data,
            form.email.data,
            password_hash,
            '',
            '',
            False,
            verification_token,
        ))

        result = cur.fetchone()
        if result:
            user_id = result['id']

            try:
                from app.utils.email_sender import send_verification_email
                app = current_app._get_current_object()

                success = send_verification_email(
                    app,
                    form.email.data,
                    form.username.data,
                    verification_token
                )

                if success:
                    flash('Регистрация прошла успешно! Проверьте ваш email для подтверждения.', 'success')
                else:
                    flash('Регистрация прошла успешно, но не удалось отправить email для подтверждения.', 'warning')
                    flash('Свяжитесь с администратором для активации аккаунта.', 'warning')

            except Exception as e:
                current_app.logger.error(f'Ошибка отправки email: {e}')
                flash('Регистрация прошла успешно, но не удалось отправить email для подтверждения.', 'warning')
                flash('Свяжитесь с администратором для активации аккаунта.', 'warning')

            g.db.commit()
            cur.close()
            return redirect(url_for('users.login'))

    return render_template('users/register.html', form=form)


def verify_email_view(token):
    """Подтверждение email"""
    cur = get_cursor()

    cur.execute("""
        SELECT id, username, email, verification_sent_at
        FROM users
        WHERE verification_token = %s AND email_verified = FALSE
    """, (token,))

    user_data = cur.fetchone()

    if not user_data:
        cur.close()
        flash('Неверная или устаревшая ссылка подтверждения.', 'danger')
        return redirect(url_for('shop.index'))

    user_id = user_data['id']
    username = user_data['username']
    token_sent_at = user_data['verification_sent_at']

    from datetime import datetime, timedelta
    if token_sent_at:
        expiration_time = token_sent_at + timedelta(hours=24)
        if datetime.utcnow() > expiration_time:
            cur.close()
            flash('Срок действия ссылки истек. Запросите новую.', 'danger')
            return redirect(url_for('users.resend_verification'))

    cur.execute("""
        UPDATE users
        SET email_verified = TRUE,
            verification_token = NULL,
            verification_sent_at = NULL
        WHERE id = %s
    """, (user_id,))

    g.db.commit()
    cur.close()

    flash(f'Email успешно подтвержден, {username}! Теперь вы можете войти.', 'success')
    return redirect(url_for('users.login'))


def resend_verification_view():
    """Повторная отправка верификации"""
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))

    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('Введите email', 'danger')
            return render_template('users/resend_verification.html')

        cur = get_cursor()
        cur.execute("""
            SELECT id, username, email, email_verified
            FROM users
            WHERE email = %s
        """, (email,))

        user_data = cur.fetchone()
        cur.close()

        if not user_data:
            flash('Пользователь с таким email не найден', 'danger')
            return render_template('users/resend_verification.html')

        email_verified = user_data.get('email_verified', False)
        if email_verified:
            flash('Ваш email уже подтвержден!', 'info')
            return redirect(url_for('users.login'))

        new_token = secrets.token_urlsafe(32)

        cur = get_cursor()
        cur.execute("""
            UPDATE users
            SET verification_token = %s,
                verification_sent_at = NOW()
            WHERE email = %s
        """, (new_token, email))

        g.db.commit()
        cur.close()

        user_id = user_data['id']
        username = user_data['username']

        try:
            from app.utils.email_sender import send_verification_email
            app = current_app._get_current_object()

            success = send_verification_email(
                app=app,
                user_id=user_id,
                username=username,
                email=email,
                token=new_token
            )

            if success:
                flash('Новая ссылка для подтверждения отправлена на ваш email!', 'success')
            else:
                flash('Ссылка обновлена, но не удалось отправить email', 'warning')

        except ImportError:
            flash('Модуль отправки email не найден', 'danger')
        except Exception as e:
            current_app.logger.error(f'Ошибка отправки email: {e}')
            flash('Ссылка обновлена, но возникла ошибка при отправке email', 'warning')

        return redirect(url_for('users.login'))

    return render_template('users/resend_verification.html')


def login_view():
    """Вход в систему"""
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))

    form = LoginForm()

    if form.validate_on_submit():
        cur = get_cursor()

        cur.execute(
            'SELECT * FROM users WHERE username = %s',
            (form.username.data,)
        )
        user_data = cur.fetchone()
        cur.close()

        if user_data:
            if check_password_hash(user_data['password_hash'], form.password.data):

                email_verified = user_data.get('email_verified', False)

                if not email_verified:
                    flash('Пожалуйста, подтвердите ваш email перед входом.', 'warning')
                    flash('Проверьте вашу почту или запросите повторную отправку ссылки.', 'info')
                    return redirect(url_for('users.resend_verification'))

                user = User.from_dict(user_data)
                login_user(user, remember=True)

                next_page = request.args.get('next')
                if next_page:
                    next_url = urlparse(next_page)
                    if next_url.netloc == '':
                        return redirect(next_page)

                flash(f'Добро пожаловать, {user.username}!', 'success')
                return redirect(url_for('shop.index'))

        flash('Неверное имя пользователя или пароль.', 'danger')

    return render_template('users/login.html', form=form)


def logout_view():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('shop.index'))
