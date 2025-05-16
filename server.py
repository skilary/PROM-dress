from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Product, User, Order
import os
import json

app = Flask(__name__)
app.secret_key = "secret-key"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'bestdress.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

#загрузка, обновление json
def setup():
    db.create_all()
    if Product.query.count() == 0:
        with open(os.path.join(basedir, 'products.json'), 'r', encoding='utf-8') as f:
            products_data = json.load(f)
            for item in products_data:
                sizes = item.get('sizes', [])
                if isinstance(sizes, list):
                    sizes = ",".join(sizes)
                product = Product(
                    id=item.get('id'),
                    photo=item.get('photo'),
                    name=item.get('name'),
                    price=item.get('price'),
                    material=item.get('material'),
                    sizes=sizes
                )
                db.session.add(product)
            db.session.commit()

# определение сессии(активна или нет)
def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# Определение маршрутов (routes)
@app.route('/')
@app.route('/products')
def products():
    prods = Product.query.all()
    user = current_user()
    return render_template('index.html', products=prods, user=user)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    user = current_user()
    return render_template('product_detail.html', product=product, user=user)

# регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        if User.query.filter_by(phone=phone).first():
            flash("Пользователь с таким номером телефона уже существует.")
            return redirect(url_for('register'))
        new_user = User(phone=phone, password=password, balance=0)
        db.session.add(new_user)
        db.session.commit()
        flash("Регистрация прошла успешно. Теперь вы можете войти.")
        return redirect(url_for('login'))
    return render_template('register.html')

# вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        user = User.query.filter_by(phone=phone, password=password).first()
        if user:
            session['user_id'] = user.id
            flash("Вход выполнен успешно!")
            return redirect(url_for('products'))
        else:
            flash("Неверный номер телефона или пароль.")
    return render_template('login.html')

# выход
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Вы вышли из аккаунта.")
    return redirect(url_for('products'))

# пополнение счёта
@app.route('/account', methods=['GET', 'POST'])
def account():
    user = current_user()
    if not user:
        flash("Для доступа к аккаунту необходимо войти.")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        try:
            amount = float(amount)
            if amount > 0:
                user.balance += amount
                db.session.commit()
                flash("Счет успешно пополнен!")
            else:
                flash("Введите положительную сумму.")
        except ValueError:
            flash("Введите корректное число.")
            
    return render_template('account.html', user=user)


# корзина
@app.route('/cart')
def cart():
    user = current_user()
    if not user:
        flash("Для доступа к корзине необходимо войти.")
        return redirect(url_for('login'))
    return render_template('cart.html', user=user)


# добавление товара
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    user = current_user()
    if not user:
        flash("Для добавления в корзину необходимо войти.")
        return redirect(url_for('login'))
    product = Product.query.get_or_404(product_id)
    if product not in user.cart:
        user.cart.append(product)
        db.session.commit()
        flash("Товар добавлен в корзину!")
    else:
        flash("Товар уже добавлен в корзину.")
    return redirect(url_for('cart'))


# попытка покупки
@app.route('/checkout')
def checkout():
    user = current_user()
    if not user:
        flash("Для оформления заказа необходимо войти.")
        return redirect(url_for('login'))
    if not user.cart:
        flash("В корзине нет товаров.")
        return redirect(url_for('cart'))
    
    total = sum(p.price for p in user.cart)
    if user.balance < total:
        flash("Недостаточно средств для оформления заказа. Пополните счет.")
        return redirect(url_for('account'))
    
    user.balance -= total
    new_order = Order(user_id=user.id, total=total)
    # копия списка товаров
    new_order.products = user.cart[:]
    db.session.add(new_order)
    # очищаем корзину
    user.cart = []
    db.session.commit()
    flash("Заказ оформлен успешно!")
    return redirect(url_for('account'))

if __name__ == '__main__':
    with app.app_context():
        # выполнение инициализации перед запуском сервера
        setup()
    app.run(debug=True)
