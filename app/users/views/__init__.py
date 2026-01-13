# Аутентификация
from .auth import (
    register_view,
    verify_email_view,
    resend_verification_view,
    login_view,
    logout_view
)

# Профиль
from .profile import (
    profile_view,
    edit_profile_view
)

# Товары
from .products import my_products_view

# Админ-панель
from .admin import (
    admin_panel_view,
    admin_users_view,
    edit_user_view,
    delete_user_view
)

__all__ = [
    # Аутентификация
    'register_view',
    'verify_email_view',
    'resend_verification_view',
    'login_view',
    'logout_view',
    
    # Профиль
    'profile_view',
    'edit_profile_view',
    
    # Товары
    'my_products_view',
    
    # Админ-панель
    'admin_panel_view',
    'admin_users_view',
    'edit_user_view',
    'delete_user_view'
]