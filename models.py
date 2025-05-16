from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Таблица для связи «Корзина»
cart_items = db.Table('cart_items',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

# Таблица для связи «Заказы»
order_items = db.Table('order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    material = db.Column(db.String)
    # сохраняем список размеров
    sizes = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<Product {self.name}>"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    balance = db.Column(db.Float, default=0)
    cart = db.relationship('Product', secondary=cart_items, backref='users')
    orders = db.relationship('Order', backref='user')

    def __repr__(self):
        return f"<User {self.phone}>"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    products = db.relationship('Product', secondary=order_items, backref='orders')
    total = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Order {self.id} for user {self.user_id}>"
