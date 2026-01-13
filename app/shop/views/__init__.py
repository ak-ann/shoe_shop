"""
Инициализация представлений магазина
"""

from .products import index, product_detail, categories_list, category_products, brands_list
from .cart import cart, update_cart_quantity, add_to_cart, remove_from_cart, clear_cart, cart_status
from .checkout import checkout, api_checkout, order_success, download_receipt, api_get_cart
from .reviews import add_review, edit_review, delete_review

__all__ = [
    'index',
    'product_detail',
    'categories_list',
    'category_products',
    'brands_list',
    'cart',
    'update_cart_quantity',
    'add_to_cart',
    'remove_from_cart',
    'clear_cart',
    'cart_status',
    'checkout',
    'api_checkout',
    'api_get_cart',
    'order_success',
    'download_receipt',
    'add_review',
    'edit_review',
    'delete_review'
]
