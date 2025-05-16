from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from website.models import User, Product, Cart, Orders, OrderItem, Payment, Category, Employee,db
from sqlalchemy.orm import make_transient
from dotenv import load_dotenv
import os


load_dotenv()

#Set up MySQQL(source) and target(oracle) engines
source_engine = create_engine(os.getenv('MYSQL_DB'))
target_engine = create_engine(os.getenv('ORACLE_DB'))

#Create session makers for both engines
MySQLSession = sessionmaker(bind=source_engine)
Oraclesession = sessionmaker(bind=target_engine) 

mysql_session = MySQLSession()
oracle_session = Oraclesession()

def migrate_model(model):
    records = mysql_session.query(model).all()
    for record in records:
        mysql_session.expunge(record)  # Detach the record from the session
        make_transient(record)  # Make the record transient
        oracle_session.merge(record)
    oracle_session.commit()
    

def run_migrations():
    
    print("Creating tables in Oracle database (if not exist)...")
    db.metadata.create_all(target_engine)
    
    # Migrate each model
    print("Migrating data from MySQL to Oracle...")
    models = [User, Employee,Category,Product, Cart, Orders, OrderItem, Payment]
    for model in models:
        print(f"Migrating {model.__name__}...")
        migrate_model(model)
    # Close the sessions
    mysql_session.close()
    oracle_session.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    run_migrations()