# import csv
# import json
# import os
# import zipfile
# from datetime import datetime
# from io import BytesIO, StringIO

# import psycopg2
# from flask import current_app, send_file
# from app.database import get_cursor, get_db_connection


# class ExportService:
#     def __init__(self):
#         self.export_dir = "exports"
#         if not os.path.exists(self.export_dir):
#             os.makedirs(self.export_dir)

#     def export_table_to_csv(self, table_name, filename=None):
#         """Экспорт данных конкретной таблицы в CSV."""
#         if filename is None:
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             filename = f"{table_name}_{timestamp}.csv"

#         filepath = os.path.join(self.export_dir, filename)

#         try:
#             conn = self.get_db_connection()
#             cur = conn.cursor()

#             cur.execute(f"SELECT * FROM {table_name}")
#             records = cur.fetchall()

#             cur.execute("""
#                 SELECT column_name 
#                 FROM information_schema.columns 
#                 WHERE table_name = %s 
#                 ORDER BY ordinal_position
#             """, (table_name,))
#             columns = [row[0] for row in cur.fetchall()]

#             with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
#                 writer = csv.writer(csvfile)
#                 writer.writerow(columns)
#                 for record in records:
#                     writer.writerow(record)

#             cur.close()
#             conn.close()

#             return {
#                 'success': True,
#                 'message': f'Таблица {table_name} успешно экспортирована',
#                 'filepath': filepath,
#                 'filename': filename
#             }

#         except Exception as e:
#             return {
#                 'success': False,
#                 'message': f'Ошибка при экспорте таблицы {table_name}: {str(e)}'
#             }

#     def export_users_to_csv(self, filename=None):
#         """Экспорт пользователей с дополнительной информацией."""
#         if filename is None:
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             filename = f"users_{timestamp}.csv"

#         filepath = os.path.join(self.export_dir, filename)

#         try:
#             conn = self.get_db_connection()
#             cur = conn.cursor()

#             cur.execute("""
#                 SELECT
#                     u.id, u.username, u.email,
#                     u.first_name, u.last_name, u.phone, u.address,
#                     u.created_at, u.is_admin,
#                     COALESCE(COUNT(o.id), 0) as order_count,
#                     COALESCE(SUM(o.total_amount), 0) as total_spent
#                 FROM users u
#                 LEFT JOIN orders o ON u.id = o.user_id
#                 GROUP BY u.id
#                 ORDER BY u.created_at DESC
#             """)

#             records = cur.fetchall()

#             columns = [
#                 'ID', 'Имя пользователя', 'Email',
#                 'Имя', 'Фамилия', 'Телефон', 'Адрес',
#                 'Дата регистрации', 'Администратор',
#                 'Количество заказов', 'Общая сумма покупок'
#             ]

#             with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
#                 writer = csv.writer(csvfile)
#                 writer.writerow(columns)

#                 for record in records:
#                     formatted_record = list(record)

#                     if formatted_record[7]:
#                         formatted_record[7] = formatted_record[7].strftime(
#                             '%d.%m.%Y %H:%M'
#                         )
#                     formatted_record[8] = 'Да' if formatted_record[8] else 'Нет'
#                     writer.writerow(formatted_record)

#             cur.close()
#             conn.close()

#             return {
#                 'success': True,
#                 'message': 'Пользователи успешно экспортированы',
#                 'filepath': filepath,
#                 'filename': filename
#             }

#         except Exception as e:
#             return {
#                 'success': False,
#                 'message': f'Ошибка при экспорте пользователей: {str(e)}'
#             }

#     def export_products_to_csv(self, filename=None):
#         """Экспорт товаров с детальной информацией."""
#         if filename is None:
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             filename = f"products_{timestamp}.csv"

#         filepath = os.path.join(self.export_dir, filename)

#         try:
#             conn = self.get_db_connection()
#             cur = conn.cursor()

