"""
Управление категориями
"""

from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required
import re
from ..decorators import admin_required
from app.database import get_cursor


def generate_slug(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9а-яё]+', '-', slug).strip('-')
    return slug


@login_required
@admin_required
def admin_categories():
    """Список категорий"""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT c.id, c.name, c.slug, c.description, c.created_at,
                   COALESCE(p.product_count, 0) as product_count
            FROM categories c
            LEFT JOIN (
                SELECT category_id, COUNT(*) as product_count
                FROM products
                GROUP BY category_id
            ) p ON c.id = p.category_id
            ORDER BY c.name
        """)
        categories = cur.fetchall()
        return render_template("admin/categories.html", categories=categories)

    except Exception as e:
        flash(f"Ошибка при загрузке категорий: {e}", "danger")
        return render_template("admin/categories.html", categories=[])


@login_required
@admin_required
def create_category():
    """Создание категории"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Название категории обязательно", "danger")
            return render_template("admin/category_form.html")

        if not slug:
            slug = generate_slug(name)

        try:
            cur = get_cursor()
            # Проверка уникальности slug
            cur.execute("SELECT id FROM categories WHERE slug = %s", (slug,))
            if cur.fetchone():
                flash("Категория с таким URL уже существует", "danger")
                return render_template("admin/category_form.html")

            cur.execute("""
                INSERT INTO categories (name, slug, description, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (name, slug, description))

            cur.connection.commit()
            flash(f'Категория "{name}" успешно создана', "success")
            return redirect(url_for("admin.admin_categories"))

        except Exception as e:
            flash(f"Ошибка при создании категории: {e}", "danger")

    return render_template("admin/category_form.html")


@login_required
@admin_required
def edit_category(category_id):
    """Редактирование категории"""
    try:
        cur = get_cursor()

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            slug = request.form.get("slug", "").strip()
            description = request.form.get("description", "").strip()

            if not name:
                flash("Название категории обязательно", "danger")
                return redirect(url_for("admin.edit_category", category_id=category_id))

            if not slug:
                slug = generate_slug(name)

            # Проверка уникальности slug для других категорий
            cur.execute(
                "SELECT id FROM categories WHERE slug = %s AND id != %s",
                (slug, category_id)
                )
            if cur.fetchone():
                flash("Категория с таким URL уже существует", "danger")
                return redirect(url_for("admin.edit_category", category_id=category_id))

            cur.execute("""
                UPDATE categories
                SET name = %s, slug = %s, description = %s, updated_at = NOW()
                WHERE id = %s
            """, (name, slug, description, category_id))

            cur.connection.commit()
            flash("Категория успешно обновлена", "success")
            return redirect(url_for("admin.admin_categories"))

        # Получение категории для формы
        cur.execute(
            "SELECT id, name, slug, description FROM categories WHERE id = %s",
            (category_id,)
            )
        category = cur.fetchone()
        if not category:
            flash("Категория не найдена", "danger")
            return redirect(url_for("admin.admin_categories"))

        return render_template("admin/category_form.html", category=dict(category))

    except Exception as e:
        flash(f"Ошибка при редактировании категории: {e}", "danger")
        return redirect(url_for("admin.admin_categories"))


@login_required
@admin_required
def delete_category():
    """Удаление категории через JSON или форму"""
    try:
        if request.is_json:
            data = request.get_json()
            category_id = data.get("id")
        else:
            category_id = request.form.get("id")

        if not category_id:
            if request.is_json:
                return jsonify({
                    "success": False,
                    "message": "ID категории не указан"
                })
            else:
                flash("ID категории не указан", "danger")
                return redirect(url_for("admin.admin_categories"))

        cur = get_cursor()

        cur.execute("SELECT COUNT(*) as cnt FROM products WHERE category_id = %s", (category_id,))
        result = cur.fetchone()

        if result and result['cnt'] > 0:
            if request.is_json:
                return jsonify({
                    "success": False,
                    "message": "Нельзя удалить категорию с товарами"
                    })
            else:
                flash("Нельзя удалить категорию с товарами", "danger")
                return redirect(url_for("admin.admin_categories"))

        cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        cur.connection.commit()

        if request.is_json:
            return jsonify({
                "success": True,
                "message": "Категория успешно удалена"
                })
        else:
            flash("Категория успешно удалена", "success")
            return redirect(url_for("admin.admin_categories"))

    except Exception as e:
        if request.is_json:
            return jsonify({
                "success": False,
                "message": f"Ошибка при удалении: {str(e)}"
                })
        else:
            flash(f"Ошибка при удалении категории: {e}", "danger")
            return redirect(url_for("admin.admin_categories"))
