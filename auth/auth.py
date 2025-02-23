from flask import Flask, request, jsonify, make_response
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from functools import wraps
import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'V05UST4iEp5sfyRo'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'open.1000'
app.config['MYSQL_DB'] = 'flask_auth'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)

# Initialize extensions
mysql = MySQL(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Role-based authorization decorator
def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT role FROM users WHERE username = %s", (current_user,))
            user_role = cursor.fetchone()
            cursor.close()
            
            if user_role and user_role[0] == role:
                return func(*args, **kwargs)
            else:
                return jsonify({'message': 'Access Denied!'}), 403
        return wrapper
    return decorator

# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
    role = data.get('role', 'user')  # Default role is 'user'
    
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
    mysql.connection.commit()
    cursor.close()
    
    return jsonify({'message': 'User registered successfully!'}), 201

# User login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    
    if user and bcrypt.check_password_hash(user[0], password):
        token = create_access_token(identity=username)
        return jsonify({'token': token})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# Admin-only route
@app.route('/admin', methods=['GET'])
@jwt_required()
@role_required('admin')
def admin_route():
    return jsonify({'message': 'Welcome, Admin!'})

# User route
@app.route('/user', methods=['GET'])
@jwt_required()
@role_required('user')
def user_route():
    return jsonify({'message': 'Welcome, User!'})

if __name__ == '__main__':
    app.run(debug=True)
