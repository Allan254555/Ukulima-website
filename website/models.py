from . import db
from datetime import datetime
from flask_login import UserMixin

# User model

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(150), nullable=False)
    lastname= db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150),unique=True,nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
   
#Employee model for employee details
class Employee(db.Model, UserMixin):
    employeeId = db.Column(db.Integer,primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey(User.id),nullable=False,unique=True)
    role = db.Column(db.String(100),nullable=False)
    salary = db.Column(db.Float,nullable=False)
    hireDate = db.Column(db.Date, nullable=False)
    
#category model for product category
class Category(db.Model):
    categoryId = db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),unique=True, nullable=False)
    image_url=db.Column(db.String(255), nullable=True)
    
    products = db.relationship('Product',backref='category',lazy=True,cascade="all,delete-orphan")
    
    
#Product model for the product category
class Product(db.Model):
    productsID = db.Column(db.Integer,primary_key=True)
    categoryId = db.Column(db.Integer, db.ForeignKey('category.categoryId'),nullable=False)
    productName =db.Column(db.String(100),unique=True,nullable=False)
    price = db.Column(db.Float,nullable=False)
    productDescription = db.Column(db.String(255),nullable=False)
    image_url = db.Column(db.String(255))
    quantity =db.Column(db.Integer)
    
class Orders(db.Model):
    orderID = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    total_amount = db.Column(db.Numeric(10,2), nullable=False)
    order_status = db.Column(db.Enum('Pending','Processing','Shipped','Delivered','Cancelled'), default='Pending')
    order_date = db.Column(db.DateTime, default=datetime.now())
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    
    user = db.relationship('User', backref=db.backref('orders', lazy=True, cascade='all, delete'))
    items = db.relationship('OrderItem', backref='orders', lazy=True, cascade='all, delete-orphan')
    
class OrderItem(db.Model):
    itemID = db.Column(db.Integer, primary_key=True)
    orderID = db.Column(db.Integer, db.ForeignKey(Orders.orderID), nullable=False)
    productID = db.Column(db.Integer, db.ForeignKey(Product.productsID), nullable=False)
    quantity = db.Column(db.Integer, nullable= False, default=0)
    sub_total = db.Column(db.Numeric(10,2), nullable=False)
    
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True, cascade='all, delete'))
    
class Payment(db.Model):
    paymentID = db.Column(db.Integer, primary_key=True)
    orderID = db.Column(db.Integer, db.ForeignKey(Orders.orderID), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    paymentMethod = db.Column(db.Enum('Cash on Delivery','Credit Card','Debit Card','Paypal','Google Pay','Apple Pay'), nullable=False)
    paymentStatus = db.Column(db.Enum('Pending','Processing','Completed','Failed'), default='Pending')
    paymentDate = db.Column(db.DateTime, default=datetime.now())
    
    order = db.relationship('Orders', backref=db.backref('payments', lazy=True, cascade='all, delete'))
    user = db.relationship('User', backref=db.backref('payments', lazy=True, cascade='all, delete'))
    
class Cart(db.Model):
    cartID =db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.productsID'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    
    
    user = db.relationship('User', backref=db.backref('cart', lazy=True, cascade='all, delete'))
    product = db.relationship('Product', backref=db.backref('carts', lazy=True, cascade='all, delete'))
