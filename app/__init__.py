import os
from flask import Flask
from app.extensions import mail, login_manager
from app.database import close_db
from config import Config
from app.context_processors import cart_context, utility_context


def create_app(config_class=Config):
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static")
    )
    app.config.from_object(Config)

    # init extensions
    mail.init_app(app)
    login_manager.init_app(app)

    # database
    app.teardown_appcontext(close_db)

    # Контекстные процессоры
    app.context_processor(cart_context)
    app.context_processor(utility_context)

    # blueprints
    from app.shop import shop_bp
    from app.users import users_bp
    from app.admin import admin_bp
    from app.pages import pages_bp

    app.register_blueprint(shop_bp)
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(pages_bp)

    return app
