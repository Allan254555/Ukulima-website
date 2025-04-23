from flask import Blueprint, jsonify, redirect, request, send_from_directory, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import db
import uuid
import os
from werkzeug.utils import secure_filename
from .routes import staff_required
from .models import Category, Product, Cart
from .config import Config

views = Blueprint("views", __name__)
uploads =Blueprint("uploads", __name__)

# Ensure the upload folder exists
UPLOAD_FOLDER = os.path.join(os.getcwd(),'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@uploads.route('/<filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@views.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    category_list = [{"id": c.categoryId, "name": c.name} for c in categories]
    return jsonify({"categories": category_list})

# Add category endpoint
@views.route('/staff/categories', methods=['POST'])
@staff_required
def add_category():
    if 'file' not in request.files:
        return jsonify({'msg': 'No image uploaded'}), 400

    file = request.files['file']
    name = request.form.get('name')

    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({'msg': 'Category already exists'}), 400

    if not allowed_file(file.filename):
        return jsonify({'msg': 'Invalid file type'}), 400

    file_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

    file.save(filepath)
    image_url = unique_filename

    new_category = Category(name=name, image_url=image_url)
    db.session.add(new_category)
    db.session.commit()

    return jsonify({'msg': 'Category added successfully'})

# Add products
@views.route('/staff/products', methods=["POST"])
@staff_required
def add_product():
    if 'file' not in request.files:
        return jsonify({'msg': 'No image uploaded'}), 400

    file = request.files['file']
    productName = request.form.get('productName')
    price = request.form.get('price')
    categoryId = request.form.get('categoryId')
    productDescription = request.form.get('productDescription')
    quantity = request.form.get('quantity')

    category = Category.query.get(categoryId)
    if not category:
        return jsonify({"msg": "Category not found"}), 404

    existing_product = Product.query.filter_by(productName=productName).first()
    if existing_product:
        return jsonify({"msg": "Product already exists"}), 400

    if not allowed_file(file.filename):
        return jsonify({'msg': 'Invalid file type'}), 400

    file_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

    file.save(filepath)
    image_url = unique_filename

    new_product = Product(productName=productName,
                          price=price,
                          categoryId=categoryId,
                          productDescription=productDescription,
                          image_url=image_url,
                          quantity=quantity)
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"msg": "Product added successfully"}), 201

@views.route('/staff/products/<int:productsID>', methods=['PATCH'])
@staff_required
def update_product(productsID):
    product = Product.query.get(productsID)
    if not product:
        return jsonify({"msg": "Product not found"}), 404

    data = request.get_json()
    price = data.get('price')
    quantity = data.get('quantity')
    productDescription = data.get('productDescription')
    productName = data.get('productName')
    categoryId = data.get('categoryId')

    if price is not None:
        try:
            product.price = float(price)
        except ValueError:
            return jsonify({'msg': 'Invalid price value'}), 400

    if quantity is not None:
        try:
            product.quantity = int(quantity)
        except ValueError:
            return jsonify({'msg': 'Invalid quantity value'}), 400

        if product.quantity == 0:
            db.session.commit()
            return jsonify({
                'msg': 'Product updated successfully',
                'status': 'Out of Stock'
            }), 200

    if productName is not None:
        if productName.strip() == "":
            return jsonify({'msg': 'Product name cannot be empty'}), 400
        existing = Product.query.filter(Product.productName == productName, Product.productsID != productsID).first()
        if existing:
            return jsonify({'msg': 'Another product with that name already exists'}), 400
        product.productName = productName

    if productDescription is not None:
        product.productDescription = productDescription

    db.session.commit()

    response = {'msg': 'Product updated successfully'}
    if quantity is not None and product.quantity == 0:
        response['status'] = 'Out of Stock'

    return jsonify(response), 200

@views.route('/products', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 9, type=int)

    pagination = Product.query.paginate(page=page, per_page=per_page, error_out=False)

    products = [
        {
            "productsID": p.productsID,
            "productName": p.productName,
            "price": p.price,
            "quantity": p.quantity,
            "status": "Out of Stock" if p.quantity == 0 else "In Stock",
            "productDescription": p.productDescription,
            "categoryName": p.category.name if p.category else None,
            "image_url": url_for('uploads_blueprint.serve_upload', filename=p.image_url, _external=True)
            
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
