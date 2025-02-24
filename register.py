from flask import Flask, jsonify, request,render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import jwt
from functools import wraps
import datetime
from datetime import date
from flask_cors import CORS
# Initialize Flask app and JWT manager
app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'ukulima'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # JWT Secret Key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:60926092%40Av@127.0.0.1:3306/farm'  # 60926092@Av
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=1)

#initialize extentions
jwt = JWTManager(app)
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(150), nullable=False)
    lastname= db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150),unique=True,nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
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
    url = db.Column(db.String(255),nullable=True)
    quantity =db.Column(db.Integer,nullable=True)

# Create the database tables
with app.app_context():
    db.create_all()

# Registration Endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    firstname = data.get('firstname')
    lastname = data.get("lastname")
    phone = data.get("phone")
    email = data.get('email')
    password = data.get('password')
    is_admin = data.get('is_admin', False) 

    # Check if user already exists
    existing_user = User.query.filter((User.email==email)).first()
    if existing_user:
        return jsonify({"msg":"user already exists"}),400
    # Hash the password
    hashed_password = generate_password_hash(password)
    
    # Store the user in the "database"
    new_user = User(firstname=firstname,lastname=lastname, phone=phone,email=email, password=hashed_password, is_admin=is_admin)
    db.session.add(new_user)
    db.session.commit()
    

    return jsonify({"msg": "Registration successful"}), 201

# Login Endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    # Check if user exists in the database
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg":"Enter correct Email Address or register"}),404
    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Incorrect password"}), 401

    # Create a JWT token
    access_token = create_access_token(identity=user.email)
    return jsonify(access_token=access_token), 200


def admin_required(fn):
    @wraps(fn)  # Preserve function name and metadata
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user or not user.is_admin:
            return jsonify({"msg": "Admin access required"}), 403
        
        return fn(*args, **kwargs)
    return wrapper

#Admin only route
@app.route('/admin', methods=['GET'])
@admin_required
def admin_route():
    return jsonify({'message':'welcome, admin'})

@app.route('/admin/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.all()
    user_list = [{
        "id": user.id,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "email": user.email,
        "phone": user.phone,
        "is_admin": user.is_admin
    } for user in users]
    
    return jsonify(user_list), 200

@app.route('/admin/users/<int:user_id>/promote', methods=['PUT'])
@admin_required
def promote_user(user_id):
    user = User.query.get(user_id)
    
    if not user: 
        return jsonify({"msg": "User not found"}), 404
    
    user.is_admin = True
    db.session.commit()
    return jsonify({"msg": f"User {user.firstname} promoted to admin"}), 200

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"msg": "User deleted successfully"}), 200

def customer_required(x):
    @wraps(x)  # Preserve function name and metadata
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({"msg": "Please, register first"}), 403
        if user.is_admin:
            return jsonify({"msg": "Acess restricted to customers only"})
        return x(*args, **kwargs)
    return wrapper


 #User route   
@app.route('/customers', methods=['GET'])
@jwt_required()
@customer_required
def customer():
    return jsonify({"msg":"welcome user"})


# Protected Endpoint
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity()
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

        
#Add category end point
@app.route('/admin/categories', methods=['POST'])
def add_category():
    data = request.get_json()
    name=data.get('name')
    url = data.get('url')
    
    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({'msg':'Category already exists'}),400
    
    new_category = Category(name=name, url=url)
    db.session.add(new_category)
    db.session.commit()
    
    return jsonify({'msg':'Category added successfully'})

with app.app_context():
    #db.drop_all()
    db.create_all()

#add products
@app.route('/admin/products',methods=["POST"])
@admin_required
def add_product():
    data = request.get_json()
    
    productName = data.get('productName')
    price = data.get('price')
    categoryId = data.get('categoryId')
    productDescription = data.get('productDescription')
    url = data.get('url')
    quantity = data.get('quantity')
    
    category = Category.query.get(categoryId)
    if not category:
        return jsonify({"msg": "Category not found"}), 404

    # Create a new product
    new_product = Product(productName=productName, price=price, categoryId=categoryId,
                          productDescription= productDescription, url=url, quantity=quantity)
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"msg": "Product added successfully"}), 201

@app.route('/register/admin', methods=['POST'])
def register_admin():
    data = request.get_json()
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    salary = data.get('salary')
    
     # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"msg": "User already exists"}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Create new admin user
    new_admin = User(
        firstname=firstname,
        lastname=lastname,
        phone=phone,
        email=email,
        password=hashed_password,
        is_admin=True  # Ensure they are an admin
    )
    db.session.add(new_admin)
    db.session.commit()

    # Create an Employee entry for the admin user
    new_employee = Employee(
        userId=new_admin.id,
        role=role,
        salary=salary,
        hireDate=date.today()
    )
    db.session.add(new_employee)
    db.session.commit()

    return jsonify({"msg": "Admin registered successfully"}), 201
    
if __name__ == '__main__':
    app.run(debug=True)
