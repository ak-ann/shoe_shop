# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField
# from wtforms.validators import DataRequired, Email, Length, EqualTo


# class RegistrationForm(FlaskForm):
#     username = StringField('Имя пользователя',
#                            validators=[DataRequired(), Length(min=3, max=150)])
#     email = StringField('Email',
#                         validators=[DataRequired(), Email()])
#     password = PasswordField('Пароль',
#                              validators=[DataRequired(), Length(min=8)])
#     confirm_password = PasswordField('Подтвердите пароль',
#                                      validators=[DataRequired(), EqualTo('password')])


# class LoginForm(FlaskForm):
#     username = StringField('Имя пользователя', validators=[DataRequired()])
#     password = PasswordField('Пароль', validators=[DataRequired()])

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.database import get_cursor


class RegistrationForm(FlaskForm):
    username = StringField(
        'Имя пользователя',
        validators=[DataRequired(), Length(min=3, max=150)]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Пароль',
        validators=[DataRequired(), Length(min=8)]
    )
    confirm_password = PasswordField(
        'Подтвердите пароль',
        validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, field):
        """Проверка уникальности username"""
        with get_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (field.data,))
            if cur.fetchone():
                raise ValidationError('Это имя пользователя уже занято')
    
    def validate_email(self, field):
        """Проверка уникальности email"""
        with get_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (field.data,))
            if cur.fetchone():
                raise ValidationError('Этот email уже зарегистрирован')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')