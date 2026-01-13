"""
Представления для работы с корзиной
"""
from flask import render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import current_user
import os

from app.database import get_cursor


def get_cart_count():
    """Получить количество товаров в корзине"""
    cart_count = 0

    if current_user.is_authenticated:
        with get_cursor() as cur:
            sql = "SELECT SUM(quantity) as total FROM cart_items WHERE user_id = %s"
            cur.execute(sql, (current_user.id,))
            result = cur.fetchone()
            cart_count = result['total'] if result and result['total'] else 0
    elif 'cart' in session:
        cart_count = sum(session['cart'].values())

    return cart_count


def get_cart_items(user_id=None):
    """Получить товары в корзине для указанного пользователя"""
    try:
        if user_id is None:
            if not current_user.is_authenticated:
                return []
            user_id = current_user.id

        with get_cursor() as cur:
            query = """
            SELECT
                ci.id as cart_item_id,
                ci.user_id,
                ci.product_id,
                ci.size,
                ci.quantity,
                ci.added_at,
                p.name,
                p.price,
                p.description,
                p.stock,
                p.is_published,
                (p.stock > 0) as in_stock,
                c.name as category_name,
                sb.name as brand_name,
                (SELECT image_url FROM product_images WHERE product_id = p.id AND is_main = TRUE LIMIT 1) as main_image
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN shop_brand sb ON p.brand_id = sb.id
            WHERE ci.user_id = %s
            ORDER BY ci.added_at DESC
            """

            cur.execute(query, (user_id,))
            return cur.fetchall()

    except Exception:
        return []


def check_stock_availability(product_id, size, quantity):
    """Проверить доступность товара на складе"""
    try:
        with get_cursor() as cur:
            if size:
                cur.execute("""
                    SELECT ps.quantity as size_stock, p.stock as total_stock
                    FROM product_sizes ps
                    JOIN products p ON ps.product_id = p.id
                    WHERE ps.product_id = %s AND ps.size = %s
                """, (product_id, size))

                result = cur.fetchone()

                if not result:
                    return False, "Размер недоступен"

                if quantity > result['size_stock']:
                    return False, f"Для размера {size} доступно только {result['size_stock']} шт."

                return True, None
            else:
                cur.execute("""
                    SELECT stock FROM products
                    WHERE id = %s AND is_published = TRUE
                """, (product_id,))

                result = cur.fetchone()

                if not result:
                    return False, "Товар не найден"

                if quantity > result['stock']:
                    return False, f"Доступно только {result['stock']} шт."

                return True, None

    except Exception:
        return False, "Ошибка проверки наличия"


def cart():
    """Страница корзины"""
    try:
        if not current_user.is_authenticated:
            flash('Пожалуйста, войдите в систему', 'error')
            return redirect('/users/login')

        user_id = current_user.id

        with get_cursor() as cur:
            query = """
            SELECT
                ci.id as cart_item_id,
                ci.user_id,
                ci.product_id,
                ci.size,
                ci.quantity,
                ci.added_at,
                p.name,
                p.price,
                p.description,
                p.stock,
                p.is_published,
                (p.stock > 0) as in_stock,
                c.name as category_name,
                sb.name as brand_name,
                (SELECT image_url FROM product_images WHERE product_id = p.id AND is_main = TRUE LIMIT 1) as main_image
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN shop_brand sb ON p.brand_id = sb.id
            WHERE ci.user_id = %s
            ORDER BY ci.added_at DESC
            """

            cur.execute(query, (user_id,))
            items = cur.fetchall()

            cart_items = []
            total_quantity = 0
            total_price = 0.0

            for item in items:
                quantity = item['quantity']
                price = float(item['price'] or 0)
                item_total = price * quantity

                total_quantity += quantity
                total_price += item_total

                image = item['main_image']
                if image:
                    if image.startswith(('http://', 'https://', '/')):
                        pass
                    elif image.startswith('uploads/'):
                        image = f"/static/{image}"
                    elif image.startswith('media/'):
                        image = f"/static/media/{image}"
                    else:
                        if os.path.exists(f"static/uploads/products/{image}"):
                            image = f"/static/uploads/products/{image}"
                        elif os.path.exists(f"static/media/{image}"):
                            image = f"/static/media/{image}"
                        else:
                            image = "/static/images/no-image.png"
                else:
                    image = "/static/images/no-image.png"

                size_available = True
                if item['size']:
                    available, _ = check_stock_availability(
                        item['product_id'],
                        item['size'],
                        quantity
                    )
                    size_available = available

                cart_items.append({
                    'cart_item_id': item['cart_item_id'],
                    'product_id': item['product_id'],
                    'size': item['size'],
                    'quantity': quantity,
                    'added_at': item['added_at'],
                    'name': item['name'],
                    'price': price,
                    'description': item['description'],
                    'stock': item['stock'],
                    'in_stock': item['in_stock'] and size_available,
                    'is_published': item['is_published'],
                    'image': image,
                    'category_name': item['category_name'],
                    'brand_name': item['brand_name'],
                    'item_total': item_total,
                    'has_discount': False
                })

            return render_template(
                'shop/cart.html',
                cart_items=cart_items,
                total_quantity=total_quantity,
                total_price=round(total_price, 2),
                total_discount=0,
                total_without_discount=round(total_price, 2)
            )

    except Exception:
        flash('Произошла ошибка при загрузке корзины', 'error')
        return redirect('/')