#             cur.execute("""
#                 SELECT
#                     p.id, p.name, p.description, p.price, p.sku,
#                     p.stock, p.is_published, p.created_at,
#                     c.name as category_name,
#                     b.name as brand_name,
#                     STRING_AGG(DISTINCT ps.size, ', ') as sizes,
#                     STRING_AGG(DISTINCT pa.value, ' | ') as attributes
#                 FROM products p
#                 LEFT JOIN categories c ON p.category_id = c.id
#                 LEFT JOIN shop_brand b ON p.brand_id = b.id
#                 LEFT JOIN product_sizes ps ON p.id = ps.product_id
#                 LEFT JOIN product_attributes pa ON p.id = pa.product_id
#                 GROUP BY p.id, c.name, b.name
#                 ORDER BY p.created_at DESC
#             """)

#             records = cur.fetchall()

#             columns = [
#                 'ID', 'Название', 'Описание', 'Цена', 'Артикул',
#                 'Количество', 'Опубликован', 'Дата создания',
#                 'Категория', 'Бренд', 'Размеры', 'Атрибуты'
#             ]

#             with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
#                 writer = csv.writer(csvfile)
#                 writer.writerow(columns)

#                 for record in records:
#                     formatted_record = list(record)
#                     if formatted_record[7]:
#                         formatted_record[7] = formatted_record[7].strftime(
#                             '%d.%m.%Y %H:%M'
#                         )
#                     formatted_record[6] = 'Да' if formatted_record[6] else 'Нет'
#                     writer.writerow(formatted_record)

#             cur.close()
#             conn.close()

#             return {
#                 'success': True,
#                 'message': 'Товары успешно экспортированы',
#                 'filepath': filepath,
#                 'filename': filename
#             }

#         except Exception as e:
#             return {
#                 'success': False,
#                 'message': f'Ошибка при экспорте товаров: {str(e)}'
#             }

#     def export_orders_to_csv(self, start_date=None, end_date=None, filename=None):
#         """Экспорт заказов за период."""
#         if filename is None:
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             filename = f"orders_{timestamp}.csv"

#         filepath = os.path.join(self.export_dir, filename)

#         try:
#             conn = self.get_db_connection()
#             cur = conn.cursor()

#             query = """
#                 SELECT
#                     o.id, o.order_number, o.total_amount, o.status,
#                     o.created_at, o.shipping_address, o.payment_method,
#                     u.username, u.email,
#                     COUNT(oi.id) as items_count
#                 FROM orders o
#                 LEFT JOIN users u ON o.user_id = u.id
#                 LEFT JOIN order_items oi ON o.id = oi.order_id
#             """

#             params = []
#             conditions = []

#             if start_date:
#                 conditions.append("o.created_at >= %s")
#                 params.append(start_date)

#             if end_date:
#                 conditions.append("o.created_at <= %s")
#                 params.append(end_date)

#             if conditions:
#                 query += " WHERE " + " AND ".join(conditions)

#             query += " GROUP BY o.id, u.username, u.email ORDER BY o.created_at DESC"

#             cur.execute(query, params)
#             records = cur.fetchall()

#             columns = [
#                 'ID', 'Номер заказа', 'Сумма', 'Статус',
#                 'Дата создания', 'Адрес доставки', 'Способ оплаты',
#                 'Пользователь', 'Email', 'Количество товаров'
#             ]

#             with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
#                 writer = csv.writer(csvfile)
#                 writer.writerow(columns)

#                 for record in records:
#                     formatted_record = list(record)
#                     if formatted_record[4]:
#                         formatted_record[4] = formatted_record[4].strftime(
#                             '%d.%m.%Y %H:%M'
#                         )
#                     writer.writerow(formatted_record)

#             cur.close()
#             conn.close()

#             return {
#                 'success': True,
#                 'message': 'Заказы успешно экспортированы',
#                 'filepath': filepath,
#                 'filename': filename
#             }

