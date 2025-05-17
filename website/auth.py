from flask import Blueprint,request,jsonify,render_template, url_for,flash, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from functools import wraps
import os
from datetime import date
from .models import User,  Employee
from website import mail,db
from flask_mail import Message
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask import session


auth = Blueprint('routes', __name__)
# Registration Endpoint
@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    firstname = data.get('firstname')
    lastname = data.get("lastname")
    phone = data.get("phone")
    email = data.get('email').lower()
    password = data.get('password')
    is_staff = data.get('is_staff', False) 

    # Check if user already exists
    existing_user = User.query.filter((User.email==email)).first()
    if existing_user:
        return jsonify({"msg":"user already exists"}),400
    # Hash the password
    hashed_password = generate_password_hash(password)
    
    # Store the user in the "database"
    new_user = User(firstname=firstname,lastname=lastname, phone=phone,email=email, password=hashed_password, is_staff =is_staff)
    db.session.add(new_user)
    db.session.commit()
    
    login_user(new_user)  # Log in the user after registration

    try:
        msg = Message(
        subject="Welcome to Farmers E-Commerce",
        sender=("Farmers Platform", os.environ.get("MAIL_USERNAME")),
        recipients=[email],
        body=f"""Hello {firstname},

Thank you for registering on Farmers E-Commerce.

We're glad to have you onboard!

Best regards,
Farmers Platform Team"""
    )
        mail.send(msg)

    except Exception as e:
        print(f"Failed to send email: {e}")
    
    return jsonify({"msg": "Registration successful",
                        "User":{
                            "id":new_user.id,
                            "firstname":new_user.firstname,
                            "lastname":new_user.lastname,
                            "email":new_user.email,
                            "phone":new_user.phone,
                            }}), 201

# Login Endpoint
@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email').lower()
    password = data.get('password')

    # Check if user exists in the database
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg":"Enter correct Email Address or register"}),404
    if not check_password_hash(user.password, password):
        return jsonify({"msg": "Incorrect password"}), 401

    # Create a JWT token
    access_token = create_access_token(identity=user.email)
    response = {
        "msg":"Login-successful",
        "access_token": access_token,
    }
    
    if user.is_staff:
        response["is_staff"] = True
        
    return jsonify(response), 200
    