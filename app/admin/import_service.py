import csv
import logging
import os
import re

from app.database import get_cursor

logger = logging.getLogger(__name__)


class ImportService:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.import_dir = os.path.join(project_root, 'imports')

        if not os.path.exists(self.import_dir):
            os.makedirs(self.import_dir, exist_ok=True)

        print(f"ImportService: Директория импорта: {self.import_dir}")

    def validate_csv_file(self, filepath):
        """Валидация CSV файла."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sample = f.read(1024)
                sniffer = csv.Sniffer()
                if not sniffer.has_header(sample):
                    return False, "CSV файл не содержит заголовков"

                f.seek(0)
                reader = csv.reader(f)
                headers = next(reader)

                if len(headers) < 1:
                    return False, "CSV файл пуст или имеет неверный формат"

            return True, "Файл валиден"
        except Exception as e:
            return False, f"Ошибка валидации CSV: {str(e)}"

    def import_users_from_csv(self, filepath, update_existing=False):
        """Импорт пользователей из CSV."""
        stats = {
            'total': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            cur = get_cursor()

            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for i, row in enumerate(reader, 1):
                    try:
                        username = row.get('username', '').strip()
                        email = row.get('email', '').strip()
                        first_name = row.get('first_name', '').strip()
                        last_name = row.get('last_name', '').strip()
                        phone = row.get('phone', '').strip()
                        address = row.get('address', '').strip()
                        is_admin_value = row.get('is_admin', 'False').strip().lower()
                        is_admin = is_admin_value in ['true', '1', 'yes', 'да']

                        if not username or not email:
                            stats['skipped'] += 1
                            stats['errors'].append(
                                f"Строка {i}: Пропущены username или email"
                            )
                            continue

                        cur.execute("""
                            SELECT id FROM users 
                            WHERE email = %s OR username = %s
                        """, (email, username))
                        existing_user = cur.fetchone()

                        if existing_user and update_existing:
                            cur.execute("""
                                UPDATE users
                                SET username = %s, first_name = %s, last_name = %s,
                                    phone = %s, address = %s, is_admin = %s,
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (
                                username, first_name, last_name,
                                phone, address, is_admin, existing_user['id']
                            ))
                            stats['updated'] += 1
                        elif not existing_user:
                            cur.execute("""
                                INSERT INTO users
                                (username, email, first_name, last_name,
                                 phone, address, is_admin, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                            """, (
                                username, email, first_name, last_name,
                                phone, address, is_admin
                            ))
                            stats['inserted'] += 1
                        else:
                            stats['skipped'] += 1

                        stats['total'] += 1

                    except Exception as e:
                        stats['errors'].append(f"Строка {i}: {str(e)}")
                        continue

            cur.connection.commit()

            return {
                'success': True,
                'message': (
                    f'Импорт завершен. Всего: {stats["total"]}, '
                    f'Добавлено: {stats["inserted"]}, '
                    f'Обновлено: {stats["updated"]}, '
                    f'Пропущено: {stats["skipped"]}'
                ),
                'stats': stats
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка импорта пользователей: {str(e)}',
                'stats': stats
            }

    def import_products_from_csv(self, filepath, update_existing=False):
        """Импорт товаров из CSV."""
        stats = {
            'total': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            cur = get_cursor()

            cur.execute("SELECT id, name FROM categories")
            categories = {row['name'].lower(): row['id'] for row in cur.fetchall()}

            cur.execute("SELECT id, name FROM shop_brand")
            brands = {row['name'].lower(): row['id'] for row in cur.fetchall()}

            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for i, row in enumerate(reader, 1):
                    try:
                        name = row.get('name', '').strip()
                        sku = row.get('sku', '').strip()
                        description = row.get('description', '').strip()

                        try:
                            price = float(row.get('price', 0))
                        except ValueError:
                            price = 0.0

                        try:
                            stock = int(row.get('stock', 0))
                        except ValueError:
                            stock = 0

                        category_name = row.get('category', '').strip().lower()
                        brand_name = row.get('brand', '').strip().lower()

                        category_id = categories.get(category_name)
                        brand_id = brands.get(brand_name)

                        color = row.get('color', '').strip()
                        material = row.get('material', '').strip()
                        gender = row.get('gender', '').strip()
                        sizes = row.get('sizes', '').strip()

                        is_published_value = row.get(
                            'is_published', 'True'
                        ).strip().lower()
                        is_published = is_published_value in [
                            'true', '1', 'yes', 'да'
                        ]

                        if not name or not sku:
                            stats['skipped'] += 1
                            stats['errors'].append(
                                f"Строка {i}: Пропущены name или sku"
                            )
                            continue

                        cur.execute("""
                            SELECT id FROM products
                            WHERE sku = %s OR name = %s
                        """, (sku, name))
                        existing_product = cur.fetchone()

                        if existing_product and update_existing:
                            cur.execute("""
                                UPDATE products
                                SET name = %s, description = %s, price = %s,
                                    stock = %s, category_id = %s, brand_id = %s,
                                    is_published = %s, updated_at = NOW()
                                WHERE id = %s
                            """, (
                                name, description, price, stock,
                                category_id, brand_id, is_published,
                                existing_product['id']
                            ))

                            product_id = existing_product['id']

                            cur.execute("""
                                DELETE FROM product_attributes
                                WHERE product_id = %s
                            """, (product_id,))

                            if color:
                                cur.execute("""
                                    INSERT INTO product_attributes
                                    (product_id, attribute_type, value)
                                    VALUES (%s, 'color', %s)
                                """, (product_id, color))

                            if material:
                                cur.execute("""
                                    INSERT INTO product_attributes
                                    (product_id, attribute_type, value)
                                    VALUES (%s, 'material', %s)
                                """, (product_id, material))

                            if gender:
                                cur.execute("""
                                    INSERT INTO product_attributes
                                    (product_id, attribute_type, value)
                                    VALUES (%s, 'gender', %s)
                                """, (product_id, gender))

                            cur.execute("""
                                DELETE FROM product_sizes
                                WHERE product_id = %s
                            """, (product_id,))
                            if sizes:
                                size_list = [
                                    s.strip() for s in sizes.split(',')
                                    if s.strip()
                                ]
                                for size in size_list:
                                    cur.execute("""
                                        INSERT INTO product_sizes
                                        (product_id, size, quantity)
                                        VALUES (%s, %s, %s)
                                    """, (product_id, size, stock))

                            stats['updated'] += 1

                        elif not existing_product:
                            cur.execute("""
                                INSERT INTO products
                                (name, description, price, sku,
                                 stock, category_id, brand_id,
                                 is_published, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                                RETURNING id
                            """, (
                                name, description, price, sku, stock,
                                category_id, brand_id, is_published
                            ))

                            product_id = cur.fetchone()['id']

                            if color:
                                cur.execute("""
                                    INSERT INTO product_attributes 
                                    (product_id, attribute_type, value)
                                    VALUES (%s, 'color', %s)
                                """, (product_id, color))

                            if material:
                                cur.execute("""
                                    INSERT INTO product_attributes 
                                    (product_id, attribute_type, value)
                                    VALUES (%s, 'material', %s)
                                """, (product_id, material))

                            if gender:
                                cur.execute("""
                                    INSERT INTO product_attributes 
                                    (product_id, attribute_type, value)
                                    VALUES (%s, 'gender', %s)
                                """, (product_id, gender))

                            if sizes:
                                size_list = [
                                    s.strip() for s in sizes.split(',') 
                                    if s.strip()
                                ]
                                for size in size_list:
                                    cur.execute("""
                                        INSERT INTO product_sizes 
                                        (product_id, size, quantity)
                                        VALUES (%s, %s, %s)
                                    """, (product_id, size, stock))

                            stats['inserted'] += 1
                        else:
                            stats['skipped'] += 1

                        stats['total'] += 1

                    except Exception as e:
                        stats['errors'].append(f"Строка {i}: {str(e)}")
                        continue

            cur.connection.commit()

            return {
                'success': True,
                'message': (
                    f'Импорт товаров завершен. Всего: {stats["total"]}, '
                    f'Добавлено: {stats["inserted"]}, '
                    f'Обновлено: {stats["updated"]}, '
                    f'Пропущено: {stats["skipped"]}'
                ),
                'stats': stats
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка импорта товаров: {str(e)}',
                'stats': stats
            }

    def import_categories_from_csv(self, filepath, update_existing=False):
        """Импорт категорий из CSV."""
        stats = {
            'total': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            cur = get_cursor()

            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for i, row in enumerate(reader, 1):
                    try:
                        name = row.get('name', '').strip()
                        slug = row.get('slug', '').strip()
                        description = row.get('description', '').strip()

                        if not name:
                            stats['skipped'] += 1
                            stats['errors'].append(
                                f"Строка {i}: Пропущено название категории"
                            )
                            continue

                        if not slug:
                            slug = name.lower()
                            slug = re.sub(r'[^a-z0-9а-яё]+', '-', slug).strip('-')

                        cur.execute("""
                            SELECT id FROM categories
                            WHERE slug = %s OR name = %s
                        """, (slug, name))
                        existing_category = cur.fetchone()

                        if existing_category and update_existing:
                            cur.execute("""
                                UPDATE categories
                                SET name = %s, slug = %s, description = %s, 
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (
                                name, slug, description, existing_category['id']
                            ))
                            stats['updated'] += 1
                        elif not existing_category:
                            cur.execute("""
                                INSERT INTO categories
                                (name, slug, description, created_at)
                                VALUES (%s, %s, %s, NOW())
                            """, (name, slug, description))
                            stats['inserted'] += 1
                        else:
                            stats['skipped'] += 1

                        stats['total'] += 1

                    except Exception as e:
                        stats['errors'].append(f"Строка {i}: {str(e)}")
                        continue

            cur.connection.commit()

            return {
                'success': True,
                'message': (
                    f'Импорт категорий завершен. Всего: {stats["total"]}, '
                    f'Добавлено: {stats["inserted"]}, '
                    f'Обновлено: {stats["updated"]}, '
                    f'Пропущено: {stats["skipped"]}'
                ),
                'stats': stats
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка импорта категорий: {str(e)}',
                'stats': stats
            }

    def import_brands_from_csv(self, filepath, update_existing=False):
        """Импорт брендов из CSV."""
        stats = {
            'total': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            cur = get_cursor()

            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for i, row in enumerate(reader, 1):
                    try:
                        name = row.get('name', '').strip()
                        description = row.get('description', '').strip()

                        if not name:
                            stats['skipped'] += 1
                            stats['errors'].append(
                                f"Строка {i}: Пропущено название бренда"
                            )
                            continue

                        is_published_value = row.get(
                            'is_published', 'True'
                        ).strip().lower()
                        is_published = is_published_value in [
                            'true', '1', 'yes', 'да'
                        ]

                        cur.execute("""
                            SELECT id FROM shop_brand 
                            WHERE name = %s
                        """, (name,))
                        existing_brand = cur.fetchone()

                        if existing_brand and update_existing:
                            cur.execute("""
                                UPDATE shop_brand
                                SET description = %s, is_published = %s,
                                    updated_at = NOW()
                                WHERE id = %s
                            """, (
                                description, is_published, existing_brand['id']
                            ))
                            stats['updated'] += 1
                        elif not existing_brand:
                            cur.execute("""
                                INSERT INTO shop_brand 
                                (name, description, is_published, created_at)
                                VALUES (%s, %s, %s, NOW())
                            """, (name, description, is_published))
                            stats['inserted'] += 1
                        else:
                            stats['skipped'] += 1

                        stats['total'] += 1

                    except Exception as e:
                        stats['errors'].append(f"Строка {i}: {str(e)}")
                        continue

            cur.connection.commit()

            return {
                'success': True,
                'message': (
                    f'Импорт брендов завершен. Всего: {stats["total"]}, '
                    f'Добавлено: {stats["inserted"]}, '
                    f'Обновлено: {stats["updated"]}, '
                    f'Пропущено: {stats["skipped"]}'
                ),
                'stats': stats
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка импорта брендов: {str(e)}',
                'stats': stats
            }

    def get_import_templates(self):
        """Получить шаблоны CSV для импорта."""
        templates = {
            'users': {
                'filename': 'users_template.csv',
                'columns': [
                    'username', 'email', 'first_name', 'last_name',
                    'phone', 'address', 'is_admin'
                ],
                'description': 'Импорт пользователей',
                'example': [
                    [
                        'ivanov', 'ivan@example.com', 'Иван', 'Иванов',
                        '+79991234567', 'Москва, ул. Ленина 1', 'False'
                    ],
                    [
                        'petrov', 'petr@example.com', 'Петр', 'Петров',
                        '+79998765432', 'СПб, Невский пр. 10', 'True'
                    ]
                ]
            },
            'products': {
                'filename': 'products_template.csv',
                'columns': [
                    'name', 'sku', 'description', 'price', 'stock',
                    'category', 'brand', 'color', 'material', 'gender',
                    'sizes', 'is_published'
                ],
                'description': 'Импорт товаров',
                'example': [
                    [
                        'Кроссовки Nike Air', 'NIKE-001', 'Спортивные кроссовки',
                        '8999.99', '50', 'Кроссовки', 'Nike', 'Черный', 'Кожа',
                        'Мужские', '40,41,42,43', 'True'
                    ],
                    [
                        'Туфли кожаные', 'SHOES-002', 'Классические туфли',
                        '5999.50', '30', 'Туфли', 'Adidas', 'Коричневый',
                        'Натуральная кожа', 'Мужские', '39,40,41', 'True'
                    ]
                ]
            },
            'categories': {
                'filename': 'categories_template.csv',
                'columns': ['name', 'slug', 'description'],
                'description': 'Импорт категорий',
                'example': [
                    ['Кроссовки', 'sneakers', 'Спортивная обувь'],
                    ['Туфли', 'shoes', 'Классическая обувь'],
                    ['Сапоги', 'boots', 'Зимняя обувь']
                ]
            },
            'brands': {
                'filename': 'brands_template.csv',
                'columns': ['name', 'description', 'is_published'],
                'description': 'Импорт брендов',
                'example': [
                    [
                        'Nike', 'Американский производитель спортивной одежды',
                        'True'
                    ],
                    [
                        'Adidas', 'Немецкий производитель спортивной одежды',
                        'True'
                    ],
                    ['Reebok', 'Производитель спортивной обуви', 'False']
                ]
            }
        }

        return templates

    def create_template_file(self, template_type):
        """Создать файл шаблона для импорта."""
        templates = self.get_import_templates()

        if template_type not in templates:
            return None

        template = templates[template_type]
        filepath = os.path.join(self.import_dir, template['filename'])

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(template['columns'])

            for example_row in template['example']:
                writer.writerow(example_row)

        return filepath
