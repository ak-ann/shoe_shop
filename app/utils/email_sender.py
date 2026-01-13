import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template, current_app


def generate_verification_token(length=32):
    """Генерация токена для подтверждения email"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_random_password(length=12):
    """Генерация случайного пароля"""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    if not any(c.isdigit() for c in password):
        password = password[:-1] + secrets.choice(string.digits)
    if not any(c in '!@#$%^&*' for c in password):
        password = password[:-1] + secrets.choice('!@#$%^&*')
    return password


def send_email(app, to_email, subject, html_content):
    """Отправка email через SMTP"""
    try:
        smtp_server = app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = app.config.get('MAIL_PORT', 587)
        smtp_username = app.config.get('MAIL_USERNAME')
        smtp_password = app.config.get('MAIL_PASSWORD')
        from_email = app.config.get('MAIL_DEFAULT_SENDER', smtp_username)

        if not all([smtp_server, smtp_username, smtp_password]):
            print("ПРЕДУПРЕЖДЕНИЕ: Настройки почты не заданы. Email не будет отправлен.")
            print(f"Настройки: SERVER={smtp_server}, USER={smtp_username}, PASS={'*' * len(smtp_password) if smtp_password else None}")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        print(f"✓ Email отправлен на {to_email}")
        return True
    except Exception as e:
        print(f"✗ Ошибка отправки email на {to_email}: {e}")
        return False


def send_verification_email(app, user_id, username, email, token):
    """Отправка email для подтверждения регистрации - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        print(f"\n НАЧАЛО ОТПРАВКИ EMAIL ВЕРИФИКАЦИИ")
        print(f"   Приложение: {app}")
        print(f"   Email: {email}")
        print(f"   Имя: {username}")
        print(f"   Токен: {token}")

        base_url = app.config.get('BASE_URL', 'http://localhost:5000')
        confirm_url = f"{base_url}/users/verify-email/{token}"

        subject = f"Подтверждение регистрации в {app.config.get('APP_NAME', 'Shoe Shop')}"

        print(f"\n Ссылка для подтверждения: {confirm_url}")
        print(f" Тема письма: {subject}")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;">
                <h1>Добро пожаловать, {username}!</h1>
            </div>

            <div style="padding: 30px; background-color: #f8f9fa; border-radius: 0 0 5px 5px;">
                <p>Спасибо за регистрацию в <strong>Shoe Shop</strong>!</p>

                <p>Для завершения регистрации и активации вашего аккаунта, пожалуйста, подтвердите ваш email адрес, нажав на кнопку ниже:</p>
    
                <div style="text-align: center;">
                    <a href="{confirm_url}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Подтвердить Email
                    </a>
                </div>

                <p>Если кнопка не работает, скопируйте и вставьте ссылку в браузер:</p>
                <p style="word-break: break-all;">
                    <a href="{confirm_url}">{confirm_url}</a>
                </p>

                <p><strong>Важно:</strong> Без подтверждения email вы не сможете войти в свой аккаунт.</p>
            </div>
        </body>
        </html>
        """

        smtp_server = app.config.get('MAIL_SERVER', '')
        smtp_port = app.config.get('MAIL_PORT', 587)
        smtp_username = app.config.get('MAIL_USERNAME', '')
        smtp_password = app.config.get('MAIL_PASSWORD', '')

        print(f"\n Параметры SMTP:")
        print(f"   Сервер: {smtp_server}")
        print(f"   Порт: {smtp_port}")
        print(f"   Логин: {smtp_username}")
        print(f"   Пароль: {'*' * len(smtp_password) if smtp_password else 'НЕТ'}")

        if not smtp_username or not smtp_password:
            print("⚠️ Настройки email не заданы. Использую тестовый режим.")

            print(f"\n ДЛЯ ТЕСТИРОВАНИЯ:")
            print(f"   Ссылка: {confirm_url}")
            print(f"   Команда для проверки: curl {confirm_url}")

            from datetime import datetime
            with open('verification_links.log', 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now()} | {username} | {email} | {confirm_url}\n")

            return True

        print(f"\n Пытаюсь отправить реальный email...")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_username
        msg['To'] = email

        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            print("Подключение установлено")

            server.login(smtp_username, smtp_password)
            print("Авторизация успешна")

            server.send_message(msg)
            print(f"Email отправлен на {email}")

        return True

    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_password_reset_email(app, username, email, new_password):
    """Отправка email с новым паролем"""
    subject = f"Восстановление пароля в {app.config.get('APP_NAME', 'Shoe Shop')}"

    html_content = render_template(
        'email/password_reset.html',
        username=username,
        new_password=new_password,
        app_name=app.config.get('APP_NAME', 'Shoe Shop')
    )

    return send_email(app, email, subject, html_content)


def send_password_reset_token_email(app, username, email, token):
    """Отправка email со ссылкой для сброса пароля"""
    base_url = app.config.get('BASE_URL', 'http://localhost:5000')
    reset_url = f"{base_url}/users/reset-password/{token}"

    subject = f"Сброс пароля в {app.config.get('APP_NAME', 'Shoe Shop')}"

    html_content = render_template(
        'email/password_reset_token.html',
        username=username,
        reset_url=reset_url,
        app_name=app.config.get('APP_NAME', 'Shoe Shop')
    )

    return send_email(app, email, subject, html_content)
