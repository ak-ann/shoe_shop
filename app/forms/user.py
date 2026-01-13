# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
# from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError, NumberRange


# class UserEditForm(FlaskForm):
#     first_name = StringField('Имя')
#     last_name = StringField('Фамилия')
#     username = StringField('Имя пользователя',
#                            validators=[DataRequired(), Length(min=3, max=150)])
#     email = StringField('Email',
#                         validators=[DataRequired(), Email()])
#     phone = StringField('Телефон')
#     address = TextAreaField('Адрес')
#     current_password = PasswordField('Текущий пароль',
#                                      validators=[DataRequired()])
#     new_password = PasswordField('Новый пароль',
#                                  validators=[Optional(), Length(min=6)])
#     submit = SubmitField('Сохранить')


# class ReviewForm(FlaskForm):
#     text = TextAreaField('Отзыв', validators=[DataRequired()])
#     rating = IntegerField('Оценка (1–5)',
#                           validators=[DataRequired(), NumberRange(min=1, max=5)])


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError, NumberRange
from flask_login import current_user
from app.database import get_cursor


class UserEditForm(FlaskForm):
    first_name = StringField('Имя', validators=[Optional()])
    last_name = StringField('Фамилия', validators=[Optional()])
    username = StringField(
        'Имя пользователя',
        validators=[DataRequired(), Length(min=3, max=150)]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    phone = StringField('Телефон', validators=[Optional()])
    address = TextAreaField('Адрес', validators=[Optional()])
    current_password = PasswordField(
        'Текущий пароль',
        validators=[DataRequired()]
    )
    new_password = PasswordField(
        'Новый пароль',
        validators=[Optional(), Length(min=6)]
    )
    submit = SubmitField('Сохранить')
    
    def validate_username(self, field):
        """Проверка уникальности username"""
        if field.data == current_user.username:
            return  # Это текущее имя пользователя
        
        with get_cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE username = %s AND id != %s",
                (field.data, current_user.id)
            )
            if cur.fetchone():
                raise ValidationError('Это имя пользователя уже занято')
    
    def validate_email(self, field):
        """Проверка уникальности email"""
        if field.data == current_user.email:
            return  # Это текущий email
        
        with get_cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                (field.data, current_user.id)
            )
            if cur.fetchone():
                raise ValidationError('Этот email уже зарегистрирован')


class ReviewForm(FlaskForm):
    text = TextAreaField('Отзыв', validators=[DataRequired()])
    rating = IntegerField(
        'Оценка (1–5)',
        validators=[DataRequired(), NumberRange(min=1, max=5)]
    )
    submit = SubmitField('Оставить отзыв')