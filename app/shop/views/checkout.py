"""
Представления для оформления заказа
"""
from flask import render_template, request, jsonify, send_file, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
import os
from datetime import datetime

from app.database import get_cursor


def checkout():
    """Страница оформления заказа"""
    try:
        if not current_user.is_authenticated:
            flash('Пожалуйста, войдите в систему для оформления заказа', 'warning')
            return redirect(url_for('users.login'))

        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    ci.id as cart_item_id,
                    ci.product_id,
                    ci.size,
                    ci.quantity,
                    p.name as product_name,
                    p.price,
                    p.description,
                    pi.image_url as product_image,
                    (SELECT name FROM categories WHERE id = p.category_id) as category_name,
                    (SELECT name FROM shop_brand WHERE id = p.brand_id) as brand_name
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_main = TRUE
                WHERE ci.user_id = %s
            """, (current_user.id,))

            cart_items = cur.fetchall()

        if len(cart_items) == 0:
            flash('Ваша корзина пуста', 'warning')
            return redirect(url_for('shop.cart_route'))

        total_amount = 0
        for item in cart_items:
            price = float(item['price'] or 0)
            quantity = item['quantity']
            total_amount += price * quantity

        user_data = {
            'full_name': f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.username or '',
            'email': current_user.email or '',
            'phone': getattr(current_user, 'phone', ''),
            'address': getattr(current_user, 'address', '')
        }

        current_year = datetime.now().year

        return render_template('shop/checkout.html',
                               cart_items=cart_items,
                               total=total_amount,
                               user=user_data,
                               current_year=current_year)

    except Exception:
        flash('Ошибка при загрузке страницы оформления заказа', 'error')
        return redirect(url_for('shop.cart_route'))


def api_checkout():
    """API для обработки заказа"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Войдите в систему'}), 401

        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Нет данных'}), 400

        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    ci.id as cart_item_id,
                    ci.product_id,
                    ci.size,
                    ci.quantity,
                    p.name as product_name,
                    p.price,
                    p.description,
                    pi.image_url as product_image
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_main = TRUE
                WHERE ci.user_id = %s
            """, (current_user.id,))

            cart_items = cur.fetchall()

            if not cart_items:
                return jsonify({'success': False, 'message': 'Корзина пуста'}), 400

            order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            order_date = datetime.now()

            total_amount = 0
            order_items = []

            for item in cart_items:
                price = float(item['price'] or 0)
                quantity = item['quantity']
                subtotal = price * quantity
                total_amount += subtotal

                order_items.append({
                    'product_id': item['product_id'],
                    'product_name': item['product_name'],
                    'size': item['size'],
                    'quantity': quantity,
                    'price': price,
                    'subtotal': subtotal,
                    'image_url': item['product_image']
                })

            try:
                cur.execute("""
                    INSERT INTO orders (
                        user_id, order_number, total_amount, status,
                        shipping_address, payment_method, payment_status, notes,
                        billing_address, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    current_user.id,
                    order_number,
                    total_amount,
                    'processing',
                    data.get('address', ''),
                    data.get('paymentMethod', 'cash'),
                    'pending',
                    data.get('comment', ''),
                    data.get('address', ''),
                    order_date
                ))

                result = cur.fetchone()
                order_id = result['id'] if result else 0

            except Exception:
                cur.execute("""
                    INSERT INTO orders (user_id, order_number, total_amount)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (current_user.id, order_number, total_amount))

                result = cur.fetchone()
                order_id = result['id'] if result else 0

            for item in order_items:
                try:
                    cur.execute("""
                        INSERT INTO order_items (order_id, product_id, size, quantity, price)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        order_id,
                        item['product_id'],
                        item['size'],
                        item['quantity'],
                        item['price']
                    ))
                except Exception:
                    pass

                cur.execute("""
                    UPDATE products
                    SET stock = stock - %s
                    WHERE id = %s AND stock >= %s
                """, (item['quantity'], item['product_id'], item['quantity']))

            cur.execute("DELETE FROM cart_items WHERE user_id = %s", (current_user.id,))

            cur.connection.commit()

        receipts_dir = os.path.join(current_app.root_path, 'static', 'receipts')
        os.makedirs(receipts_dir, exist_ok=True)

        receipt_content = f"""
==================================
            LUXURY SHOES
==================================
            ЧЕК О ПРОДАЖЕ
==================================
Дата: {order_date.strftime('%d.%m.%Y %H:%M:%S')}
Номер заказа: {order_number}
----------------------------------
КЛИЕНТ:
Имя: {data.get('fullName', '')}
Телефон: {data.get('phone', '')}
Email: {data.get('email', '')}
Адрес: {data.get('address', '')}
Оплата: {data.get('paymentMethod', 'Наличные')}
----------------------------------
ТОВАРЫ:
"""

        for item in order_items:
            receipt_content += f"\n• {item['product_name']}"
            if item['size']:
                receipt_content += f" (Размер: {item['size']})"
            receipt_content += f"\n  {item['quantity']} шт. × {item['price']:.2f} руб. = {item['subtotal']:.2f} руб."

        receipt_content += f"""
----------------------------------
ИТОГО: {total_amount:.2f} руб.
==================================
Спасибо за покупку!
==================================
"""

        filename = f"receipt_{order_number}.txt"
        filepath = os.path.join(receipts_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(receipt_content)

        return jsonify({
            'success': True,
            'message': 'Заказ оформлен успешно!',
            'order_number': order_number,
            'order_id': order_id,
            'total_amount': total_amount,
            'receipt_url': f'/static/receipts/{filename}'
        })

    except Exception:
        return jsonify({
            'success': False,
            'message': 'Ошибка при оформлении заказа'
        }), 500


@login_required
def order_success(order_number):
    """Страница успешного оформления заказа"""
    return render_template('shop/order_success.html',
                           order_number=order_number,
                           order_date=datetime.now().strftime('%d.%m.%Y %H:%M'))


@login_required
def download_receipt(order_number):
    """Скачивание чека"""
    try:
        filename = f"receipt_{order_number}.txt"
        filepath = os.path.join(current_app.root_path, 'static', 'receipts', filename)

        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='text/plain'
            )
        else:
            flash('Чек не найден', 'error')
            return redirect(url_for('shop.cart_route'))

    except Exception:
        flash('Ошибка при скачивании чека', 'error')
        return redirect(url_for('shop.cart_route'))


@login_required
def api_get_cart():
    """API для получения содержимого корзины"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT
                    ci.id as cart_item_id,
                    ci.product_id,
                    ci.size,
                    ci.quantity,
                    p.name,
                    p.price,
                    p.stock,
                    pi.image_url,
                    (SELECT name FROM categories WHERE id = p.category_id) as category_name,
                    (SELECT name FROM shop_brand WHERE id = p.brand_id) as brand_name
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_main = TRUE
                WHERE ci.user_id = %s
            """, (current_user.id,))

            items = cur.fetchall()

            cart_items = []
            for item in items:
                cart_items.append({
                    'cart_item_id': item['cart_item_id'],
                    'product_id': item['product_id'],
                    'name': item['name'],
                    'size': item['size'],
                    'quantity': item['quantity'],
                    'price': float(item['price'] or 0),
                    'stock': item['stock'],
                    'image_url': item['image_url'],
                    'category_name': item['category_name'],
                    'brand_name': item['brand_name']
                })

            return jsonify({
                'success': True,
                'items': cart_items,
                'count': len(cart_items)
            })

    except Exception:
        return jsonify({'success': False, 'message': 'Ошибка при загрузке корзины'}), 500
