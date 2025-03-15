from . import db
# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(150), nullable=False)
    lastname= db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150),unique=True,nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    
class Employee(db.Model):
    employeeId = db.Column(db.Integer,primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey(User.id),nullable=False,unique=True)
    role = db.Column(db.String(100),nullable=False)
    salary = db.Column(db.Float,nullable=False)
    hireDate = db.Column(db.Date, nullable=False)
    
#category model for product category
class Category(db.Model):
    categoryId = db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),unique=True, nullable=False)
    url=db.Column(db.String(255), nullable=True)
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
    
class Cart(db.Model):
    cartID =db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey(Product.productsID), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    



