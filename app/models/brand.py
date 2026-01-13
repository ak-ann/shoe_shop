from app.extensions import db
from datetime import datetime


class Brand(db.Model):
    __tablename__ = 'shop_brand'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='brand_products', lazy='dynamic')

    def __repr__(self):
        return f'<Brand {self.name}>'
