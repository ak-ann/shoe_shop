from flask import Blueprint
from flask_login import login_required

from .decorators import admin_required
from .views import (
    dashboard,
    users, edit_user, delete_user,
    products, create_product, edit_product, delete_product,
    admin_categories, create_category, edit_category, delete_category,
    admin_brands, create_brand, edit_brand, delete_brand,
    export_data, download_export, generate_export, delete_export, quick_export,
    import_data, download_import_template, upload_import, view_import_errors, preview_import
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Дашборд
admin_bp.route('/')(login_required(admin_required(dashboard)))

# Пользователи
admin_bp.route('/users')(login_required(admin_required(users)))

admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])(
    login_required(admin_required(edit_user))
)
admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])(
    login_required(admin_required(delete_user))
)

# Товары
admin_bp.route('/products')(login_required(admin_required(products)))

admin_bp.route('/products/create', methods=['GET', 'POST'])(
    login_required(admin_required(create_product))
)
admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])(
    login_required(admin_required(edit_product))
)
admin_bp.route('/products/<int:id>/delete', methods=['POST'])(
    login_required(admin_required(delete_product))
)

# Категории
admin_bp.route('/categories')(login_required(admin_required(admin_categories)))
admin_bp.route('/categories/create', methods=['GET', 'POST'])(
    login_required(admin_required(create_category))
)
admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])(
    login_required(admin_required(edit_category))
)
admin_bp.route('/categories/delete', methods=['POST'])(
    login_required(admin_required(delete_category))
)

# Бренды
admin_bp.route('/brands')(login_required(admin_required(admin_brands)))

admin_bp.route('/brands/create', methods=['GET', 'POST'])(
    login_required(admin_required(create_brand))
)
admin_bp.route('/brands/<int:brand_id>/edit', methods=['GET', 'POST'])(
    login_required(admin_required(edit_brand))
)
admin_bp.route('/brands/<int:brand_id>/delete', methods=['POST'])(
    login_required(admin_required(delete_brand))
)

# Экспорт
admin_bp.route('/export')(login_required(admin_required(export_data)))
admin_bp.route('/export/download/<filename>')(
    login_required(admin_required(download_export))
)
admin_bp.route('/export/generate', methods=['POST'])(
    login_required(admin_required(generate_export))
)
admin_bp.route('/export/delete/<filename>', methods=['POST'])(
    login_required(admin_required(delete_export))
)
admin_bp.route('/api/export/quick', methods=['POST'])(
    login_required(admin_required(quick_export))
)

# Импорт
admin_bp.route('/import')(login_required(admin_required(import_data)))
admin_bp.route('/import/template/<template_type>')(
    login_required(admin_required(download_import_template))
)
admin_bp.route('/import/upload', methods=['POST'])(
    login_required(admin_required(upload_import))
)
admin_bp.route('/import/errors')(
    login_required(admin_required(view_import_errors))
)
admin_bp.route('/import/preview', methods=['POST'])(
    login_required(admin_required(preview_import))
)
