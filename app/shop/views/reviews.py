"""
Представления для работы с отзывами
"""
from flask import render_template, request, redirect, url_for, flash, abort, g
from flask_login import current_user, login_required
from app.database import get_cursor, get_db_connection


@login_required
def add_review(product_id):
    """Добавление отзыва к товару"""
    try:
        comment = request.form.get('comment', '').strip()
        rating = request.form.get('rating', '5')

        if not comment:
            flash('Введите текст отзыва', 'error')
            return redirect(url_for('shop.product_detail_route', product_id=product_id))

        if len(comment) < 10:
            flash('Отзыв должен содержать минимум 10 символов', 'error')
            return redirect(url_for('shop.product_detail_route', product_id=product_id))

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                flash('Оценка должна быть от 1 до 5', 'error')
                return redirect(url_for('shop.product_detail_route', product_id=product_id))
        except (ValueError, TypeError):
            flash('Некорректная оценка', 'error')
            return redirect(url_for('shop.product_detail_route', product_id=product_id))

        cursor = get_cursor()
        if not cursor:
            flash('Ошибка подключения к базе данных', 'error')
            return redirect(url_for('shop.product_detail_route', product_id=product_id))

        cursor.execute("""
            SELECT id FROM reviews
            WHERE product_id = %s AND user_id = %s
        """, (product_id, current_user.id))

        existing_review = cursor.fetchone()

        if existing_review:
            cursor.close()
            flash('Вы уже оставляли отзыв на этот товар.', 'warning')
            return redirect(url_for('shop.product_detail_route', product_id=product_id))

        cursor.execute("""
            INSERT INTO reviews (comment, rating, product_id, user_id, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id
        """, (comment, rating, product_id, current_user.id))

        cursor.fetchone()

        if hasattr(g, 'db') and g.db:
            g.db.commit()
        else:
            cursor.connection.commit()

        cursor.close()

        flash('Отзыв успешно добавлен!', 'success')

    except Exception as e:
        try:
            if hasattr(g, 'db') and g.db:
                g.db.rollback()
        except:
            pass

        flash('Ошибка при добавлении отзыва', 'error')

    return redirect(url_for('shop.product_detail_route', product_id=product_id))


@login_required
def edit_review(product_id, review_id):
    """Редактирование отзыва"""
    connection = get_db_connection()
    if not connection:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('shop.product_detail_route', product_id=product_id))

    try:
        from psycopg2.extras import DictCursor
        cursor = connection.cursor(cursor_factory=DictCursor)

        cursor.execute("""
            SELECT r.*, u.username AS author_name
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = %s
        """, (review_id,))

        review = cursor.fetchone()

        if not review:
            flash('Отзыв не найден', 'error')
            return redirect(url_for('shop.product_detail_route', product_id=product_id))

        if review['user_id'] != current_user.id and not current_user.is_admin:
            abort(403)

        if request.method == 'POST':
            text = request.form.get('text', '').strip()
            rating = request.form.get('rating', '5')

            if not text or len(text) < 10:
                flash('Отзыв должен содержать минимум 10 символов', 'error')
                return render_template('shop/edit_review.html',
                                       review=review,
                                       product_id=product_id,
                                       comment=text,
                                       rating=int(rating) if rating.isdigit() else 5)

            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    flash('Оценка должна быть от 1 до 5', 'error')
                    return render_template('shop/edit_review.html',
                                           review=review,
                                           product_id=product_id,
                                           comment=text,
                                           rating=rating)
            except ValueError:
                flash('Некорректная оценка', 'error')
                return render_template('shop/edit_review.html',
                                       review=review,
                                       product_id=product_id,
                                       comment=text,
                                       rating=5)

            cursor.execute("""
                UPDATE reviews SET
                comment = %s, rating = %s
                WHERE id = %s
            """, (text, rating, review_id))

            connection.commit()
            flash('Отзыв обновлен!', 'success')
            return redirect(url_for('shop.product_detail_route', product_id=product_id))

        return render_template('shop/edit_review.html',
                               review=review,
                               product_id=product_id,
                               comment=review['comment'],
                               rating=review['rating'])

    except Exception as e:
        flash('Произошла ошибка', 'error')
        return redirect(url_for('shop.product_detail_route', product_id=product_id))

    finally:
        if connection:
            connection.close()


@login_required
def delete_review(product_id, review_id):
    """Удаление отзыва"""
    connection = get_db_connection()
    if not connection:
        flash('Ошибка подключения к базе данных', 'error')
        return redirect(url_for('shop.product_detail_route', product_id=product_id))

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT user_id FROM reviews WHERE id = %s", (review_id,))
        review = cursor.fetchone()

        if not review:
            flash('Отзыв не найден', 'error')
            return redirect(url_for('shop.product_detail_route', product_id=product_id))

        if review['user_id'] != current_user.id and not current_user.is_admin:
            abort(403)

        cursor.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
        connection.commit()
        flash('Отзыв удален!', 'success')

    except Exception as e:
        connection.rollback()
        flash('Ошибка при удалении отзыва', 'error')

    finally:
        if connection:
            connection.close()

    return redirect(url_for('shop.product_detail_route', product_id=product_id))