from flask import Blueprint

shop_bp = Blueprint('shop', __name__)

from app.shop import routes
