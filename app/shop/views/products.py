from flask import render_template, request, abort, flash
from flask_login import current_user
from app.forms import ReviewForm
from app.database import get_cursor


def index():
    """Главная страница магазина"""
    try:
        with get_cursor() as cur:
            selected_categories = request.args.getlist('categories', type=int)
            selected_brands = request.args.getlist('brands', type=int)
            search_query = request.args.get('q', '').strip()

            sql = """
                SELECT p.*,
                    c.name as category_name,
                    b.name as brand_name,
                    COALESCE(
                        (SELECT image_url FROM product_images
                         WHERE product_id = p.id AND is_main = TRUE LIMIT 1),
                        (SELECT image_url FROM product_images
                         WHERE product_id = p.id LIMIT 1),
                        '/static/images/no-image.png'
                    ) as image_url
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN shop_brand b ON p.brand_id = b.id
                WHERE p.is_published = true
            """

            conditions = []
            params = []

            if search_query:
                conditions.append("(p.name ILIKE %s OR p.description ILIKE %s OR p.sku ILIKE %s)")
                search_pattern = f'%{search_query}%'
                params.extend([search_pattern, search_pattern, search_pattern])

            if selected_categories:
                placeholders = ', '.join(['%s'] * len(selected_categories))
                conditions.append(f"p.category_id IN ({placeholders})")
                params.extend(selected_categories)

            if selected_brands:
                placeholders = ', '.join(['%s'] * len(selected_brands))
                conditions.append(f"p.brand_id IN ({placeholders})")
                params.extend(selected_brands)

            if conditions:
                sql += " AND " + " AND ".join(conditions)

            sql += " ORDER BY p.created_at DESC"

            cur.execute(sql, params)
            all_products = cur.fetchall()

            cur.execute("SELECT * FROM categories WHERE is_published = true ORDER BY name")
            categories = cur.fetchall()

            cur.execute("SELECT * FROM shop_brand WHERE is_published = true ORDER BY name")
            brands = cur.fetchall()

            page = request.args.get('page', 1, type=int)
            per_page = 12

            total = len(all_products)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_products = all_products[start:end]

            class Paginate:
                def __init__(self, items, page, per_page, total):
                    self.items = items
                    self.page = page
                    self.per_page = per_page
                    self.total = total
                    self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
                    self.has_next = page < self.pages
                    self.has_prev = page > 1

                @property
                def prev_num(self):
                    return self.page - 1 if self.has_prev else None

                @property
                def next_num(self):
                    return self.page + 1 if self.has_next else None

            pagination = Paginate(paginated_products, page, per_page, total)

            return render_template('shop/index.html',
                                   products=pagination,
                                   categories=categories,
                                   brands=brands,
                                   selected_categories=selected_categories,
                                   selected_brands=selected_brands,
                                   search_query=search_query)
    except Exception:
        flash('Ошибка при загрузке товаров', 'error')
        return render_template('shop/index.html', products=[], categories=[], brands=[])


def product_detail(product_id):
    """Страница товара"""
    try:
        with get_cursor() as cur:
            sql = """
                SELECT
                    p.*,
                    c.name as category_name,
                    b.name as brand_name,
                    COALESCE(
                        (SELECT image_url FROM product_images
                         WHERE product_id = p.id AND is_main = TRUE LIMIT 1),
                        (SELECT image_url FROM product_images
                         WHERE product_id = p.id LIMIT 1),
                        '/static/images/no-image.png'
                    ) as main_image
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN shop_brand b ON p.brand_id = b.id
                WHERE p.id = %s
            """
            cur.execute(sql, (product_id,))
            product = cur.fetchone()

            if not product:
                abort(404)

            is_published = product.get('is_published')
            seller_id = product.get('seller_id')

            if not is_published:
                if not current_user.is_authenticated:
                    abort(404)
                if seller_id and current_user.id != seller_id and not current_user.is_staff:
                    abort(404)

            cur.execute("""
                SELECT
                    r.*,
                    COALESCE(u.username, 'Анонимный пользователь') as author_name
                FROM reviews r
                LEFT JOIN users u ON r.user_id = u.id
                WHERE r.product_id = %s
                ORDER BY r.created_at DESC
            """, (product_id,))
            reviews = cur.fetchall()

            try:
                cur.execute("""
                    UPDATE products
                    SET views = COALESCE(views, 0) + 1
                    WHERE id = %s
                """, (product_id,))
            except Exception:
                pass

            cur.execute("""
                SELECT image_url, is_main, sort_order
                FROM product_images
                WHERE product_id = %s
                ORDER BY is_main DESC, sort_order
            """, (product_id,))
            images = cur.fetchall()

            cur.execute("""
                SELECT size, quantity
                FROM product_sizes
                WHERE product_id = %s
                ORDER BY size
            """, (product_id,))
            sizes = cur.fetchall()

            cur.execute("""
                SELECT attribute_type, value
                FROM product_attributes
                WHERE product_id = %s
            """, (product_id,))
            attributes = cur.fetchall()

            form = ReviewForm()

            return render_template('shop/detail.html',
                                   product=product,
                                   reviews=reviews,
                                   images=images,
                                   sizes=sizes,
                                   attributes=attributes,
                                   form=form)

    except Exception:
        abort(500, description="Ошибка при загрузке товара")


def categories_list():
    """Список категорий"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT *
                FROM categories
                WHERE is_published = true
                ORDER BY name
            """)
            categories = cur.fetchall()

            return render_template('shop/categories.html', categories=categories)

    except Exception:
        flash('Ошибка при загрузке категорий', 'error')
        return render_template('shop/categories.html', categories=[])


def category_products(slug):
    """Товары категории"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT *
                FROM categories
                WHERE slug = %s AND is_published = true
            """, (slug,))
            category = cur.fetchone()

            if not category:
                abort(404)

            category_id = category.get('id')

            sql = """
                SELECT
                    p.*,
                    c.name as category_name,
                    b.name as brand_name,
                    COALESCE(
                        (SELECT image_url FROM product_images
                         WHERE product_id = p.id AND is_main = TRUE LIMIT 1),
                        '/static/images/no-image.png'
                    ) as image_url
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN shop_brand b ON p.brand_id = b.id
                WHERE p.category_id = %s AND p.is_published = true
                ORDER BY p.created_at DESC
            """

            cur.execute(sql, (category_id,))
            products = cur.fetchall()

            page = request.args.get('page', 1, type=int)
            per_page = 12

            total = len(products)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_products = products[start:end]

            class Paginate:
                def __init__(self, items, page, per_page, total):
                    self.items = items
                    self.page = page
                    self.per_page = per_page
                    self.total = total
                    self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
                    self.has_next = page < self.pages
                    self.has_prev = page > 1

                @property
                def prev_num(self):
                    return self.page - 1 if self.has_prev else None

                @property
                def next_num(self):
                    return self.page + 1 if self.has_next else None

            pagination = Paginate(paginated_products, page, per_page, total)

            return render_template('shop/category.html',
                                   category=category,
                                   products=pagination)

    except Exception:
        abort(500, description="Ошибка при загрузке товаров категории")


def brands_list():
    """Список брендов"""
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT *
                FROM shop_brands
                WHERE is_published = true
                ORDER BY name
            """)
            brands = cur.fetchall()

            return render_template('shop/brands.html', brands=brands)

    except Exception:
        flash('Ошибка при загрузке брендов', 'error')
        return render_template('shop/brands.html', brands=[])
