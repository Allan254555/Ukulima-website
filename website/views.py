from flask import Blueprint,jsonify, request, render_template, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import db
import uuid
import os
from werkzeug.utils import secure_filename
from .routes import staff_required
from .models import User,Category,Product
from .config import Config

views = Blueprint("views", __name__)

#Add category end point
@views.route('/staff/categories', methods=['POST'])
@staff_required
def add_category():
    data = request.get_json()
    name=data.get('name')
    url = data.get('url')
    
    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({'msg':'Category already exists'}),400
    
    new_category = Category(name=name, url=url)
    db.session.add(new_category)
    db.session.commit()
    
    return jsonify({'msg':'Category added successfully'})

# Ensure the upload folder exists
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


#add products
@views.route('/staff/products',methods=["POST"])
@staff_required
def add_product():
    #data = request.form.get()
    if 'file' not in request.files:
        return jsonify({'msg':'No image uploaded'}),400
    
    file= request.files['file']
    productName = request.form.get('productName')
    price = request.form.get('price')
    categoryId = request.form.get('categoryId')
    productDescription = request.form.get('productDescription')
    image_url = request.form.get('image_url')
    quantity = request.form.get('quantity')
    
    #Validate category
    category = Category.query.get(categoryId)
    if not category:
        return jsonify({"msg": "Category not found"}), 404
    
    #Check if product already exists
    existing_product = Product.query.filter_by(productName=productName).first()
    if existing_product:
        return jsonify({"msg":"Product already exists"}),400
    
    # Validate file type
    if not allowed_file(file.filename):
        return jsonify({'msg': 'Invalid file type'}), 400
    
    #Ensure upload folser exists
    upload_folder = os.path.join('static','uploads')
    os.makedirs(upload_folder, exist_ok=True)
    

    #Generate unique filename
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    file.save(filepath)
    image_url = f"static/uploads/{unique_filename}"
    # Create a new product
    new_product = Product(productName=productName,
                          price=price,
                          categoryId=categoryId,
                          productDescription= productDescription, 
                          image_url=image_url, 
                          quantity=quantity
                          )
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"msg": "Product added successfully"}), 201

#Get product
@views.route('/products', methods=['GET'])
#@jwt_required()
def get_products():
    products = Product.query.all()
    return jsonify([
        {'productsID':p.productsID,
                     "productName": p.productName,
                     "price": p.price, 
                     "quantity": p.quantity,
                     "categoryId":p.categoryId,
                     "image_url":request.host_url + p.image_url 
        } for p in products
    ])
                   

