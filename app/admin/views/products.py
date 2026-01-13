"""
Управление товарами
"""

from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
from psycopg2 import Error

from app.forms.product import ProductForm
from ..decorators import admin_required
from app.database import get_cursor


def format_date(date_obj):
    """Форматирование даты для отображения"""
    if not date_obj:
        return ""
    return date_obj.strftime('%d.%m.%Y %H:%M')


@login_required
@admin_required
def products():
    """Список товаров с фильтрами"""
    try:
        cur = get_cursor()
        
        # Параметры фильтрации
        category_id = request.args.get('category_id', type=int)
        brand_id = request.args.get('brand_id', type=int)
        status = request.args.get('status', '')
        search = request.args.get('search', '').strip()
        
        # Получение товаров
        products_list = _get_filtered_products(cur, category_id, brand_id, status, search)
        
        # Получение категорий и брендов для фильтров
        categories = _get_categories(cur)
        brands = _get_brands(cur)
        
        return render_template('admin/products.html',
                             products=products_list,
                             categories=categories,
                             brands=brands,
                             selected_category=category_id,
                             selected_brand=brand_id,
                             selected_status=status,
                             search_query=search)
                             
    except Error as e:
        flash('Ошибка при загрузке товаров', 'danger')
        return render_template('admin/products.html',
                             products=[],
                             categories=[],
                             brands=[])


def _get_categories(cur):
    """Получить список категорий"""
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    return [{'id': cat['id'], 'name': cat['name']} for cat in cur.fetchall()]


def _get_brands(cur):
    """Получить список брендов"""
    cur.execute("SELECT id, name FROM shop_brand ORDER BY name")
    return [{'id': brand['id'], 'name': brand['name']} for brand in cur.fetchall()]


def _get_filtered_products(cur, category_id, brand_id, status, search):
    """Получить отфильтрованные товары"""
    query = """
        SELECT 
            p.id, 
            p.name, 
            p.sku,
            p.price,
            p.stock,
            p.is_published,
            p.created_at,
            c.name as category_name,
            b.name as brand_name,
            pi.image_url
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN shop_brand b ON p.brand_id = b.id
        LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_main = TRUE
        WHERE 1=1
    """
    
    params = []
    
    # Фильтры
    if category_id:
        query += " AND p.category_id = %s"
        params.append(category_id)
    
    if brand_id:
        query += " AND p.brand_id = %s"
        params.append(brand_id)
    
    if status == 'published':
        query += " AND p.is_published = TRUE"
    elif status == 'draft':
        query += " AND p.is_published = FALSE"
    
    if search:
        query += " AND (p.name ILIKE %s OR p.sku ILIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    query += " ORDER BY p.created_at DESC"
    cur.execute(query, params)
    
    # Форматирование результата
    products_data = []
    for row in cur.fetchall():
        products_data.append({
            'id': row['id'],
            'name': row['name'],
            'sku': row['sku'] or '',
            'price': row['price'] or 0,
            'stock': row['stock'] or 0,
            'is_published': row['is_published'],
            'created_at': format_date(row['created_at']),
            'category_name': row['category_name'] or 'Без категории',
            'brand_name': row['brand_name'] or 'Без бренда',
            'image_url': row['image_url']
        })
    
    return products_data


@login_required
@admin_required
def create_product():
    """Создание товара"""
    try:
        cur = get_cursor()
        
        # Получение данных для формы
        categories = _get_categories(cur)
        brands = _get_brands(cur)
        
        form = ProductForm()
        form.category_id.choices = [(0, '-- Выберите категорию --')] + [(c['id'], c['name']) for c in categories]
        form.brand_id.choices = [(0, '-- Выберите бренд --')] + [(b['id'], b['name']) for b in brands]
        
        if request.method == 'GET':
            return render_template('admin/product_form.html',
                                 form=form,
                                 product=None)
        
        if form.validate_on_submit():
            return _handle_product_creation(cur, form)
        
        # Если форма не валидна
        flash('Пожалуйста, исправьте ошибки в форме', 'danger')
        return render_template('admin/product_form.html',
                             form=form,
                             product=None)
                             
    except Error as e:
        flash('Ошибка при создании товара', 'danger')
        return redirect(url_for('admin.products'))


