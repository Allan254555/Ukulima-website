from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import datetime
import os
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
    
def create_app():
    app=Flask(__name__, template_folder='templates', static_folder="static")
    app.config['SECRET_KEY'] = 'ukulima'
    app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # JWT Secret Key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=1)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'  # Redirect to login page if not authenticated
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from .orders import orders
    from .auth import auth
    from .routes import routes
    from .transactions import views as transactions_views

    app.register_blueprint(routes, url_prefix='/', name='routes_blueprint')
    app.register_blueprint(orders, url_prefix='/api/', name='orders_blueprint')
    app.register_blueprint(auth, url_prefix='/api/', name='auth_blueprint')
    app.register_blueprint(transactions_views, url_prefix="/", name="transactions_blueprint")

    
    from .models import User, Category, Product, Cart, Employee, Orders, OrderItem, Payment
    # Create the database tables
    with app.app_context():
        if not os.path.exists("instance/default.db"):
           db.create_all()
    
    return app
