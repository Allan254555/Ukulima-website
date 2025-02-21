from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import getenv
db = SQLAlchemy()
    
def create_app():
    app=Flask(__name__, template_folder='templates')
    app.config["SECRET_KEY"] = 'ukulima'
    
    #connect to my sql database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:60926092%40Av@127.0.0.1:3306/ukulima'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    from .views import views
    from .routes import routes
    
    app.register_blueprint(routes,url_prefix='/')
    app.register_blueprint(views, url_prefix="/")
    
    from .models import User
    # Create the database tables
    with app.app_context():
        db.create_all()
    
    return app
