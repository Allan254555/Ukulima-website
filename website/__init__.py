from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import datetime
from dotenv import load_dotenv
import os
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
load_dotenv()
    
def create_app():
    app=Flask(__name__, template_folder='templates', static_folder="static")
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Secret Key for session management
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # JWT Secret Key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('ORACLE_DB')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=24)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Your Gmail address
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Use App Password (not your Gmail password)
    app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'
    
    
    flask_env = os.getenv('FLASK_ENV', 'production')
    app.config['ENV'] = flask_env
    app.config['DEBUG'] = flask_env == 'development'
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'  # Redirect to login page if not authenticated
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from .payment import payment
    from .orders import orders
    from .auth import auth
    from .routes import routes
    from .views import views
    from .cart import cart
    from .views import uploads
    from website.transactions import admin_dashboard
    
    app.register_blueprint(admin_dashboard , url_prefix='/api/', name='admin_dashboard_blueprint') 
    app.register_blueprint(uploads, url_prefix='/uploads', name='uploads_blueprint')
    app.register_blueprint(cart, url_prefix='/api/', name='cart_blueprint') 
    app.register_blueprint(payment, url_prefix='/api/', name='payment_blueprint')
    app.register_blueprint(routes, url_prefix='/api/', name='routes_blueprint')
    app.register_blueprint(orders, url_prefix='/api/', name='orders_blueprint')
    app.register_blueprint(auth, url_prefix='/api/', name='auth_blueprint')
    app.register_blueprint(views, url_prefix="/api/", name='views_blueprint')

    
    from .models import User, Category, Product, Cart, Employee, Orders, OrderItem, Payment
    # Create the database tables
    with app.app_context():
        if not os.path.exists("instance/default.db"):
           db.create_all()
    
    return app
