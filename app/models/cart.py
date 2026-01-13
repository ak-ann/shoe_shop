from app.extensions import db
from datetime import datetime


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='cart_items')
    user = db.relationship('User', backref='cart_items')

    def __repr__(self):
        return f'<CartItem {self.product_id} x{self.quantity}>'

    @property
    def total_price(self):
        if self.product and self.product.price:
            return float(self.product.price) * self.quantity
        return 0.0
