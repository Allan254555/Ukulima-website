from flask import Blueprint,request,render_template, url_for,flash, redirect
#registration route
from website import db
from .models import User


routes = Blueprint('routes', __name__)

@routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        firstname = request.form["firstName"]
        lastname =request.form["lastName"]
        email =request.form["email"].lower()
        password = request.form['password']
        #hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("routes.login"))

        # Create new user and hash password
        new_user = User(firstname=firstname, lastname=lastname, email=email, password=password)
        new_user.set_password(password)

        # Save user to database
        db.session.add(new_user)
        db.session.commit()

        flash(f"Welcome, {firstname} {lastname}! Registration successful.", "success")
        return redirect(url_for("routes.login"))
        
    return render_template("register.html")

#login route
@routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(user.password, password):
            flash(f"Welcome back, {user.firstname}!", "success")
            return redirect(url_for("routes.home"))
        else:
            flash("Invalid email or password.", "danger")
        
    return render_template("login.html")
   