#         except Exception as e:
#             return {
#                 'success': False,
#                 'message': f'Ошибка при экспорте заказов: {str(e)}'
#             }

#     def export_full_backup(self, filename=None):
#         """Создание полного бэкапа базы данных."""
#         if filename is None:
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             filename = f"full_backup_{timestamp}.zip"

#         zip_path = os.path.join(self.export_dir, filename)

#         try:
#             tables = [
#                 'users', 'products', 'categories', 'shop_brand',
#                 'orders', 'order_items', 'reviews', 'cart_items',
#                 'wishlists', 'product_images', 'product_sizes',
#                 'product_attributes', 'product_price_history'
#             ]

#             with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
#                 for table in tables:
#                     try:
#                         result = self.export_table_to_csv(table, f"{table}.csv")
#                         if result['success']:
#                             zipf.write(
#                                 result['filepath'],
#                                 os.path.basename(result['filepath'])
#                             )
#                             os.remove(result['filepath'])
#                     except Exception as e:
#                         print(f"Ошибка при экспорте таблицы {table}: {e}")

#                 meta = {
#                     'export_date': datetime.now().isoformat(),
#                     'tables_exported': tables,
#                     'database': current_app.config.get('DB_NAME', 'shoe_shop')
#                 }

#                 meta_json = json.dumps(meta, indent=2, ensure_ascii=False)
#                 zipf.writestr('backup_metadata.json', meta_json)

#             return {
#                 'success': True,
#                 'message': 'Полный бэкап создан успешно',
#                 'filepath': zip_path,
#                 'filename': filename
#             }

#         except Exception as e:
#             return {
#                 'success': False,
#                 'message': f'Ошибка при создании бэкапа: {str(e)}'
#             }

#     def get_available_exports(self):
#         """Получить список доступных экспортов."""
#         return [
#             {
#                 'id': 'users',
#                 'name': 'Пользователи',
#                 'description': 'Все пользователи системы'
#             },
#             {
#                 'id': 'products',
#                 'name': 'Товары',
#                 'description': 'Все товары с атрибутами'
#             },
#             {
#                 'id': 'orders',
#                 'name': 'Заказы',
#                 'description': 'Заказы за указанный период'
#             },
#             {
#                 'id': 'full',
#                 'name': 'Полный бэкап',
#                 'description': 'Все таблицы БД в ZIP-архиве'
#             },
#             {
#                 'id': 'categories',
#                 'name': 'Категории',
#                 'description': 'Все категории товаров'
#             },
#             {
#                 'id': 'brands',
#                 'name': 'Бренды',
#                 'description': 'Все бренды магазина'
#             }
#         ]

#     def cleanup_old_exports(self, days_to_keep=7):
#         """Очистка старых файлов экспорта."""
#         try:
#             cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

#             for filename in os.listdir(self.export_dir):
#                 filepath = os.path.join(self.export_dir, filename)
#                 if os.path.isfile(filepath):
#                     file_time = os.path.getctime(filepath)
#                     if file_time < cutoff_date:
#                         os.remove(filepath)
#                         print(f"Удален старый файл экспорта: {filename}")

#             return True
#         except Exception as e:
#             print(f"Ошибка при очистке старых файлов: {e}")
#             return False
import csv
import json
import os
import zipfile
from datetime import datetime
from io import BytesIO, StringIO

from app.database import get_cursor


