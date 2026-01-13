# from flask_wtf import FlaskForm
# from flask_wtf.file import FileField, FileAllowed, MultipleFileField
# from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField
# from wtforms.validators import DataRequired, Optional, NumberRange


# class ProductForm(FlaskForm):
#     name = StringField('Название товара', validators=[DataRequired()])
#     description = TextAreaField('Описание', validators=[Optional()])
#     price = FloatField('Цена', validators=[DataRequired(), NumberRange(min=0)])
#     sku = StringField('Артикул (SKU)', validators=[Optional()])

#     category_id = SelectField('Категория', coerce=int, choices=[], validators=[Optional()])
#     brand_id = SelectField('Бренд', coerce=int, choices=[], validators=[Optional()])

#     stock = IntegerField('Количество на складе', validators=[DataRequired(), NumberRange(min=0)])
#     is_published = BooleanField('Опубликовать', default=True)

#     color = StringField('Цвет', validators=[Optional()])
#     material = StringField('Материал', validators=[Optional()])

#     gender = SelectField('Пол', choices=[
#         ('', 'Не указано'),
#         ('male', 'Мужской'),
#         ('female', 'Женский'),
#         ('unisex', 'Унисекс')
#     ], validators=[Optional()])

#     sizes = StringField('Размеры (через запятую)', validators=[Optional()])

#     images = MultipleFileField('Изображения товара', validators=[
#         Optional(),
#         FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
#     ])

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import (
    StringField, TextAreaField, FloatField, IntegerField,
    SelectField, BooleanField, SubmitField
)
from wtforms.validators import DataRequired, Optional, NumberRange


class ProductForm(FlaskForm):
    name = StringField('Название товара', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[Optional()])
    price = FloatField(
        'Цена',
        validators=[DataRequired(), NumberRange(min=0)]
    )
    sku = StringField('Артикул (SKU)', validators=[Optional()])
    category_id = SelectField(
        'Категория',
        coerce=int,
        choices=[],
        validators=[Optional()]
    )
    brand_id = SelectField(
        'Бренд',
        coerce=int,
        choices=[],
        validators=[Optional()]
    )
    stock = IntegerField(
        'Количество на складе',
        validators=[DataRequired(), NumberRange(min=0)]
    )
    is_published = BooleanField('Опубликовать', default=True)
    color = StringField('Цвет', validators=[Optional()])
    material = StringField('Материал', validators=[Optional()])
    gender = SelectField(
        'Пол',
        choices=[
            ('', 'Не указано'),
            ('male', 'Мужской'),
            ('female', 'Женский'),
            ('unisex', 'Унисекс')
        ],
        validators=[Optional()]
    )
    sizes = StringField('Размеры (через запятую)', validators=[Optional()])
    images = MultipleFileField(
        'Изображения товара',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
        ]
    )
    submit = SubmitField('Сохранить')
    
    def __init__(self, categories=None, brands=None, *args, **kwargs):
        """Инициализация с передачей списков категорий и брендов"""
        super().__init__(*args, **kwargs)
        
        # Настройка категорий
        if categories is None:
            categories = []
        self.category_id.choices = [(0, '-- Выберите категорию --')]
        self.category_id.choices.extend([
            (cat['id'], cat['name']) for cat in categories
        ])

        if brands is None:
            brands = []
        self.brand_id.choices = [(0, '-- Выберите бренд --')]
        self.brand_id.choices.extend([
            (brand['id'], brand['name']) for brand in brands
        ])