def update_cart_quantity(item_id):
    quantity = request.form.get('quantity', type=int)

    if not quantity or quantity < 1:
        flash('Неверное количество', 'error')
        return redirect(url_for('shop.cart_route'))

    if quantity > 10:
        flash('Максимальное количество — 10 шт.', 'error')
        return redirect(url_for('shop.cart_route'))

    try:
        cursor = get_cursor()
        cursor.execute("""
            UPDATE cart_items
            SET quantity = %s
            WHERE id = %s AND user_id = %s
            RETURNING quantity
        """, (quantity, item_id, current_user.id))

        updated = cursor.fetchone()
        cursor.connection.commit()
        cursor.close()

        if updated:
            flash('Количество обновлено', 'success')
        else:
            flash('Товар не найден в корзине', 'error')

    except Exception as e:
        print(f"Error updating cart quantity: {e}")
        flash('Ошибка обновления количества', 'error')

    return redirect(url_for('shop.cart_route'))


def add_to_cart(product_id):
    """Добавление товара в корзину"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Войдите в систему'})

        quantity = int(request.form.get('quantity', 1))
        size = request.form.get('size')

        if quantity < 1:
            return jsonify({
                'success': False,
                'message': 'Количество должно быть больше 0'
                })
        if quantity > 10:
            return jsonify({
                'success': False,
                'message': 'Максимальное количество - 10 шт.'
                })

        with get_cursor() as cur:
            if size:
                cur.execute("""
                    SELECT id, quantity
                    FROM cart_items
                    WHERE user_id = %s AND product_id = %s AND size = %s
                """, (current_user.id, product_id, size))
            else:
                cur.execute("""
                    SELECT id, quantity
                    FROM cart_items
                    WHERE user_id = %s AND product_id = %s AND size IS NULL
                """, (current_user.id, product_id))

            existing_item = cur.fetchone()

            if existing_item:
                new_quantity = existing_item['quantity'] + quantity
                if new_quantity > 10:
                    return jsonify({
                        'success': False,
                        'message': f'Максимальное количество в корзине - 10 шт. У вас уже {existing_item["quantity"]} шт.'
                    })

                cur.execute("""
                    UPDATE cart_items
                    SET quantity = %s
                    WHERE id = %s
                """, (new_quantity, existing_item['id']))
                action = 'updated'
            else:
                cur.execute("""
                    INSERT INTO cart_items (user_id, product_id, size, quantity, added_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (current_user.id, product_id, size if size else None, quantity))
                action = 'added'

            cur.execute("""
                SELECT name, price
                FROM products
                WHERE id = %s
            """, (product_id,))

            product = cur.fetchone()
            product_name = product['name'] if product else "Товар"

            cur.execute("""
                SELECT SUM(quantity) as total
                FROM cart_items
                WHERE user_id = %s
            """, (current_user.id,))

            result = cur.fetchone()
            cart_count = result['total'] or 0 if result else 0

            cur.connection.commit()

            message_text = f'Товар "{product_name}" добавлен в корзину'
            if action == 'updated':
                message_text = f'Количество товара "{product_name}" обновлено'

            return jsonify({
                'success': True,
                'message': message_text,
                'cart_count': cart_count,
                'action': action
            })

    except Exception:
        return jsonify({
            'success': False,
            'message': 'Произошла ошибка при добавлении товара'
        })


