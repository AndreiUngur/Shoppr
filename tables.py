from utils import db


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), index=True, unique=True)
    price = db.Column(db.Float)
    inventory_count = db.Column(db.Integer)
    cartitems = db.relationship("CartItem", backref="products", lazy=True)

    def __repr__(self):
        return '<Product %r>' % self.title


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    created_date = db.Column(db.DateTime)
    carts = db.relationship("CartItem", backref="carts", lazy=True)

    def __repr__(self):
        return '<Cart %r>' % self.id


class CartItem(db.Model):
    __tablename__ = "cartitems"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'))
    quantity = db.Column(db.Integer)
