# from flask_wtf import FlaskForm
# from wtforms import StringField, TextAreaField, SelectField, BooleanField
# from wtforms.validators import DataRequired, Optional, Length
# from app.models import Category


# class CategoryForm(FlaskForm):
#     name = StringField('Название категории', validators=[DataRequired(), Length(max=100)])
#     description = TextAreaField('Описание')
#     slug = StringField('URL-адрес (slug)', validators=[DataRequired(), Length(max=100)])
#     parent_id = SelectField('Родительская категория', coerce=int, validators=[Optional()])
#     is_published = BooleanField('Опубликовано', default=True)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.parent_id.choices = [(0, '--- Нет (основная категория) ---')] + \
#             [(c.id, c.name) for c in Category.query.all()]


# class BrandForm(FlaskForm):
#     name = StringField('Название бренда', validators=[DataRequired(), Length(max=256)])
#     description = TextAreaField('Описание')
#     is_published = BooleanField('Опубликовано', default=True)


from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


class CategoryForm(FlaskForm):
    name = StringField(
        'Название категории',
        validators=[DataRequired(), Length(max=100)]
    )
    description = TextAreaField('Описание', validators=[Optional()])
    slug = StringField(
        'URL-адрес (slug)',
        validators=[DataRequired(), Length(max=100)]
    )
    parent_id = SelectField(
        'Родительская категория',
        coerce=int,
        validators=[Optional()],
        choices=[]  # Будет заполняться в view
    )
    is_published = BooleanField('Опубликовано', default=True)
    submit = SubmitField('Сохранить')
    
    def __init__(self, categories=None, *args, **kwargs):
        """Инициализация с передачей списка категорий"""
        super().__init__(*args, **kwargs)
        if categories is None:
            categories = []
        
        # Добавляем вариант "Без родительской категории"
        self.parent_id.choices = [(0, '--- Нет (основная категория) ---')]
        # Добавляем реальные категории
        self.parent_id.choices.extend([
            (cat['id'], cat['name']) for cat in categories
        ])


class BrandForm(FlaskForm):
    name = StringField(
        'Название бренда',
        validators=[DataRequired(), Length(max=256)]
    )
    description = TextAreaField('Описание', validators=[Optional()])
    is_published = BooleanField('Опубликовано', default=True)
    submit = SubmitField('Сохранить')