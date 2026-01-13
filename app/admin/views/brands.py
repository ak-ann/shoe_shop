from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required
from psycopg2 import Error

from ..decorators import admin_required
from app.database import get_cursor


def format_date(date_obj):
    """Форматирование даты для отображения"""
    if not date_obj:
        return ""
    return date_obj.strftime('%d.%m.%Y %H:%M')


@login_required
@admin_required
def admin_brands():
    """Список брендов"""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT
                b.id,
                b.name,
                b.description,
                b.is_published,
                b.created_at,
                COUNT(p.id) AS product_count
            FROM shop_brand b
            LEFT JOIN products p ON b.id = p.brand_id
            GROUP BY b.id
            ORDER BY b.name
        """)
        brands = cur.fetchall()

        result = [
            {
                "id": b["id"],
                "name": b["name"],
                "description": b["description"],
                "is_published": b["is_published"],
                "created_at": format_date(b["created_at"]),
                "product_count": b["product_count"],
            }
            for b in brands
        ]

        return render_template("admin/brands.html", brands=result)

    except Error:
        flash("Ошибка при загрузке брендов", "danger")
        return render_template("admin/brands.html", brands=[])


@login_required
@admin_required
def create_brand():
    """Создание бренда"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        is_published = "is_published" in request.form

        if not name:
            flash("Название бренда обязательно", "danger")
            return redirect(url_for("admin.create_brand"))

        try:
            cur = get_cursor()
            cur.execute("""
                INSERT INTO shop_brand (
                        name, description, is_published, created_at
                        )
                VALUES (%s, %s, %s, NOW())
            """, (name, description, is_published))

            cur.connection.commit()
            flash(f'Бренд "{name}" успешно создан', "success")
            return redirect(url_for("admin.admin_brands"))

        except Error:
            flash("Ошибка при создании бренда", "danger")

    return render_template("admin/brand_form.html", brand=None)


@login_required
@admin_required
def edit_brand(brand_id):
    """Редактирование бренда"""
    try:
        cur = get_cursor()

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            is_published = "is_published" in request.form

            if not name:
                flash("Название бренда обязательно", "danger")
                return redirect(url_for("admin.edit_brand", brand_id=brand_id))

            cur.execute("""
                UPDATE shop_brand
                SET name = %s,
                    description = %s,
                    is_published = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (name, description, is_published, brand_id))

            cur.connection.commit()
            flash("Бренд успешно обновлён", "success")
            return redirect(url_for("admin.admin_brands"))

        cur.execute("""
            SELECT id, name, description, is_published
            FROM shop_brand
            WHERE id = %s
        """, (brand_id,))
        brand = cur.fetchone()

        if not brand:
            flash("Бренд не найден", "danger")
            return redirect(url_for("admin.admin_brands"))

        return render_template("admin/brand_form.html", brand=dict(brand))

    except Error:
        flash("Ошибка при редактировании бренда", "danger")
        return redirect(url_for("admin.admin_brands"))


@login_required
@admin_required
def delete_brand(brand_id):
    """Удаление бренда"""
    try:
        cur = get_cursor()

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM products WHERE brand_id = %s",
            (brand_id,)
        )
        if cur.fetchone()["cnt"] > 0:
            flash("Нельзя удалить бренд с товарами", "danger")
            return redirect(url_for("admin.admin_brands"))

        cur.execute("DELETE FROM shop_brand WHERE id = %s", (brand_id,))
        cur.connection.commit()

        flash("Бренд удалён", "success")
        return redirect(url_for("admin.admin_brands"))

    except Error:
        flash("Ошибка при удалении бренда", "danger")
        return redirect(url_for("admin.admin_brands"))
