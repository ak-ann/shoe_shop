"""
Сервис отправки email
"""

from flask_mail import Message
from flask import current_app
import traceback


def send_receipt_email_async(app, email_data):
    """Асинхронная отправка email"""
    with app.app_context():
        try:
            mail = current_app.extensions['mail']

            msg = Message(
                subject=f"Заказ №{email_data['order_number']} — Luxury Shoes",
                recipients=[email_data['customer_email']],
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )

            msg.charset = 'utf-8'

            msg.body = f"""
Заказ №{email_data['order_number']} успешно оформлен!

Дата: {email_data['order_date']}
Способ оплаты: {email_data['payment_method']}
Адрес доставки: {email_data['delivery_address']}

Состав заказа:
"""

            for item in email_data['items']:
                msg.body += f"- {item['product_name']}"
                if item.get('size'):
                    msg.body += f" (Размер: {item['size']})"
                msg.body += f": {item['quantity']} × {item['price']} = {item['subtotal']} руб.\n"

            msg.body += f"\nИТОГО: {email_data['total_amount']} руб.\n\nСпасибо за покупку!"

            mail.send(msg)
            current_app.logger.info(f"Email sent to {email_data['customer_email']}")

        except Exception as e:
            current_app.logger.error(f"Error sending email: {e}")
            traceback.print_exc()