def remove_from_cart(item_id):
    """Удаление товара из корзины"""
    try:
        if not current_user.is_authenticated:
            flash('Войдите в систему', 'warning')
            return redirect('/cart')

        with get_cursor() as cur:
            cur.execute("""
                SELECT p.name
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                WHERE ci.id = %s AND ci.user_id = %s
            """, (item_id, current_user.id))

            item = cur.fetchone()

            if not item:
                flash('Товар не найден в корзине', 'error')
                return redirect('/cart')

            cur.execute("DELETE FROM cart_items WHERE id = %s AND user_id = %s",
                        (item_id, current_user.id))

            cur.connection.commit()

            flash(f'Товар "{item["name"]}" удален из корзины', 'success')
            return redirect('/cart')

    except Exception:
        flash('Ошибка удаления товара', 'danger')
        return redirect('/cart')


def clear_cart():
    """Очистка корзины"""
    try:
        if current_user.is_authenticated:
            with get_cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM cart_items WHERE user_id = %s",
                            (current_user.id,))
                result = cur.fetchone()
                count = result['count'] if result else 0

                if count == 0:
                    flash('Корзина уже пуста', 'info')
                    return redirect('/cart')

                cur.execute(
                    "DELETE FROM cart_items WHERE user_id = %s",
                    (current_user.id,))
                cur.connection.commit()

                flash(f'Корзина очищена ({count} товаров удалено)', 'success')
        else:
            flash('Войдите в систему', 'warning')

        return redirect('/cart')

    except Exception:
        flash('Ошибка очистки корзины', 'danger')
        return redirect('/cart')


def cart_status():
    """API для получения количества товаров в корзине"""
    try:
        cart_count = get_cart_count()
        return jsonify({
            'success': True,
            'cart_count': cart_count
        })
    except Exception:
        return jsonify({
            'success': False,
            'cart_count': 0
        })


def update_cart_item_quantity(item_id, new_quantity):
    """Обновление количества товара в корзине"""
    try:
        if not current_user.is_authenticated:
            return {'success': False, 'message': 'Войдите в систему'}

        if new_quantity < 1:
            return {'success': False, 'message': 'Количество должно быть больше 0'}

        if new_quantity > 10:
            return {'success': False, 'message': 'Максимальное количество - 10 шт.'}

        with get_cursor() as cur:
            cur.execute("""
                SELECT ci.product_id, ci.size, ci.quantity as old_quantity
                FROM cart_items ci
                WHERE ci.id = %s AND ci.user_id = %s
            """, (item_id, current_user.id))

            item = cur.fetchone()

            if not item:
                return {'success': False, 'message': 'Товар не найден в корзине'}

            available, message = check_stock_availability(
                item['product_id'],
                item['size'],
                new_quantity
            )

            if not available:
                return {'success': False, 'message': message}

            cur.execute("""
                UPDATE cart_items
                SET quantity = %s
                WHERE id = %s AND user_id = %s
            """, (new_quantity, item_id, current_user.id))

            cur.connection.commit()

            return {
                'success': True,
                'message': 'Количество обновлено',
                'old_quantity': item['old_quantity'],
                'new_quantity': new_quantity
            }

    except Exception:
        return {'success': False, 'message': 'Ошибка обновления количества'}


def get_cart_summary():
    """Получить сводку по корзине"""
    try:
        if not current_user.is_authenticated:
            return {
                'count': 0,
                'total': 0,
                'items': []
            }

        items = get_cart_items(current_user.id)

        total_quantity = 0
        total_price = 0.0

        for item in items:
            quantity = item['quantity']
            price = float(item['price'] or 0)

            total_quantity += quantity
            total_price += price * quantity

        return {
            'count': len(items),
            'total_quantity': total_quantity,
            'total_price': round(total_price, 2)
        }

    except Exception:
        return {
            'count': 0,
            'total': 0,
            'items': []
        }