def _handle_product_creation(cur, form):
    """Обработать создание товара"""
    try:
        # Создание товара
        cur.execute("""
            INSERT INTO products (
                name, description, price, sku, category_id, 
                brand_id, stock, is_published, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            form.name.data,
            form.description.data or '',
            float(form.price.data) if form.price.data else 0,
            form.sku.data or '',
            form.category_id.data if form.category_id.data != 0 else None,
            form.brand_id.data if form.brand_id.data != 0 else None,
            int(form.stock.data) if form.stock.data else 0,
            form.is_published.data
        ))
        
        product_id = cur.fetchone()['id']
        
        # Сохранение изображений
        _save_product_images(cur, product_id, form.images.data)
        
        cur.connection.commit()
        
        flash('Товар успешно создан!', 'success')
        return redirect(url_for('admin.products'))
        
    except Error as e:
        cur.connection.rollback()
        flash('Ошибка при создании товара', 'danger')
        return redirect(url_for('admin.create_product'))


def _save_product_images(cur, product_id, images_data):
    """Сохранить изображения товара"""
    if not images_data:
        return
    
    for i, image_file in enumerate(images_data):
        if image_file and image_file.filename:
            # Создание директории
            upload_dir = os.path.join('static', 'uploads', 'products')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Сохранение файла
            filename = secure_filename(f"{product_id}_{i}_{image_file.filename}")
            filepath = os.path.join(upload_dir, filename)
            image_file.save(filepath)
            
            # Сохранение в БД
            db_url = f"/static/uploads/products/{filename}"
            is_main = (i == 0)
            
            cur.execute("""
                INSERT INTO product_images (product_id, image_url, is_main, sort_order)
                VALUES (%s, %s, %s, %s)
            """, (product_id, db_url, is_main, i))


@login_required
@admin_required
def edit_product(product_id):
    """Редактирование товара"""
    try:
        cur = get_cursor()
        
        # Получение данных для формы
        categories = _get_categories(cur)
        brands = _get_brands(cur)
        
        form = ProductForm()
        form.category_id.choices = [(0, 'Без категории')] + [(c['id'], c['name']) for c in categories]
        form.brand_id.choices = [(0, 'Без бренда')] + [(b['id'], b['name']) for b in brands]
        
        if request.method == 'GET':
            product_data = _get_product_data(cur, product_id)
            if not product_data:
                flash('Товар не найден', 'danger')
                return redirect(url_for('admin.products'))
            
            # Заполнение формы
            product = product_data['product']
            form.name.data = product['name']
            form.description.data = product['description'] or ''
            form.price.data = str(product['price']) if product['price'] else '0'
            form.sku.data = product['sku'] or ''
            form.category_id.data = product['category_id'] or 0
            form.brand_id.data = product['brand_id'] or 0
            form.stock.data = str(product['stock']) if product['stock'] else '0'
            form.is_published.data = product['is_published']
            
            # Атрибуты
            attributes = product_data['attributes']
            form.color.data = attributes.get('color', '')
            form.material.data = attributes.get('material', '')
            form.gender.data = attributes.get('gender', '')
            
            # Размеры
            sizes = product_data['sizes']
            form.sizes.data = ', '.join(sizes)
            
            product_info = {
                'id': product['id'],
                'images': product_data['images']
            }
            
            return render_template('admin/product_form.html',
                                 form=form,
                                 product=product_info,
                                 title="Редактирование товара")
        
        if form.validate_on_submit():
            return _handle_product_update(cur, form, product_id)
        
        flash('Пожалуйста, исправьте ошибки в форме', 'danger')
        return render_template('admin/product_form.html',
                             form=form,
                             product=None,
                             title="Редактирование товара")
                             
    except Error as e:
        flash('Ошибка при загрузке товара', 'danger')
        return redirect(url_for('admin.products'))


def _get_product_data(cur, product_id):
    """Получить данные товара"""
    # Основная информация о товаре
    cur.execute("""
        SELECT id, name, description, price, sku, category_id, 
               brand_id, stock, is_published
        FROM products 
        WHERE id = %s
    """, (product_id,))
    
    product_row = cur.fetchone()
    if not product_row:
        return None
    
    # Атрибуты товара
    cur.execute("""
        SELECT attribute_type, value 
        FROM product_attributes 
        WHERE product_id = %s
    """, (product_id,))
    
    attributes = {}
    for attr in cur.fetchall():
        attributes[attr['attribute_type']] = attr['value']
    
    # Размеры товара
    cur.execute("SELECT size FROM product_sizes WHERE product_id = %s", (product_id,))
    sizes = [size['size'] for size in cur.fetchall()]
    
    # Изображения товара
    cur.execute("""
        SELECT id, image_url, is_main, sort_order 
        FROM product_images 
        WHERE product_id = %s 
        ORDER BY sort_order
    """, (product_id,))
    
    images = []
    for img in cur.fetchall():
        images.append({
            'id': img['id'],
            'url': img['image_url'],
            'is_main': img['is_main'],
            'sort_order': img['sort_order']
        })
    
    return {
        'product': dict(product_row),
        'attributes': attributes,
        'sizes': sizes,
        'images': images
    }


def _handle_product_update(cur, form, product_id):
    """Обработать обновление товара"""
    try:
        # Обновление товара
        cur.execute("""
            UPDATE products 
            SET name = %s, description = %s, price = %s, sku = %s, 
                category_id = %s, brand_id = %s, stock = %s, 
                is_published = %s, updated_at = NOW()
            WHERE id = %s
        """, (
            form.name.data,
            form.description.data or '',
            float(form.price.data) if form.price.data else 0,
            form.sku.data or '',
            form.category_id.data if form.category_id.data != 0 else None,
            form.brand_id.data if form.brand_id.data != 0 else None,
            int(form.stock.data) if form.stock.data else 0,
            form.is_published.data,
            product_id
        ))
        
        # Обновление атрибутов
        _update_product_attributes(cur, product_id, form)
        
        # Обновление изображений
        _update_product_images(cur, product_id, form.images.data)
        
        # Обновление размеров
        _update_product_sizes(cur, product_id, form)
        
        cur.connection.commit()
        
        flash('Товар успешно обновлен!', 'success')
        return redirect(url_for('admin.products'))
        
    except Error as e:
        cur.connection.rollback()
        flash('Ошибка при обновлении товара', 'danger')
        return redirect(url_for('admin.edit_product', product_id=product_id))


def _update_product_attributes(cur, product_id, form):
    """Обновить атрибуты товара"""
    cur.execute("DELETE FROM product_attributes WHERE product_id = %s", (product_id,))
    
    attributes = [
        ('color', form.color.data),
        ('material', form.material.data),
        ('gender', form.gender.data)
    ]
    
    for attr_type, value in attributes:
        if value:
            cur.execute("""
                INSERT INTO product_attributes (product_id, attribute_type, value)
                VALUES (%s, %s, %s)
            """, (product_id, attr_type, value))


def _update_product_images(cur, product_id, images_data):
    """Обновить изображения товара"""
    if not images_data:
        return
    
    # Получение максимального order
    cur.execute("SELECT COALESCE(MAX(sort_order), -1) FROM product_images WHERE product_id = %s", (product_id,))
    max_order = cur.fetchone()['coalesce']
    
    for i, image_file in enumerate(images_data):
        if image_file and image_file.filename:
            upload_dir = os.path.join('static', 'uploads', 'products')
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = secure_filename(f"{product_id}_{max_order + i + 1}_{image_file.filename}")
            filepath = os.path.join(upload_dir, filename)
            image_file.save(filepath)
            
            db_url = f"/static/uploads/products/{filename}"
            
            cur.execute("""
                INSERT INTO product_images (product_id, image_url, is_main, sort_order)
                VALUES (%s, %s, %s, %s)
            """, (product_id, db_url, False, max_order + i + 1))


def _update_product_sizes(cur, product_id, form):
    """Обновить размеры товара"""
    cur.execute("DELETE FROM product_sizes WHERE product_id = %s", (product_id,))
    
    if form.sizes.data:
        size_list = [s.strip() for s in form.sizes.data.split(',') if s.strip()]
        stock = int(form.stock.data) if form.stock.data else 0
        for size in size_list:
            cur.execute("""
                INSERT INTO product_sizes (product_id, size, quantity)
                VALUES (%s, %s, %s)
            """, (product_id, size, stock))


@login_required
@admin_required
def delete_product(product_id):
    """Удаление товара"""
    try:
        cur = get_cursor()
        
        # Проверка существования товара
        cur.execute("SELECT name FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        
        if not product:
            flash('Товар не найден', 'danger')
            return redirect(url_for('admin.products'))
        
        # Удаление товара
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        cur.connection.commit()
        
        flash(f'Товар "{product["name"]}" успешно удален!', 'success')
        return redirect(url_for('admin.products'))
        
    except Error as e:
        flash('Ошибка при удалении товара', 'danger')
        return redirect(url_for('admin.products'))