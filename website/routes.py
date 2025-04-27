from flask import Blueprint,request,jsonify,render_template, url_for,flash, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from dotenv import load_dotenv
from functools import wraps
import os

from datetime import date
from .models import User,  Employee

load_dotenv

routes = Blueprint('routes', __name__)

def staff_required(fn):
    @wraps(fn)  # Preserve function name and metadata
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_email = get_jwt_identity()
        user =User.query.filter_by(email=current_user_email).first()
        
        if not user or not user.is_staff:
            return jsonify({"msg": "staff access required"}), 403
        
        return fn(*args, **kwargs)
    return wrapper

#staff only route
@routes.route('/staff', methods=['GET'])
@staff_required
def staff_route():
    return jsonify({'message':'welcome, staff'})

@routes.route('/staff/users', methods=['GET'])
@staff_required
def list_users():
    users = User.query.all()
    user_list = [{
        "id": user.id,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "email": user.email,
        "phone": user.phone,
        "is_staff": user.is_staff
    } for user in users]
    
    return jsonify(user_list), 200

@routes.route('/staff/users/<int:user_id>/promote', methods=['PUT'])
@staff_required
def promote_user(user_id):
    user = User.query.get(user_id)
    
    if not user: 
        return jsonify({"msg": "User not found"}), 404
    
    user.is_staff = True
    db.session.commit()
    return jsonify({"msg": f"User {user.firstname} promoted to staff"}), 200

@routes.route('/staff/users/<int:user_id>', methods=['DELETE'])
@staff_required
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
        if user.is_staff:
            return jsonify({"msg": "Acess restricted to customers only"}), 403
        return x(*args, **kwargs)
    return wrapper


 #User route   
@routes.route('/customers', methods=['GET'])
@jwt_required()
def customer():
    return jsonify({"msg":"welcome user"})


# Protected Endpoint
@routes.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity()
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

        

@routes.route('/register/staff', methods=['POST'])
def register_staff():
    data = request.get_json()
    
    
    json_ukulima_superuser_username = data.get('ukulima_superuser_username')
    json_ukulima_superuser_password = data.get('ukulima_superuser_password')
    
    # Authenticate admin
    environ_admin_username = os.getenv("UKULIMA_SUPERUSER_USERNAME")
    environ_admin_password = os.environ.get("UKULIMA_SUPERUSER_PASSWORD")
    
    if not environ_admin_username or not environ_admin_password:
      return jsonify({"msg": "Superuser credentials not configured"}), 500
    
    if json_ukulima_superuser_username == environ_admin_username and json_ukulima_superuser_password == environ_admin_password:
        firstname = data.get('firstname')
        lastname = data.get('lastname')
        phone = data.get('phone')
        email = data.get('email').lower()
        password = data.get('password')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"msg": "User already exists"}), 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create new staff user
        new_staff = User(
            firstname=firstname,
            lastname=lastname,
            phone=phone,
            email=email,
            password=hashed_password,
            is_staff=True  # Ensure they are staff
        )
        db.session.add(new_staff)
        db.session.commit()

        # Create an Employee entry for the staff user
        new_employee = Employee(
            userId=new_staff.id,
            hireDate=date.today()
        )
        db.session.add(new_employee)
        db.session.commit()

        return jsonify({"msg": "staff registered successfully"}), 201
    
    return {"error": "The initiator information is invalid!"}, 400
    