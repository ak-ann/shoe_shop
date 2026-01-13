from flask import render_template
from flask_login import current_user

from app.database import get_cursor


def my_products_view():
    """Страница с товарами пользователя"""
    cur = get_cursor()

    cur.execute("""
        SELECT p.*, c.name as category_name, b.name as brand_name,
            (SELECT image_url FROM product_images
                WHERE product_id = p.id AND is_main = TRUE LIMIT 1
                ) as main_image
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN shop_brand b ON p.brand_id = b.id
        WHERE p.seller_id = %s
        ORDER BY p.created_at DESC
    """, (current_user.id,))

    products = cur.fetchall()
    cur.close()

    return render_template('users/my_products.html', products=products)
