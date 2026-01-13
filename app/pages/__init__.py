from flask import Blueprint

pages_bp = Blueprint('pages', __name__,
                     template_folder='templates',
                     static_folder='static')

from . import routes
