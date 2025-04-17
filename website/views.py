from flask import Blueprint, app,jsonify, request, render_template, send_from_directory, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import db
import uuid
import os
from werkzeug.utils import secure_filename
from .routes import staff_required
from .models import Category,Product, Cart
from .config import Config

views = Blueprint("views", __name__)

# Ensure the upload folder exists
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@views.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.abspath("static/uploads"), filename)

@views.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    category_list = [{"id": c.categoryId, "name": c.name} for c in categories]
    return jsonify({"categories": category_list})

#Add category end point
@views.route('/staff/categories', methods=['POST'])
@staff_required
def add_category():
    if 'file' not in request.files:
        return jsonify({'msg':'No image uploaded'}),400
    
    file = request.files['file']
    name=request.form.get('name')
    image_url = request.form.get('image_url')
    
    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({'msg':'Category already exists'}),400
    
    if not allowed_file(file.filename):
        return jsonify({'msg':'Invalid file type'}),400
    
    upload_folder = os.path.join('static','uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    #Generate unique filename
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    file.save(filepath)
    image_url = f"static/uploads/{unique_filename}"
    
    new_category = Category(name=name,
                            image_url=image_url)
    db.session.add(new_category)
    db.session.commit()
    
    return jsonify({'msg':'Category added successfully'})


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
    
@views.route('/products', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)  
    per_page = request.args.get('per_page', 9, type=int) #Number of items per page
    
    pagination = Product.query.paginate(page=page, per_page=per_page, error_out=False)

    products = [
        {
            "productsID": p.productsID,
            "productName": p.productName,
            "price": p.price,
            "quantity": p.quantity,
            "categoryName": p.category.name if p.category else None,
            "image_url": request.host_url + p.image_url
        }
        for p in pagination.items
    ]
    return jsonify({
            "products": products,
            "total_products": pagination.total,
            "total_pages": pagination.pages,
            "current_page": pagination.page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
    })
    

@views.route('/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        product = Product.query.get(data['product_id'])
        quantity = data.get('quantity', 1)

        if not product:
            return jsonify({"msg": "Product not found"}), 404

        if product.quantity < quantity:
            return jsonify({"msg": "Insufficient stock"}), 400

        # Begin transaction
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=product.productsID).first()

        if cart_item:
            if product.quantity >= quantity:
                product.quantity -= quantity
                cart_item.quantity += quantity
            else:
                return jsonify({"msg": "Insufficient stock"}), 400
        else:
            cart_item = Cart(user_id=user_id, product_id=product.productsID, quantity=quantity)
            db.session.add(cart_item)

        # Deduct stock from inventory
            product.quantity -= quantity

        db.session.commit()
        return jsonify({"msg": "Item added to cart"}), 201

    except Exception as e:
        db.session.rollback()  # Rollback transaction on failure
        return jsonify({"msg": "Error adding item to cart", "error": str(e)}), 500