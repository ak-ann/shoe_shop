from flask_login import login_required

from . import shop_bp
from .views import (
    index as views_index,
    product_detail,
    categories_list,
    category_products as views_category_products,
    brands_list,
    cart,
    update_cart_quantity,
    add_to_cart,
    remove_from_cart,
    clear_cart,
    cart_status,
    checkout,
    api_get_cart,
    api_checkout,
    order_success,
    download_receipt,
    add_review,
    edit_review,
    delete_review
)


# Главная страница
@shop_bp.route('/')
@shop_bp.route('/shop')
def index():
    return views_index()


# Товары
@shop_bp.route('/product/<int:product_id>')
def product_detail_route(product_id):
    return product_detail(product_id)


# Категории
@shop_bp.route('/categories')
def categories():
    return categories_list()


@shop_bp.route('/category/<slug>')
def category_products_route(slug):
    return views_category_products(slug)


# Бренды
@shop_bp.route('/brands')
def brands():
    return brands_list()


# Корзина
@shop_bp.route('/cart')
@login_required
def cart_route():
    return cart()


@shop_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart_route(product_id):
    return add_to_cart(product_id)


@shop_bp.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart_route(item_id):
    return remove_from_cart(item_id)


@shop_bp.route('/cart/clear')
def clear_cart_route():
    return clear_cart()


@shop_bp.route('/api/cart-status')
def cart_status_route():
    return cart_status()


@shop_bp.route('/cart/update-quantity/<int:item_id>', methods=['POST'])
@login_required
def update_cart_quantity_route(item_id):
    return update_cart_quantity(item_id)


# Оформление заказа
@shop_bp.route('/checkout')
@login_required
def checkout_route():
    return checkout()


@shop_bp.route('/api/checkout', methods=['POST'])
@login_required
def api_checkout_route():
    return api_checkout()


@shop_bp.route('/order-success/<order_number>')
@login_required
def order_success_route(order_number):
    return order_success(order_number)


@shop_bp.route('/download-receipt/<order_number>')
@login_required
def download_receipt_route(order_number):
    return download_receipt(order_number)


# Добавьте этот маршрут
@shop_bp.route('/api/cart')
@login_required
def api_cart_route():
    return api_get_cart()


# Отзывы
@shop_bp.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review_route(product_id):
    return add_review(product_id)


@shop_bp.route('/product/<int:product_id>/review/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review_route(product_id, review_id):
    return edit_review(product_id, review_id)


@shop_bp.route('/product/<int:product_id>/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review_route(product_id, review_id):
    return delete_review(product_id, review_id)
