from app.extensions import db
from datetime import datetime


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(500))
    pub_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    brand_id = db.Column(db.Integer, db.ForeignKey('shop_brand.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    seller = db.relationship('app.models.user.User', backref='products')
    brand = db.relationship('app.models.brand.Brand', backref='products')
    category = db.relationship('app.models.category.Category', backref='products')

    reviews = db.relationship('app.models.review.Review', backref='product', 
                              lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Product {self.name}>'
