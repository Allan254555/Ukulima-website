from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import datetime
import os

db = SQLAlchemy()
jwt = JWTManager()
    
def create_app():
    app=Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = 'ukulima'
    app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # JWT Secret Key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=1)
    
    db.init_app(app)
    jwt.init_app(app)
    
    from .views import views
    from .routes import routes
    
    app.register_blueprint(routes,url_prefix='/')
    app.register_blueprint(views, url_prefix="/")
    
    from .models import User, Category, Product, Cart, Employee
    # Create the database tables
    with app.app_context():
        db.create_all()
    
    return app