class ExportService:
    def __init__(self):
        # Получаем корень проекта (на 2 уровня выше текущего файла)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.export_dir = os.path.join(project_root, 'exports')
        
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir, exist_ok=True)
        
        print(f"ExportService: Директория экспорта: {self.export_dir}")  # Debug

    def export_table_to_csv(self, table_name, filename=None):
        """Экспорт данных конкретной таблицы в CSV."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{table_name}_{timestamp}.csv"

        filepath = os.path.join(self.export_dir, filename)

        try:
            cur = get_cursor()

            cur.execute(f"SELECT * FROM {table_name}")
            records = cur.fetchall()

            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            columns = [row[0] for row in cur.fetchall()]

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                for record in records:
                    writer.writerow(record)

            return {
                'success': True,
                'message': f'Таблица {table_name} успешно экспортирована',
                'filepath': filepath,
                'filename': filename
            }

        except Exception as e:
            print(f"Ошибка экспорта таблицы {table_name}: {e}")  # Debug
            return {
                'success': False,
                'message': f'Ошибка при экспорте таблицы {table_name}: {str(e)}'
            }

    def export_users_to_csv(self, filename=None):
        """Экспорт пользователей с дополнительной информацией."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"users_{timestamp}.csv"

        filepath = os.path.join(self.export_dir, filename)
        
        print(f"Попытка создания файла: {filepath}")  # Debug

        try:
            cur = get_cursor()

            cur.execute("""
                SELECT
                    u.id, u.username, u.email,
                    u.first_name, u.last_name, u.phone, u.address,
                    u.created_at, u.is_admin,
                    COALESCE(COUNT(o.id), 0) as order_count,
                    COALESCE(SUM(o.total_amount), 0) as total_spent
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                GROUP BY u.id
                ORDER BY u.created_at DESC
            """)

            records = cur.fetchall()

            columns = [
                'ID', 'Имя пользователя', 'Email',
                'Имя', 'Фамилия', 'Телефон', 'Адрес',
                'Дата регистрации', 'Администратор',
                'Количество заказов', 'Общая сумма покупок'
            ]

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)

                for record in records:
                    formatted_record = list(record)

                    if formatted_record[7]:
                        formatted_record[7] = formatted_record[7].strftime(
                            '%d.%m.%Y %H:%M'
                        )
                    formatted_record[8] = 'Да' if formatted_record[8] else 'Нет'
                    writer.writerow(formatted_record)

            print(f"Файл успешно создан: {filepath}")  # Debug

            return {
                'success': True,
                'message': 'Пользователи успешно экспортированы',
                'filepath': filepath,
                'filename': filename
            }

        except Exception as e:
            print(f"Ошибка при экспорте пользователей: {e}")  # Debug
            return {
                'success': False,
                'message': f'Ошибка при экспорте пользователей: {str(e)}'
            }

    def export_products_to_csv(self, filename=None):
        """Экспорт товаров с детальной информацией."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"products_{timestamp}.csv"

        filepath = os.path.join(self.export_dir, filename)

        try:
            cur = get_cursor()

            cur.execute("""
                SELECT
                    p.id, p.name, p.description, p.price, p.sku,
                    p.stock, p.is_published, p.created_at,
                    c.name as category_name,
                    b.name as brand_name,
                    STRING_AGG(DISTINCT ps.size, ', ') as sizes,
                    STRING_AGG(DISTINCT pa.value, ' | ') as attributes
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN shop_brand b ON p.brand_id = b.id
                LEFT JOIN product_sizes ps ON p.id = ps.product_id
                LEFT JOIN product_attributes pa ON p.id = pa.product_id
                GROUP BY p.id, c.name, b.name
                ORDER BY p.created_at DESC
            """)

            records = cur.fetchall()

            columns = [
                'ID', 'Название', 'Описание', 'Цена', 'Артикул',
                'Количество', 'Опубликован', 'Дата создания',
                'Категория', 'Бренд', 'Размеры', 'Атрибуты'
            ]

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)

                for record in records:
                    formatted_record = list(record)
                    if formatted_record[7]:
                        formatted_record[7] = formatted_record[7].strftime(
                            '%d.%m.%Y %H:%M'
                        )
                    formatted_record[6] = 'Да' if formatted_record[6] else 'Нет'
                    writer.writerow(formatted_record)

            return {
                'success': True,
                'message': 'Товары успешно экспортированы',
                'filepath': filepath,
                'filename': filename
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при экспорте товаров: {str(e)}'
            }

    def export_orders_to_csv(self, start_date=None, end_date=None, filename=None):
        """Экспорт заказов за период."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"orders_{timestamp}.csv"

        filepath = os.path.join(self.export_dir, filename)

        try:
            cur = get_cursor()

            query = """
                SELECT
                    o.id, o.order_number, o.total_amount, o.status,
                    o.created_at, o.shipping_address, o.payment_method,
                    u.username, u.email,
                    COUNT(oi.id) as items_count
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                LEFT JOIN order_items oi ON o.id = oi.order_id
            """

            params = []
            conditions = []

            if start_date:
                conditions.append("o.created_at >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("o.created_at <= %s")
                params.append(end_date)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " GROUP BY o.id, u.username, u.email ORDER BY o.created_at DESC"

            cur.execute(query, params)
            records = cur.fetchall()

            columns = [
                'ID', 'Номер заказа', 'Сумма', 'Статус',
                'Дата создания', 'Адрес доставки', 'Способ оплаты',
                'Пользователь', 'Email', 'Количество товаров'
            ]

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)

                for record in records:
                    formatted_record = list(record)
                    if formatted_record[4]:
                        formatted_record[4] = formatted_record[4].strftime(
                            '%d.%m.%Y %H:%M'
                        )
                    writer.writerow(formatted_record)

            return {
                'success': True,
                'message': 'Заказы успешно экспортированы',
                'filepath': filepath,
                'filename': filename
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при экспорте заказов: {str(e)}'
            }

    def export_full_backup(self, filename=None):
        """Создание полного бэкапа базы данных."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"full_backup_{timestamp}.zip"

        zip_path = os.path.join(self.export_dir, filename)

        try:
            tables = [
                'users', 'products', 'categories', 'shop_brand',
                'orders', 'order_items', 'reviews', 'cart_items',
                'wishlists', 'product_images', 'product_sizes',
                'product_attributes', 'product_price_history'
            ]

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for table in tables:
                    try:
                        result = self.export_table_to_csv(table, f"{table}.csv")
                        if result['success']:
                            zipf.write(
                                result['filepath'],
                                os.path.basename(result['filepath'])
                            )
                            os.remove(result['filepath'])
                    except Exception as e:
                        print(f"Ошибка при экспорте таблицы {table}: {e}")

                meta = {
                    'export_date': datetime.now().isoformat(),
                    'tables_exported': tables,
                    'database': 'shoe_shop'  # Убрал зависимость от current_app
                }

                meta_json = json.dumps(meta, indent=2, ensure_ascii=False)
                zipf.writestr('backup_metadata.json', meta_json)

            return {
                'success': True,
                'message': 'Полный бэкап создан успешно',
                'filepath': zip_path,
                'filename': filename
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при создании бэкапа: {str(e)}'
            }

    def get_available_exports(self):
        """Получить список доступных экспортов."""
        return [
            {
                'id': 'users',
                'name': 'Пользователи',
                'description': 'Все пользователи системы'
            },
            {
                'id': 'products',
                'name': 'Товары',
                'description': 'Все товары с атрибутами'
            },
            {
                'id': 'orders',
                'name': 'Заказы',
                'description': 'Заказы за указанный период'
            },
            {
                'id': 'full',
                'name': 'Полный бэкап',
                'description': 'Все таблицы БД в ZIP-архиве'
            },
            {
                'id': 'categories',
                'name': 'Категории',
                'description': 'Все категории товаров'
            },
            {
                'id': 'brands',
                'name': 'Бренды',
                'description': 'Все бренды магазина'
            }
        ]

    def cleanup_old_exports(self, days_to_keep=7):
        """Очистка старых файлов экспорта."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

            for filename in os.listdir(self.export_dir):
                filepath = os.path.join(self.export_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getctime(filepath)
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        print(f"Удален старый файл экспорта: {filename}")

            return True
        except Exception as e:
            print(f"Ошибка при очистке старых файлов: {e}")
            return False