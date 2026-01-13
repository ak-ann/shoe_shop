"""
Маршруты статических страниц
"""
from flask import render_template
from . import pages_bp


@pages_bp.route('/about')
def about():
    """Страница "О нас" """
    return render_template('pages/about.html')
