from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager


mail = Mail()
login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()

login_manager.login_view = 'users.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'info'

from app.models.user import User

@login_manager.user_loader
def load_user(user_id):
    """Функция загрузки пользователя для Flask-Login"""
    return User.get_by_id(user_id)
