"""
Маршруты пользователей - только определения URL
"""

from flask_login import login_required
from . import users_bp


@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация"""
    from .views.auth import register_view
    return register_view()

@users_bp.route('/verify-email/<token>')
def verify_email(token):
    """Подтверждение email"""
    from .views.auth import verify_email_view
    return verify_email_view(token)

@users_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Повторная отправка верификации"""
    from .views.auth import resend_verification_view
    return resend_verification_view()

@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вход"""
    from .views.auth import login_view
    return login_view()

@users_bp.route('/logout')
@login_required
def logout():
    """Выход"""
    from .views.auth import logout_view
    return logout_view()

# === ПРОФИЛЬ ===
@users_bp.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    """Профиль пользователя"""
    from .views.profile import profile_view
    return profile_view(username)

@users_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Редактирование профиля"""
    from .views.profile import edit_profile_view
    return edit_profile_view()

# === МОИ ТОВАРЫ ===
@users_bp.route('/my-products')
@login_required
def my_products():
    """Товары пользователя"""
    from .views.products import my_products_view
    return my_products_view()

# === АДМИН-ПАНЕЛЬ ===
@users_bp.route('/admin')
@login_required
def admin_panel():
    """Главная админ-панели"""
    from .views.admin import admin_panel_view
    return admin_panel_view()

@users_bp.route('/admin/users')
@login_required
def admin_users():
    """Управление пользователями"""
    from .views.admin import admin_users_view
    return admin_users_view()

@users_bp.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Редактирование пользователя (админ)"""
    from .views.admin import edit_user_view
    return edit_user_view(user_id)

@users_bp.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Удаление пользователя (админ)"""
    from .views.admin import delete_user_view
    return delete_user_view(user_id)