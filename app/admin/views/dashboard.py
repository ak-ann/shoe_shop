from flask import render_template, flash
from flask_login import login_required
from ..decorators import admin_required
from app.database import get_cursor


def format_date(date_obj):
    """Форматирование даты для отображения"""
    if not date_obj:
        return ""
    return date_obj.strftime('%d.%m.%Y %H:%M')


@login_required
@admin_required
def dashboard():
    """Главная страница админ-панели"""
    try:
        cur = get_cursor()

        stats = _get_dashboard_stats(cur)
        recent_users = _get_recent_users(cur)
        recent_products = _get_recent_products(cur)

        return render_template('admin/dashboard.html',
                               stats=stats,
                               recent_users=recent_users,
                               recent_products=recent_products,
                               recent_activities=[])

    except Exception as e:
        print(f"Ошибка в dashboard: {e}")
        flash(f'Ошибка при загрузке дашборда: {str(e)}', 'danger')
        return render_template('admin/dashboard.html',
                               stats={},
                               recent_users=[],
                               recent_products=[],
                               recent_activities=[])


def _get_dashboard_stats(cur):
    """Получить статистику для дашборда"""
    stats = {}

    tables = [
        ('total_users', 'users'),
        ('total_products', 'products'),
        ('total_categories', 'categories'),
        ('total_brands', 'shop_brand'),
        ('total_orders', 'orders')
    ]

    for stat_name, table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            result = cur.fetchone()
            stats[stat_name] = result['count'] if isinstance(result, dict) else result[0]
        except Exception as e:
            print(f"Ошибка получения статистики для {table}: {e}")
            stats[stat_name] = 0

    try:
        cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'completed'")
        result = cur.fetchone()
        stats['total_revenue'] = result['coalesce'] if isinstance(result, dict) else result[0] or 0
    except Exception as e:
        print(f"Ошибка получения выручки: {e}")
        stats['total_revenue'] = 0

    stats['online_users'] = 3
    stats['active_orders'] = 5

    return stats


def _get_recent_users(cur):
    """Получить последних пользователей"""
    try:
        cur.execute("""
            SELECT id, username, email, created_at, is_admin
            FROM users
            ORDER BY created_at DESC
            LIMIT 5
        """)
        users = cur.fetchall()

        return [{
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': format_date(user['created_at']),
            'is_staff': user['is_admin']
        } for user in users]

    except Exception as e:
        print(f"Ошибка получения пользователей: {e}")
        return []


def _get_recent_products(cur):
    """Получить последние товары"""
    try:
        cur.execute("""
            SELECT p.id, p.name, p.price, p.stock, p.is_published, p.created_at,
                   (SELECT image_url FROM product_images WHERE product_id = p.id AND is_main = TRUE LIMIT 1) as main_image
            FROM products p
            ORDER BY p.created_at DESC
            LIMIT 5
        """)
        products = cur.fetchall()

        return [{
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'image': product['main_image'],
            'stock': product['stock'],
            'is_published': product['is_published'],
            'created_at': format_date(product.get('created_at'))
        } for product in products]

    except Exception as e:
        print(f"Ошибка получения товаров: {e}")
        return []
