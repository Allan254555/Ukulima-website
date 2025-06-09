from . import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstname = db.Column(db.String(150), nullable=False)
    lastname= db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150),unique=True,nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    
    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)
   
#Employee model for employee details
class Employee(db.Model, UserMixin):
    employeeId = db.Column(db.Integer,primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey(User.id),nullable=False,unique=True)
    hireDate = db.Column(db.Date, nullable=False)
    
#category model for product category
class Category(db.Model):
    categoryId = db.Column(db.Integer,primary_key=True, autoincrement=True)
    name=db.Column(db.String(100),unique=True, nullable=False)
    image_url=db.Column(db.String(255), nullable=True)
    
    products = db.relationship('Product',backref='category',lazy=True,cascade="all,delete-orphan")
    
    
#Product model for the product category
class Product(db.Model):
    productsID = db.Column(db.Integer,primary_key=True, autoincrement=True)
    categoryId = db.Column(db.Integer, db.ForeignKey('category.categoryId'),nullable=False)
    productName =db.Column(db.String(100),unique=True,nullable=False)
    price = db.Column(db.Float,nullable=False)
    productDescription = db.Column(db.String(255),nullable=False)
    image_url = db.Column(db.String(255))
    quantity =db.Column(db.Integer)
    
class Orders(db.Model):
    orderID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    total_amount = db.Column(db.Numeric(10,2), nullable=False)
    
    delivery_fee = db.Column(db.Numeric(10, 2), nullable=False)  # ✅ delivery fee
    delivery_address = db.Column(db.String(255), nullable=False)
    
    order_status = db.Column(db.Enum('Unpaid','Pending','Processing','Shipped','Delivered','Cancelled', name='order_status_enum'), default='Unpaid')
    paystack_reference = db.Column(db.String(255), nullable=True)
    order_date = db.Column(db.DateTime, default=datetime.now())
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    
    user = db.relationship('User', backref=db.backref('orders', lazy=True, cascade='all, delete'))
    items = db.relationship('OrderItem', backref='orders', lazy=True, cascade='all, delete-orphan')
    
class OrderItem(db.Model):
    itemID = db.Column(db.Integer, primary_key=True,autoincrement=True)
    orderID = db.Column(db.Integer, db.ForeignKey(Orders.orderID), nullable=False)
    productID = db.Column(db.Integer, db.ForeignKey(Product.productsID), nullable=False)
    quantity = db.Column(db.Integer, nullable= False, default=0)
    sub_total = db.Column(db.Numeric(10,2), nullable=False)
    
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True, cascade='all, delete'))
    
class Payment(db.Model):
    paymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orderID = db.Column(db.Integer, db.ForeignKey(Orders.orderID), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    paymentMethod = db.Column(db.Enum("Paystack","Mobilemoney",name='payment_method_enum'), nullable=False)
    paymentStatus = db.Column(db.Enum('Pending','Success',name='payment_status_enum'), default='Pending')
    transaction_reference = db.Column(db.String(255), nullable=True)
    currency = db.Column(db.String(3), default="KES")
    paymentDate = db.Column(db.DateTime, default=datetime.now())
    
    order = db.relationship('Orders', backref=db.backref('payments', lazy=True, cascade='all, delete'))
    user = db.relationship('User', backref=db.backref('payments', lazy=True, cascade='all, delete'))
    
class Cart(db.Model):
    cartID =db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    productID = db.Column(db.Integer, db.ForeignKey('product.productsID'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    total_price = db.Column(db.Numeric(10,2), nullable=False)
    
    
    user = db.relationship('User', backref=db.backref('cart', lazy=True, cascade='all, delete'))
    product = db.relationship('Product', backref=db.backref('carts', lazy=True, cascade='all, delete'))
