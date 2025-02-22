from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# Initialize Flask app and JWT manager
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ukulima'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # JWT Secret Key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:60926092%40Av@127.0.0.1:3306/farm'  # 60926092@Av
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


jwt = JWTManager(app)

# In-memory database for storing users

# Connect to MySQL database

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(150), nullable=False)
    lastname= db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150),unique=True,nullable=False)
    
    password = db.Column(db.String(225), nullable=False)

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

    # Check if user already exists
    existing_user = User.query.filter((User.email==email)).first()
    if existing_user:
        return jsonify({"msg":"user already exists"}),400
    # Hash the password
    hashed_password = generate_password_hash(password)
    
    # Store the user in the "database"
    new_user = User(firstname=firstname,lastname=lastname, phone=phone,email=email, password=hashed_password)
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
    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Bad firstname or password"}), 401

    # Create a JWT token
    access_token = create_access_token(identity=user.firstname)
    return jsonify(access_token=access_token), 200

# Protected Endpoint
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity()
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

if __name__ == '__main__':
    app.run(debug=True)
