from flask import Blueprint,render_template,jsonify,request,redirect,url_for,session
from.models import db,Cart,Product,User
from flask_jwt_extended import jwt_required,get_jwt_identity
from flask_login import login_required,current_user

cart = Blueprint("cart",__name__)

@cart.route('/cart_add', methods=['POST'])
@jwt_required()
def add_to_cart():
    try:
        data = request.get_json()
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        quantity = data.get('quantity', 1)  # Default to 1 if not provided
        productID = data.get('productID')
        
        #get product by productID
        product = Product.query.get(productID)
        if not product:
            return jsonify({"msg": "Product not found"}), 404

        if product.quantity < quantity:
            return jsonify({"msg": "Insufficient stock"}), 400

        #Check if product is already in cart
        cart_item = Cart.query.filter_by(user_id=user.id, productID=productID).first()
        if cart_item: #if product is already in cart update quantity
            if product.quantity >= cart_item.quantity + quantity:
                # Update existing cart item
                cart_item.quantity += quantity
                cart_item.total_price = cart_item.quantity * product.price
            else:
                return jsonify({"msg": "Insufficient stock"}), 400
        else:
            # Create new cart item
            total_price = quantity * product.price
            cart_item = Cart(user_id=user.id,
                             productID=productID,
                             quantity=quantity,
                             total_price=total_price 
                             )
            db.session.add(cart_item)

        db.session.commit()
        # Calculate total amount in cart
        cart_items = Cart.query.filter_by(user_id=user.id).all()
        total_amount = sum(item.total_price for item in cart_items)
        
        return jsonify({"msg": "Item added to cart",
                        "total_amount":total_amount}), 201       

    except Exception as e:
        db.session.rollback()  # Rollback transaction on failure
        return jsonify({"msg": "Error adding item to cart", "error": str(e)}), 500
    
    #Update cart item quantity
@cart.route('/cart_update/<int:product_id>', methods=['PATCH'])
@jwt_required()
def update_cart_item(product_id):
    try:
        data = request.get_json()
        quantity = data.get('quantity')
    
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
    
         # Find the cart item
        cart_item = Cart.query.filter_by(user_id=user.id, productID=product_id).first()
    
        if not cart_item:
            return jsonify({"msg": "Cart item not found"}), 404
        
        product = Product.query.get(product_id)
        if not product or product.quantity < quantity:
            return jsonify({"msg": "Insufficient stock"}), 400
        
        cart_item.quantity = quantity
        cart_item.total_price = quantity * product.price
        db.session.commit()
        return jsonify({"msg":"Items added to cart successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg":"Error updating cart", "error":str(e)}), 500
    
#Delete item from cart
@cart.route('/cart_delete/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_cart_item(product_id):
    try:
        email= get_jwt_identity()
        user= User.query.filter_by(email=email).first()
        
        cart_item = Cart.query.filter_by(user_id=user.id,productID=product_id).first()
        if not cart_item:
            return jsonify({"msg":"Item not found"}), 404
        
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({"msg":"Item removed drom cart"}),200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error deleting item from cart", "error": str(e)}), 500
    
@cart.route('/cart', methods=['GET'])
@jwt_required()
def view_cart():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    cart_items = Cart.query.filter_by(user_id=user.id).all()
    cart_list = []

    for item in cart_items:
        product = Product.query.get(item.productID)
        if product:
            cart_list.append({
                "productID": item.productID,
                "productName": product.productName,
                "price": product.price,
                "image_url": url_for('uploads_blueprint.serve_upload', filename=product.image_url, _external=True),
                "quantity": item.quantity,
                "total_price": item.total_price
            })

    total_amount = sum(item.total_price for item in cart_items)

    return jsonify({
        "cart": cart_list,
        "total_amount": total_amount
    })

