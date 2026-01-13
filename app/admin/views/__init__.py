"""
Инициализация представлений
"""

from .dashboard import dashboard
from .users import users, edit_user, delete_user
from .products import products, create_product, edit_product, delete_product
from .categories import admin_categories, create_category, edit_category, delete_category
from .brands import admin_brands, create_brand, edit_brand, delete_brand
from .export_import import (
    export_data, download_export, generate_export, delete_export, quick_export,
    import_data, download_import_template, upload_import, view_import_errors, preview_import
)

__all__ = [
    'dashboard',
    'users', 'edit_user', 'delete_user',
    'products', 'create_product', 'edit_product', 'delete_product',
    'admin_categories', 'create_category', 'edit_category', 'delete_category',
    'admin_brands', 'create_brand', 'edit_brand', 'delete_brand',
    'export_data', 'download_export', 'generate_export', 'delete_export', 'quick_export',
    'import_data', 'download_import_template', 'upload_import', 'view_import_errors', 'preview_import'
]
